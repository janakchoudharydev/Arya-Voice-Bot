"""
ARYA Mac Control Tools
All Mac system control functions for the ARYA voice assistant.
"""

import os
import logging
import subprocess
import urllib.parse

from livekit.agents import llm
from tools.whatsapp_tools import WHATSAPP_TOOLS  # Import WhatsApp tools separately
from tools.whatsapp_call_tools import WHATSAPP_CALL_TOOLS  # Import WhatsApp call tools
from tools.spotify_tools import SPOTIFY_TOOLS  # Import Spotify tools

logger = logging.getLogger("arya-agent")


# ============================================
# 🖥️ SYSTEM CONTROLS
# ============================================

@llm.function_tool(description="Restarts the Mac immediately.")
async def restart_mac():
    logger.info("🔄 ARYA is triggering a System Restart...")
    os.system("osascript -e 'tell app \"System Events\" to restart'")
    return "System restart ho raha hai, bro. Thodi der mein milte hain!"


@llm.function_tool(description="Shuts down the Mac immediately.")
async def shutdown_mac():
    logger.info("🛑 ARYA is triggering a System Shutdown...")
    os.system("osascript -e 'tell app \"System Events\" to shut down'")
    return "Baad mein milte hain, bro!"



@llm.function_tool(description="Puts the Mac to sleep mode immediately. Use when user says 'sleep mode', 'mac ko sleep par dal do', or 'put mac to sleep'.")
async def sleep_mac():
    logger.info("😴 ARYA is putting Mac to sleep...")
    os.system("pmset sleepnow")
    return "Mac ko sleep mode mein daal diya, bro. Sweet dreams!"


@llm.function_tool(description="Locks the Mac screen immediately.")
async def lock_screen():
    logger.info("🔒 ARYA is locking the screen...")
    os.system("pmset displaysleepnow")
    return "Screen lock kar diya, bro. Privacy mode on!"


# ============================================
# 📱 APPLICATION LIFECYCLE CONTROLS
# ============================================

@llm.function_tool(description="""Opens a specific application on the Mac and brings it to the foreground.
Pass the app name like 'Spotify', 'WhatsApp', 'Chrome', 'Safari', 'Finder'.
Use when user says 'open Safari', 'Spotify kholo', 'Chrome launch karo', etc.""")
async def open_app(app_name: str):
    """Opens an application by name and brings it to foreground."""
    logger.info(f"🚀 ARYA is opening: {app_name}")
    
    # Use 'open -a' to launch and bring to foreground
    result = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return f"Done bro! {app_name} khul gaya hai aur front pe aa gaya."
    else:
        logger.error(f"Failed to open {app_name}: {result.stderr}")
        return f"Bro, {app_name} nahi mila ya open nahi ho paya. Naam check kar ek baar."


@llm.function_tool(description="""Minimizes an application window to the dock (yellow button behavior).
The app stays running in background, just the window is hidden.
Use when user says 'minimize Safari', 'Chrome ko dock mein daal do', 'window hatao', etc.""")
async def minimize_app(app_name: str):
    """Minimizes the frontmost window of an application (like clicking yellow button)."""
    logger.info(f"📥 ARYA is minimizing: {app_name}")
    
    # AppleScript to minimize window 1 (frontmost) of the app
    script = f'''
    tell application "{app_name}"
        activate
        delay 0.2
    end tell
    
    tell application "System Events"
        tell process "{app_name}"
            if exists window 1 then
                set value of attribute "AXMinimized" of window 1 to true
                return "success"
            else
                return "no_window"
            end if
        end tell
    end tell
    '''
    
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if "success" in result.stdout:
        return f"Window minimize kar diya bro! {app_name} dock mein ja chuka hai, background mein chal raha hai."
    elif "no_window" in result.stdout:
        return f"Bro, {app_name} ki koi window nahi hai minimize karne ke liye."
    else:
        logger.error(f"Minimize failed: {result.stderr}")
        return f"Minimize mein kuch gadbad ho gayi, bro. {result.stderr}"


