"""
ARYA Spotify Tools - API-Free Version
Pure AppleScript + Spotify URI scheme integration for native desktop playback.

NO SPOTIFY API CREDENTIALS REQUIRED!

Features:
- Search and play songs/artists/albums via Spotify URI
- Play playlists by name (search-based)
- Control playback (shuffle, repeat)
- Native Spotify app control via AppleScript
- ARYA's Hinglish Bro-slang persona
"""

import os
import time
import logging
import subprocess
import urllib.parse

from livekit.agents import llm

logger = logging.getLogger("arya-agent")


# ============================================
# 🔧 HELPER FUNCTIONS
# ============================================

def _ensure_spotify_open(background: bool = True) -> bool:
    """
    Ensure Spotify desktop app is open and ready.
    
    Args:
        background: If True, opens Spotify without bringing to foreground.
    
    Returns True if Spotify is ready, False otherwise.
    """
    try:
        # Check if Spotify is running
        check_script = '''
        tell application "System Events"
            return exists (process "Spotify")
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", check_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        is_running = "true" in result.stdout.lower()
        
        if not is_running:
            logger.info("🚀 Opening Spotify app...")
            # Use -g flag to open in background (don't bring to foreground)
            if background:
                os.system("open -g -a Spotify")
            else:
                os.system("open -a Spotify")
            time.sleep(3)  # Wait for Spotify to fully launch
            
            # Verify it opened
            result = subprocess.run(
                ["osascript", "-e", check_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_running = "true" in result.stdout.lower()
        
        return is_running
        
    except Exception as e:
        logger.error(f"❌ Error checking Spotify app: {e}")
        return False


def _is_spotify_playing() -> bool:
    """Check if Spotify is currently playing audio."""
    try:
        script = '''
        tell application "System Events"
            if exists (process "Spotify") then
                tell application "Spotify"
                    return player state as string
                end tell
            else
                return "not_running"
            end if
        end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "playing" in result.stdout.lower()
    except Exception:
        return False


def _play_spotify_uri(spotify_uri: str, shuffle: bool = False) -> bool:
    """
    Play a Spotify URI using native AppleScript.
    Works with track, album, artist, and playlist URIs.
    """
    try:
        if not _ensure_spotify_open():
            logger.error("❌ Could not open Spotify app")
            return False
        
        time.sleep(0.5)
        
        # Set shuffle if requested, then play
        if shuffle:
            script = f'''
            tell application "Spotify"
                set shuffling to true
                play track "{spotify_uri}"
            end tell
            '''
        else:
            script = f'''
            tell application "Spotify"
                play track "{spotify_uri}"
            end tell
            '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Playing URI: {spotify_uri}")
            return True
        else:
            logger.error(f"❌ AppleScript error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Play URI error: {e}")
        return False


def _open_spotify_search(query: str, search_type: str = "track") -> bool:
    """
    Open Spotify search for a query using URI scheme.
    
    Args:
        query: Search query
        search_type: 'track', 'artist', 'album', 'playlist'
    """
    try:
        if not _ensure_spotify_open():
            return False
        
        time.sleep(0.3)
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # Open Spotify search URI
        search_uri = f"spotify:search:{encoded_query}"
        os.system(f"open '{search_uri}'")
        
        logger.info(f"🔍 Opened Spotify search: {query}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return False


def _search_and_play_first_result(query: str) -> bool:
    """
    Search for something and play the first result using keyboard automation.
    """
    try:
        if not _ensure_spotify_open():
            return False
        
        time.sleep(0.5)
        
        # Open search, wait, then simulate Enter to play first result
        encoded_query = urllib.parse.quote(query)
        search_uri = f"spotify:search:{encoded_query}"
        
        script = f'''
        -- Open search
        do shell script "open '{search_uri}'"
        delay 2.5
        
        -- Focus Spotify and play first result
        tell application "Spotify"
            activate
        end tell
        
        delay 0.5
        
        tell application "System Events"
            tell process "Spotify"
                -- Press Enter to play first result
                key code 36
            end tell
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"❌ Search and play error: {e}")
        return False


# ============================================
# 🎵 SPOTIFY TOOL FUNCTIONS (LLM-CALLABLE)
# ============================================

