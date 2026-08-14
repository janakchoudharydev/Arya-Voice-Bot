"""
ARYA WhatsApp Call Tools - PyObjC Native Architecture
Production-ready WhatsApp voice and video calling automation via URL Scheme and macOS Accessibility API.
"""

import os
import time
import logging
import AppKit
import ApplicationServices
from livekit.agents import llm

logger = logging.getLogger("arya-agent")

from tools.contacts_resolver import get_phone_number_from_contacts

def _snap_whatsapp_chat(phone_number: str) -> bool:
    """Uses deep linking to instantly bring WhatsApp to foreground and open exact chat."""
    try:
        # URL scheme opens WhatsApp and loads the specific chat immediately
        cmd = f'open "whatsapp://send?phone={phone_number}"'
        os.system(cmd)
        return True
    except Exception as e:
        logger.error(f"Failed to snap chat: {e}")
        return False

def _trigger_accessibility_call(call_type: str) -> str:
    """
    Traverse WhatsApp's accessibility tree to find and press the call button.
    call_type: 'voice' or 'video'
    """
    keyword = "start voice call" if call_type.lower() == "voice" else "start video call"
    
    try:
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        whatsapp_app = next((app for app in apps if app.bundleIdentifier() == "net.whatsapp.WhatsApp"), None)
        
        if not whatsapp_app:
            return "error:whatsapp_not_running"
            
        pid = whatsapp_app.processIdentifier()
        app_element = ApplicationServices.AXUIElementCreateApplication(pid)
        
        def find_button(element, depth=0):
            if depth > 10: return None
            
            err, role = ApplicationServices.AXUIElementCopyAttributeValue(element, 'AXRole', None)
            if role == 'AXButton':
                err, desc = ApplicationServices.AXUIElementCopyAttributeValue(element, 'AXDescription', None)
                if desc and keyword in str(desc).lower():
                    return element
            
            err, children = ApplicationServices.AXUIElementCopyAttributeValue(element, 'AXChildren', None)
            if err == 0 and children:
                for child in children:
                    found = find_button(child, depth + 1)
                    if found:
                        return found
            return None
            
        call_button = None
        for attempt in range(5):
            err, windows = ApplicationServices.AXUIElementCopyAttributeValue(app_element, 'AXWindows', None)
            if err == 0 and windows:
                for w in windows:
                    call_button = find_button(w)
                    if call_button:
                        break
            if call_button:
                break
            time.sleep(0.5)
            
        if not call_button:
            return "error:call_button_not_found"
            
        # Perform press
        ApplicationServices.AXUIElementPerformAction(call_button, 'AXPress')
        return "success"
        
    except Exception as e:
        logger.error(f"PyObjC AX error: {e}")
        return f"error:exception:{e}"

@llm.function_tool(description="""Initiate a WhatsApp voice call to a contact.
Use this when the user says 'Arya, call John', 'Voice call Mom on WhatsApp', etc.
Requires the exact contact name.""")
async def make_whatsapp_voice_call(contact_name: str) -> str:
    """Instantly snaps to the contact chat and natively clicks the Voice Call button."""
    logger.info(f"📞 ARYA WhatsApp Voice Call Initiated: {contact_name}")
    
    number = get_phone_number_from_contacts(contact_name)
    if not number:
        return f"Bro, lagta hai '{contact_name}' aapke Mac Contacts mein nahi hai."
        
    if not _snap_whatsapp_chat(number):
        return "Bhai, WhatsApp chat snap nahi ho paya. URL scheme fail hui."
        
    # Micro-pause to let UI transition state settle
    time.sleep(0.5)
    
    r = _trigger_accessibility_call("voice")
    if r == "success":
        logger.info(f"✅ Voice call successfully placed to {contact_name}")
        return f"Done bro! {contact_name} ko WhatsApp voice call ring hone lag gaya hai."
    else:
        logger.warning(f"Voice call failed: {r}")
        if "call_button_not_found" in r:
            return f"Chat open kar diya bro, lekin '{contact_name}' ke liye voice call ka option nahi mila."
        return f"Bro, call initiate karne mein problem aayi: {r}"

@llm.function_tool(description="""Initiate a WhatsApp video call to a contact.
Use this when the user says 'Arya, video call John', 'Put Mom on video on WhatsApp', etc.
Requires the exact contact name.""")
async def make_whatsapp_video_call(contact_name: str) -> str:
    """Instantly snaps to the contact chat and natively clicks the Video Call button."""
    logger.info(f"📹 ARYA WhatsApp Video Call Initiated: {contact_name}")
    
    number = get_phone_number_from_contacts(contact_name)
    if not number:
        return f"Bro, lagta hai '{contact_name}' aapke Mac Contacts mein nahi hai."
        
    if not _snap_whatsapp_chat(number):
        return "Bhai, WhatsApp chat snap nahi ho paya. URL scheme fail hui."
        
    # Micro-pause to let UI transition state settle
    time.sleep(0.5)
    
    r = _trigger_accessibility_call("video")
    if r == "success":
        logger.info(f"✅ Video call successfully placed to {contact_name}")
        return f"Done bro! {contact_name} ko WhatsApp video call ring hone lag gaya hai."
    else:
        logger.warning(f"Video call failed: {r}")
        if "call_button_not_found" in r:
            return f"Chat open kar diya bro, lekin '{contact_name}' ke liye video call ka option nahi mila."
        return f"Bro, video call initiate karne mein problem aayi: {r}"

# Export tools
WHATSAPP_CALL_TOOLS = [
    make_whatsapp_voice_call,
    make_whatsapp_video_call,
]