@llm.function_tool(description="""Closes the frontmost window of an application (red X button / Cmd+W behavior).
The app keeps running, only the active window is closed.
Use when user says 'close window', 'window band karo', 'Safari ki window close karo', etc.""")
async def close_window(app_name: str):
    """Closes only the frontmost window of an app (Cmd+W behavior). App stays running."""
    logger.info(f"❌ ARYA is closing window of: {app_name}")
    
    # AppleScript to close only window 1 (frontmost) - app stays running
    script = f'''
    tell application "{app_name}"
        activate
        delay 0.2
    end tell
    
    tell application "System Events"
        tell process "{app_name}"
            if exists window 1 then
                -- Simulate Cmd+W to close window
                keystroke "w" using command down
                return "success"
            else
                return "no_window"
            end if
        end tell
    end tell
    '''
    
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if "success" in result.stdout:
        return f"Window hata diya hai bro, {app_name} background mein chal rahi hai."
    elif "no_window" in result.stdout:
        return f"Bro, {app_name} ki koi window open nahi hai close karne ke liye."
    else:
        logger.error(f"Close window failed: {result.stderr}")
        return f"Window close karne mein problem aayi, bro."


@llm.function_tool(description="""Completely quits an application (Cmd+Q behavior).
This fully exits the app and frees up RAM.
Use when user says 'quit Safari', 'Chrome band karo totally', 'app puri tarah close karo', 'kill app', etc.""")
async def quit_app(app_name: str):
    """Completely quits an application (Cmd+Q). Frees up RAM."""
    logger.info(f"🛑 ARYA is quitting: {app_name}")
    
    # AppleScript to gracefully quit the app (like Cmd+Q)
    script = f'''
    tell application "{app_name}"
        quit
    end tell
    '''
    
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0:
        return f"App puri tarah se uda di hai bro! {app_name} quit ho gaya, RAM ekdum clean hai!"
    else:
        # Fallback: try using System Events keystroke
        logger.warning(f"AppleScript quit failed, trying Cmd+Q...")
        fallback_script = f'''
        tell application "{app_name}"
            activate
            delay 0.2
        end tell
        
        tell application "System Events"
            keystroke "q" using command down
        end tell
        '''
        subprocess.run(["osascript", "-e", fallback_script], capture_output=True, timeout=10)
        return f"{app_name} ko puri tarah quit kar diya, bro! Memory free ho gayi."


# ============================================
# 🔊 VOLUME CONTROLS
# ============================================

@llm.function_tool(description="Sets Mac volume. Pass level from 0 to 100.")
async def set_volume(level: int):
    """Sets the system volume to a specific level."""
    logger.info(f"🔊 ARYA is setting volume to {level}%")
    os.system(f"osascript -e 'set volume output volume {level}'")
    return f"Volume {level}% par set kar diya, bro!"


@llm.function_tool(description="Mutes the Mac audio completely.")
async def mute_audio():
    """Mutes the system audio."""
    logger.info("🔇 ARYA is muting audio...")
    os.system("osascript -e 'set volume with output muted'")
    return "Audio mute kar diya, bro! Silence mode on."


@llm.function_tool(description="Unmutes the Mac audio.")
async def unmute_audio():
    """Unmutes the system audio."""
    logger.info("🔊 ARYA is unmuting audio...")
    os.system("osascript -e 'set volume without output muted'")
    return "Audio unmute kar diya, bro! Sound is back."


@llm.function_tool(description="Increases Mac volume by 10%.")
async def volume_up():
    """Increases volume by 10%."""
    logger.info("🔺 ARYA is increasing volume...")
    os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
    return "Volume badha diya, bro!"


@llm.function_tool(description="Decreases Mac volume by 10%.")
async def volume_down():
    """Decreases volume by 10%."""
    logger.info("🔻 ARYA is decreasing volume...")
    os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
    return "Volume kam kar diya, bro!"


# ============================================
# 🌐 BROWSER & WEB CONTROLS
# ============================================

@llm.function_tool(description="Opens a URL in the default browser. Pass the full URL starting with http or https.")
async def open_url(url: str):
    """Opens a URL in the default browser."""
    logger.info(f"🌐 ARYA is opening URL: {url}")
    os.system(f"open '{url}'")
    return f"URL khol diya, bro: {url}"


@llm.function_tool(description="Searches Google for any query. Pass what you want to search.")
async def google_search(query: str):
    """Performs a Google search."""
    logger.info(f"🔍 ARYA is searching Google: {query}")
    encoded = urllib.parse.quote(query)
    os.system(f"open 'https://www.google.com/search?q={encoded}'")
    return f"Google pe search kar raha hoon: {query}"