@llm.function_tool(description="""Play a specific playlist from Spotify by name.
Use when user says things like:
- 'Play my gym playlist'
- 'Mera workout music chala do'
- 'Play chill vibes playlist'
- 'Party playlist baja do'
Pass the playlist name to search and play.""")
async def play_playlist(playlist_name: str) -> str:
    """
    Search for a playlist by name and play it.
    Uses Spotify search URI to find playlists.
    
    Args:
        playlist_name: Name of the playlist to play
    
    Returns:
        Success/failure message in Hinglish
    """
    logger.info(f"🎵 ARYA searching playlist: '{playlist_name}'")
    
    try:
        if not _ensure_spotify_open():
            return "Spotify app nahi khul raha bro, ek baar manually try kar."
        
        # Search for playlist using URI
        encoded_name = urllib.parse.quote(f"playlist:{playlist_name}")
        search_uri = f"spotify:search:{encoded_name}"
        
        # Open search and navigate to play
        script = f'''
        -- Open playlist search
        do shell script "open '{search_uri}'"
        delay 3
        
        -- Focus Spotify
        tell application "Spotify"
            activate
        end tell
        
        delay 0.5
        
        -- Navigate to first playlist result and play
        tell application "System Events"
            tell process "Spotify"
                -- Tab through to playlist section and play first result
                key code 36  -- Enter to play
            end tell
        end tell
        
        delay 0.5
        
        -- Enable shuffle for playlist
        tell application "Spotify"
            set shuffling to true
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return f"Playlist set hai bro! '{playlist_name}' searching aur playing. 🎵"
        else:
            logger.warning(f"⚠️ Playlist script warning: {result.stderr}")
            return f"'{playlist_name}' search kar diya hai, Spotify check kar bro!"
            
    except Exception as e:
        logger.error(f"❌ Playlist error: {e}")
        return f"Bhai, playlist play karne mein problem aayi. Manual try kar."


@llm.function_tool(description="""Play your Liked Songs (Favourites) from Spotify with shuffle control.
Use when user says things like:
- 'Play my liked songs' → Plays in background (default)
- 'Play my liked songs on Spotify' → Opens Spotify app and plays
- 'Play my favourite songs' or 'Play my favorites'
- 'Play my favourite song' (Treat singular as playlist)
- 'Meri favourite songs chala do'
- 'Shuffle my liked songs' (shuffle mode)
- 'Play my favorites with smart shuffle' (smart shuffle)

shuffle_mode options:
- 'none' = Play in order (DEFAULT)
- 'shuffle' = Random shuffle
- 'smart_shuffle' = Spotify's AI shuffle with recommendations

open_spotify: 
- false = Play in background without opening Spotify window (DEFAULT)
- true = Open Spotify app to foreground and play""")
async def play_liked_songs(shuffle_mode: str = "none", open_spotify: bool = False) -> str:
    """
    Play user's Liked Songs collection with shuffle control.
    
    Args:
        shuffle_mode: 'none' (default), 'shuffle', or 'smart_shuffle'
        open_spotify: If True, opens Spotify to foreground. If False, plays in background.
    
    Returns:
        Success/failure message in Hinglish
    """
    logger.info(f"❤️ ARYA playing Liked Songs (shuffle: {shuffle_mode}, foreground: {open_spotify})...")
    
    try:
        # Pass background=True (opposite of open_spotify) to control window behavior
        if not _ensure_spotify_open(background=not open_spotify):
            return "Spotify app nahi khul raha bro, manual try kar."
        
        # Normalize shuffle mode
        shuffle_mode = shuffle_mode.lower().strip()
        
        # Build AppleScript based on mode
        if open_spotify:
            # FOREGROUND MODE: Activate Spotify and play
            if shuffle_mode == "smart_shuffle":
                script = '''
                tell application "Spotify"
                    activate
                    play track "spotify:collection:tracks"
                    delay 0.5
                    set shuffling to true
                end tell
                
                delay 0.3
                tell application "System Events"
                    tell process "Spotify"
                        keystroke "s" using {command down, shift down}
                    end tell
                end tell
                '''
                shuffle_msg = "Smart Shuffle"
            elif shuffle_mode == "shuffle":
                script = '''
                tell application "Spotify"
                    activate
                    play track "spotify:collection:tracks"
                    delay 0.5
                    set shuffling to true
                end tell
                '''
                shuffle_msg = "Shuffle"
            else:
                script = '''
                tell application "Spotify"
                    activate
                    set shuffling to false
                    play track "spotify:collection:tracks"
                end tell
                '''
                shuffle_msg = "Order wise"
        else:
            # BACKGROUND MODE: Play without switching windows
            shuffle_setting = "true" if shuffle_mode == "shuffle" else "false"
            shuffle_msg = "Shuffle" if shuffle_mode == "shuffle" else "Order wise"
            
            # Smart shuffle requires foreground, fallback to regular shuffle
            if shuffle_mode == "smart_shuffle":
                shuffle_setting = "true"
                shuffle_msg = "Shuffle"  # Can't do smart shuffle in background
            
            script = f'''
            -- Remember current app
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
            end tell
            
            -- Play Liked Songs via AppleScript (more reliable than open -g)
            tell application "Spotify"
                play track "spotify:collection:tracks"
            end tell
            
            -- IMMEDIATELY refocus original app (in case Spotify steals focus)
            delay 0.1
            tell application "System Events"
                set frontmost of process frontApp to true
            end tell
            
            -- Set shuffle preference
            delay 0.5
            tell application "Spotify"
                set shuffling to {shuffle_setting}
            end tell
            '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            location_msg = "Spotify pe" if open_spotify else "background mein"
            return f"Liked Songs {location_msg} laga diya bro! ({shuffle_msg}) ❤️🎵"
        else:
            logger.warning(f"⚠️ Liked Songs warning: {result.stderr}")
            return "Liked Songs khol diya hai, Spotify check kar bro!"
            
    except Exception as e:
        logger.error(f"❌ Liked songs error: {e}")
        return f"Bhai, Liked Songs mein problem aayi: {str(e)[:50]}"


