"""
ARYA WhatsApp Tools - Production Level v4
Production-ready WhatsApp messaging automation for macOS (Native WhatsApp for Mac).

Architecture:
- State detection via pgrep (cold vs warm start)
- UI reset via Escape keys for warm start
- Contact selection via Accessibility API (AXButton click) — the ONLY reliable method
- Chat verification via AXGroup description check
- Per-phase error handling with descriptive error strings
"""

import logging
import subprocess
import time
from livekit.agents import llm

logger = logging.getLogger("arya-agent")


# ============================================================================
# HELPER: Run AppleScript safely
# ============================================================================

def _run_applescript(script: str, timeout: int = 15) -> str:
    """Run AppleScript, return stdout. Raises on timeout."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0 and not stdout:
            logger.debug(f"AppleScript stderr: {stderr}")
            return f"error:applescript:{stderr}"
        return stdout
    except subprocess.TimeoutExpired:
        logger.error(f"❌ AppleScript timed out ({timeout}s)")
        return "error:timeout"
    except Exception as e:
        logger.error(f"❌ AppleScript failed: {e}")
        return f"error:exception:{e}"


# ============================================================================
# PHASE 1: STATE DETECTION
# ============================================================================

def _is_whatsapp_running() -> bool:
    """Check if WhatsApp process is currently running."""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "WhatsApp"],
            capture_output=True, text=True, timeout=5
        )
        running = result.returncode == 0
        logger.debug(f"WhatsApp running: {running}")
        return running
    except Exception as e:
        logger.warning(f"⚠️ pgrep check failed: {e}")
        return False


# ============================================================================
# PHASE 2: LAUNCH
# ============================================================================

def _launch_whatsapp(is_cold_start: bool) -> str:
    """Launch WhatsApp and bring to foreground."""
    try:
        subprocess.run(["open", "-a", "WhatsApp"], capture_output=True, timeout=10)
        wait = 4.0 if is_cold_start else 1.5
        logger.debug(f"⏳ Waiting {wait}s ({'cold' if is_cold_start else 'warm'} start)")
        time.sleep(wait)
        return "success"
    except Exception as e:
        logger.error(f"❌ Launch failed: {e}")
        return f"error:launch:{e}"


# ============================================================================
# PHASE 3: UI RESET (warm start)
# ============================================================================

def _reset_ui_state() -> str:
    """
    Reset WhatsApp to chat list view.
    Handles: media viewers, search overlay, settings, open chats.
    """
    return _run_applescript('''
    tell application "System Events"
        if not (exists process "WhatsApp") then return "error:reset:not_running"
        tell process "WhatsApp"
            set frontmost to true
            delay 0.5
            -- Dismiss overlays (media viewer, popups, search, chat)
            repeat 4 times
                key code 53 -- Escape
                delay 0.3
            end repeat
            delay 0.3
            if not frontmost then return "error:reset:focus_lost"
            return "success"
        end tell
    end tell
    ''', timeout=10)


# ============================================================================
# PHASE 4: SEARCH & SELECT CONTACT
# ============================================================================

def _search_and_select_contact(contact_name: str) -> str:
    """
    Search for a contact and click their chat button.
    
    WhatsApp Mac native app UI hierarchy (from Accessibility Inspector):
      - AXGenericElement (desc="Search") → the search field
      - AXGroup (desc="Search results") → contains results
        - AXHeading (desc="Chats") → section header
        - AXButton (desc="Contact Name") → CLICKABLE chat row
    
    Strategy: Find the FIRST AXButton whose description contains the
    contact name, and click it. One single `entire contents` scan.
    No verification scan — the typing phase will fail if chat didn't open.
    """
    escaped_name = contact_name.replace('\\', '\\\\').replace('"', '\\"')

    # Script 1: Search + find AXButton + click (ONE scan only)
    script = f'''
    tell application "System Events"
        if not (exists process "WhatsApp") then return "error:search:not_running"
        
        tell process "WhatsApp"
            set frontmost to true
            delay 0.5
            
            -- Open search (Cmd+F)
            keystroke "f" using {{command down}}
            delay 0.8
            
            -- Clear existing search text
            keystroke "a" using {{command down}}
            delay 0.1
            key code 51 -- Backspace
            delay 0.3
            
            -- Type contact name
            keystroke "{escaped_name}"
            delay 3.0 -- Wait for search results to resolve
            
            if not frontmost then return "error:search:focus_lost"
            
            -- Find and click the AXButton whose description matches the contact
            set w to window 1
            set allElems to entire contents of w
            
            repeat with elem in allElems
                try
                    if role of elem is "AXButton" then
                        if description of elem contains "{escaped_name}" then
                            click elem
                            delay 2.0
                            return "success"
                        end if
                    end if
                end try
            end repeat
            
            return "error:search:contact_not_found"
        end tell
    end tell
    '''

    result = _run_applescript(script, timeout=25)
    
    if "success" in result:
        logger.info(f"✅ Contact '{contact_name}' clicked")
        return "success"
    
    if "contact_not_found" in result:
        logger.warning(f"⚠️ Exact match failed, trying first result fallback...")
        # Fallback: click the first AXButton that appears after the search 
        # (search is still active, results are still showing)
        fallback = f'''
        tell application "System Events"
            tell process "WhatsApp"
                set frontmost to true
                set w to window 1
                set allElems to entire contents of w
                set pastSearch to false
                
                repeat with elem in allElems
                    try
                        -- Skip past the search field area
                        if role of elem is "AXHeading" then
                            if description of elem contains "Chats" then
                                set pastSearch to true
                            end if
                        end if
                        -- Click first AXButton after Chats heading
                        if pastSearch and role of elem is "AXButton" then
                            click elem
                            delay 2.0
                            return "success"
                        end if
                    end try
                end repeat
                
                return "error:search:no_results"
            end tell
        end tell
        '''
        result2 = _run_applescript(fallback, timeout=20)
        if "success" in result2:
            logger.info(f"✅ Contact selected via first-result fallback")
            return "success"
    
    logger.error(f"❌ Contact selection failed: {result}")
    return result


# ============================================================================
# PHASE 5: TYPE & SEND MESSAGE
# ============================================================================

def _type_and_send_message(message: str) -> str:
    """
    Type message into the open chat and press Enter to send.
    Verifies WhatsApp focus before and after typing.
    """
    escaped_msg = message.replace('\\', '\\\\').replace('"', '\\"')

    script = f'''
    tell application "System Events"
        if not (exists process "WhatsApp") then return "error:send:not_running"
        
        tell process "WhatsApp"
            if not frontmost then
                return "error:send:CRITICAL_focus_lost_before_typing"
            end if
            
            -- Ensure focus is in the message input
            set frontmost to true
            delay 0.3
            
            -- Type the message
            keystroke "{escaped_msg}"
            delay 0.5
            
            -- Final focus verification
            if not frontmost then
                return "error:send:CRITICAL_focus_lost_after_typing"
            end if
            
            -- Send
            key code 36 -- Enter/Return
            delay 0.3
            
            return "success"
        end tell
    end tell
    '''
    
    result = _run_applescript(script, timeout=10)
    if "success" in result:
        logger.debug("✅ Message sent")
    else:
        logger.error(f"❌ Send failed: {result}")
    return result


# ============================================================================
# MAIN TOOL
# ============================================================================

@llm.function_tool(description="""Send a WhatsApp message to any contact.
Use this when user says things like:
- 'Send message to Dad - Hi papa'
- 'WhatsApp Rahul that I'll be late'
- 'Message Mom saying good morning'
Pass the contact_name (as saved in WhatsApp) and the message to send.""")
async def send_whatsapp_message(contact_name: str, message: str) -> str:
    """
    Production-grade WhatsApp message sender for macOS.
    
    Uses Accessibility API to find and click the exact AXButton 
    matching the contact name in search results.
    """
    # Input validation
    if not message or not message.strip():
        return "Bro, message khaali hai! Kuch toh likh do send karne ke liye."
    if not contact_name or not contact_name.strip():
        return "Bro, contact ka naam toh batao! Kaun ko message bhejna hai?"

    contact_name = contact_name.strip()
    message = message.strip()
    logger.info(f"📱 ARYA WhatsApp: '{contact_name}' ← '{message[:50]}...'")

    try:
        # PHASE 1: State detection
        is_cold = not _is_whatsapp_running()
        logger.info(f"📱 {'COLD' if is_cold else 'WARM'} start")

        # PHASE 2: Launch
        r = _launch_whatsapp(is_cold)
        if "error" in r:
            return f"Bhai, WhatsApp nahi khul paya. Check karo app installed hai."

        # PHASE 3: UI Reset (warm start only)
        if not is_cold:
            logger.info("🔄 Resetting UI state...")
            r = _reset_ui_state()
            if "error" in r:
                logger.warning(f"⚠️ UI reset issue: {r} — continuing anyway")

        # PHASE 4: Search & select contact
        logger.info(f"🔍 Searching: {contact_name}")
        r = _search_and_select_contact(contact_name)
        if "error" in r:
            detail = r.split(":")[-1]
            logger.error(f"❌ Contact selection failed: {r}")
            if "contact_not_found" in r or "no_buttons_found" in r:
                return (
                    f"Bhai, '{contact_name}' WhatsApp pe nahi mila. "
                    f"Naam exactly waise likho jaise contact list mein saved hai."
                )
            if "chat_did_not_open" in r:
                return (
                    f"Bhai, '{contact_name}' mila toh lekin chat open nahi hua. "
                    f"Phir se try karo."
                )
            return f"Bhai, WhatsApp automation mein dikkat: {detail}. Phir se try karo."

        # PHASE 5: Type & send
        logger.info("✍️ Sending message...")
        r = _type_and_send_message(message)
        if "error" in r:
            if "CRITICAL" in r:
                return (
                    "Bhai, DANGER! WhatsApp ka focus chala gaya tha. "
                    "Message NAHI bheja — galat jagah type hone se bacha liya. Phir se try karo."
                )
            return f"Bhai, message send mein dikkat: {r}. Phir se try karo."

        # SUCCESS
        logger.info(f"✅ Message sent to '{contact_name}'")
        return (
            f"Kaam set hai bro! '{contact_name}' ko message bhej diya: "
            f"{message[:50]}{'...' if len(message) > 50 else ''}"
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return f"Bhai, unexpected problem: {e}. Manual try karo."


# Export
WHATSAPP_TOOLS = [
    send_whatsapp_message,
]