@llm.function_tool(description="Searches YouTube for any video. Pass what you want to search.")
async def youtube_search(query: str):
    """Performs a YouTube search."""
    logger.info(f"📺 ARYA is searching YouTube: {query}")
    encoded = urllib.parse.quote(query)
    os.system(f"open 'https://www.youtube.com/results?search_query={encoded}'")
    return f"YouTube pe search kar raha hoon: {query}"


# ============================================
# 🎵 MEDIA CONTROLS (Works even when app is not focused!)
# ============================================

@llm.function_tool(description="Play or Pause music/song. Works even when you're working in another app. Use this when user says 'pause song', 'play song', 'pause music', 'play music', 'song roko', 'gaana chala', etc.")
async def play_pause():
    """Toggles play/pause for Spotify (works in background) or uses media keys as fallback."""
    logger.info("⏯️ ARYA toggling play/pause...")
    
    # First try Spotify directly (works even when not focused)
    script = '''
    tell application "System Events"
        if exists (process "Spotify") then
            tell application "Spotify" to playpause
            return "spotify"
        else
            -- Fallback: Use media key (F8 - Play/Pause key)
            key code 100
            return "mediakey"
        end if
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    
    if "spotify" in result.stdout.lower():
        return "Song pause/play kar diya, bro! Spotify control ho gaya."
    else:
        return "Play/Pause kar diya, bro!"


@llm.function_tool(description="Skip to the next song/track. Works even when you're in another app. Use when user says 'next song', 'skip song', 'agla gaana', etc.")
async def next_track():
    """Skips to the next track on Spotify or uses media keys."""
    logger.info("⏭️ ARYA skipping to next track...")
    
    script = '''
    tell application "System Events"
        if exists (process "Spotify") then
            tell application "Spotify" to next track
            return "spotify"
        else
            -- Fallback: Use media key (F9 - Next track key)
            key code 101
            return "mediakey"
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return "Next track pe skip kar diya, bro!"


@llm.function_tool(description="Go back to the previous song/track. Works even when in another app. Use when user says 'previous song', 'last song', 'pichla gaana', etc.")
async def previous_track():
    """Goes to the previous track on Spotify or uses media keys."""
    logger.info("⏮️ ARYA going to previous track...")
    
    script = '''
    tell application "System Events"
        if exists (process "Spotify") then
            tell application "Spotify" to previous track
            return "spotify"
        else
            -- Fallback: Use media key (F7 - Previous track key)
            key code 109
            return "mediakey"
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return "Previous track pe wapas gaya, bro!"


@llm.function_tool(description="Play a specific song on Spotify. Pass the song name. Use when user says 'play [song name]', '[song name] chalao', etc.")
async def play_song_on_spotify(song_name: str):
    """Searches and plays a song on Spotify."""
    logger.info(f"🎵 ARYA playing on Spotify: {song_name}")
    
    # URL encode the song name for Spotify URI
    encoded_song = urllib.parse.quote(song_name)
    
    # Open Spotify search and play
    script = f'''
    tell application "Spotify"
        activate
        delay 0.5
    end tell
    
    -- Open Spotify search URI
    do shell script "open 'spotify:search:{encoded_song}'"
    '''
    os.system(f"osascript -e '{script}'")
    
    return f"Spotify pe '{song_name}' search kar raha hoon, bro! First result play hoga."


@llm.function_tool(description="Get info about the currently playing song - title, artist, and album.")
async def whats_playing():
    """Gets info about the currently playing track on Spotify."""
    logger.info("🎵 ARYA checking what's playing...")
    
    script = '''
    tell application "System Events"
        if exists (process "Spotify") then
            tell application "Spotify"
                if player state is playing then
                    set trackName to name of current track
                    set artistName to artist of current track
                    set albumName to album of current track
                    return "Playing: " & trackName & " by " & artistName & " from album " & albumName
                else
                    return "Spotify pe kuch nahi chal raha bro, music paused hai."
                end if
            end tell
        else
            return "Spotify band hai bro, koi song nahi chal raha."
        end if
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() if result.stdout.strip() else "Couldn't get song info, bro."