@llm.function_tool(description="""Search and play any song, artist, or album on Spotify.
Use when user says things like:
- 'Play Blinding Lights by Weeknd'
- 'Arijit Singh ke gaane chala do'
- 'Play the album Lover by Taylor Swift'
- 'Play some Bollywood songs'
Pass the search query - song name, artist name, or album name.""")
async def search_and_play(query: str) -> str:
    """
    Search Spotify for songs/artists/albums and play the result.
    Uses Spotify URI scheme for searching.
    
    Args:
        query: Search query (song, artist, or album name)
    
    Returns:
        Success/failure message in Hinglish
    """
    logger.info(f"🔍 ARYA searching Spotify: '{query}'")
    
    try:
        if not _ensure_spotify_open():
            return "Spotify app nahi khul raha bro, ek baar manually check kar."
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        search_uri = f"spotify:search:{encoded_query}"
        
        # Open search and play first result
        script = f'''
        -- Open Spotify search
        do shell script "open '{search_uri}'"
        
        delay 2.5
        
        -- Focus Spotify and wait for results
        tell application "Spotify"
            activate
        end tell
        
        delay 1
        
        -- Play first result by pressing Enter
        tell application "System Events"
            tell process "Spotify"
                key code 36  -- Enter to play first result
            end tell
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return f"Baj raha hai bro! '{query}' search karke first result play kar diya. 🎵"
        else:
            logger.warning(f"⚠️ Search warning: {result.stderr}")
            return f"'{query}' search kar diya, Spotify check kar bro!"
            
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return f"Bhai, search mein problem aayi: {str(e)[:50]}"


@llm.function_tool(description="""Play songs by a specific artist on Spotify.
Use when user says things like:
- 'Play Arijit Singh'
- 'Taylor Swift ke gaane chala do'
- 'Play songs by Diljit'
- 'Ed Sheeran sunao'
Pass just the artist name.""")
async def play_artist(artist_name: str) -> str:
    """
    Search and play songs by a specific artist.
    
    Args:
        artist_name: Name of the artist
    
    Returns:
        Success/failure message in Hinglish
    """
    logger.info(f"🎤 ARYA playing artist: '{artist_name}'")
    
    try:
        if not _ensure_spotify_open():
            return "Spotify app nahi khul raha bro."
        
        # Search for artist specifically
        encoded_query = urllib.parse.quote(f"artist:{artist_name}")
        search_uri = f"spotify:search:{encoded_query}"
        
        script = f'''
        -- Open artist search
        do shell script "open '{search_uri}'"
        
        delay 2.5
        
        tell application "Spotify"
            activate
        end tell
        
        delay 1
        
        -- Play first artist result
        tell application "System Events"
            tell process "Spotify"
                key code 36  -- Enter to select/play
            end tell
        end tell
        
        delay 0.5
        
        -- Enable shuffle for variety
        tell application "Spotify"
            set shuffling to true
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return f"'{artist_name}' ke gaane baj rahe hain bro! Shuffle bhi on kar diya. 🎤🎵"
        else:
            return f"'{artist_name}' search kar diya, Spotify check karo!"
            
    except Exception as e:
        logger.error(f"❌ Artist play error: {e}")
        return f"Artist play karne mein problem aayi bro."


@llm.function_tool(description="""Play a specific album on Spotify.
Use when user says things like:
- 'Play the album Starboy'
- 'Lover album chala do'
- 'Play Divide album by Ed Sheeran'
Pass the album name (and optionally artist).""")
async def play_album(album_name: str) -> str:
    """
    Search and play a specific album.
    
    Args:
        album_name: Name of the album (can include artist)
    
    Returns:
        Success/failure message in Hinglish
    """
    logger.info(f"💿 ARYA playing album: '{album_name}'")
    
    try:
        if not _ensure_spotify_open():
            return "Spotify app nahi khul raha bro."
        
        # Search for album specifically
        encoded_query = urllib.parse.quote(f"album:{album_name}")
        search_uri = f"spotify:search:{encoded_query}"
        
        script = f'''
        -- Open album search
        do shell script "open '{search_uri}'"
        
        delay 2.5
        
        tell application "Spotify"
            activate
        end tell
        
        delay 1
        
        -- Play first album result
        tell application "System Events"
            tell process "Spotify"
                key code 36  -- Enter
            end tell
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return f"Album '{album_name}' baj raha hai bro! Enjoy the vibes. 💿🎵"
        else:
            return f"'{album_name}' album search kar diya, Spotify check karo!"
            
    except Exception as e:
        logger.error(f"❌ Album play error: {e}")
        return f"Album play karne mein issue aayi bro."


# ============================================
# 📦 EXPORT ALL TOOLS
# ============================================

SPOTIFY_TOOLS = [
    play_playlist,
    play_liked_songs,
    search_and_play,
    play_artist,
    play_album,
]