# ============================================
# 📁 FILE & FOLDER CONTROLS
# ============================================

@llm.function_tool(description="Opens a folder in Finder. Pass the folder path like '/Users/username/Documents'.")
async def open_folder(path: str):
    """Opens a folder in Finder."""
    logger.info(f"📁 ARYA is opening folder: {path}")
    os.system(f"open '{path}'")
    return f"Folder khol diya, bro: {path}"


@llm.function_tool(description="Opens the Downloads folder.")
async def open_downloads():
    """Opens the Downloads folder."""
    logger.info("📥 ARYA is opening Downloads...")
    os.system("open ~/Downloads")
    return "Downloads folder khol diya, bro!"


@llm.function_tool(description="Opens the Desktop folder.")
async def open_desktop():
    """Opens the Desktop folder."""
    logger.info("🖥️ ARYA is opening Desktop...")
    os.system("open ~/Desktop")
    return "Desktop folder khol diya, bro!"


@llm.function_tool(description="Opens the Documents folder.")
async def open_documents():
    """Opens the Documents folder."""
    logger.info("📄 ARYA is opening Documents...")
    os.system("open ~/Documents")
    return "Documents folder khol diya, bro!"


# ============================================
# 🔔 NOTIFICATIONS
# ============================================

@llm.function_tool(description="Shows a notification on Mac. Pass the title and message.")
async def show_notification(title: str, message: str):
    """Displays a macOS notification."""
    logger.info(f"🔔 ARYA is showing notification: {title}")
    os.system(f"osascript -e 'display notification \"{message}\" with title \"{title}\"'")
    return f"Notification dikha diya: {title}"


# ============================================
# 📊 SYSTEM INFO
# ============================================

@llm.function_tool(description="Gets the current battery percentage and charging status of the Mac.")
async def get_battery():
    """Gets battery status."""
    logger.info("🔋 ARYA is checking battery...")
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    output = result.stdout
    return f"Battery status: {output}"


@llm.function_tool(description="Gets the current date and time.")
async def get_time():
    """Gets current date and time."""
    from datetime import datetime
    now = datetime.now()
    formatted = now.strftime("%A, %d %B %Y, %I:%M %p")
    logger.info(f"🕐 Current time: {formatted}")
    return f"Bro, abhi time hai: {formatted}"


# ============================================
# 📝 QUICK ACTIONS
# ============================================

@llm.function_tool(description="Takes a screenshot and saves it to Desktop.")
async def take_screenshot():
    """Takes a screenshot."""
    logger.info("📸 ARYA is taking a screenshot...")
    os.system("screencapture -x ~/Desktop/screenshot_$(date +%Y%m%d_%H%M%S).png")
    return "Screenshot le liya, bro! Desktop pe save hai."


@llm.function_tool(description="Empties the Trash/Recycle Bin.")
async def empty_trash():
    """Empties the trash."""
    logger.info("🗑️ ARYA is emptying trash...")
    os.system("osascript -e 'tell application \"Finder\" to empty trash'")
    return "Trash khali kar diya, bro! Clean and clear."


# ============================================
# 📦 EXPORT ALL TOOLS
# ============================================

# List of all available tools for ARYA
ALL_MAC_TOOLS = [
    # System Controls
    restart_mac,
    shutdown_mac,
    sleep_mac,
    lock_screen,
    # App Lifecycle Controls
    open_app,
    minimize_app,
    close_window,
    quit_app,
    # Volume Controls
    set_volume,
    mute_audio,
    unmute_audio,
    volume_up,
    volume_down,
    # Browser Controls
    open_url,
    google_search,
    youtube_search,
    # Media Controls
    play_pause,
    next_track,
    previous_track,
    play_song_on_spotify,
    whats_playing,
    # File Controls
    open_folder,
    open_downloads,
    open_desktop,
    open_documents,
    # Notifications
    show_notification,
    # System Info
    get_battery,
    get_time,
    # Quick Actions
    take_screenshot,
    empty_trash,
    # WhatsApp Controls
    *WHATSAPP_TOOLS,
    # WhatsApp Call Controls
    *WHATSAPP_CALL_TOOLS,
    # Spotify Controls
    *SPOTIFY_TOOLS,
]
