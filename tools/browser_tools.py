"""
ARYA Browser Tools - Visual Chrome Search
For when user specifically wants to see search results in browser.
"""

import logging
import urllib.parse
import subprocess
from livekit.agents import function_tool

logger = logging.getLogger("arya-agent")

@function_tool
async def search_on_chrome(query: str) -> str:
    """
    Open Chrome and search for the specified query visually.
    
    CRITICAL: Use this tool ONLY when the user EXPLICITLY requests to:
    - "Open Chrome"
    - "Show me on Chrome"
    - "Search in browser"
    - "Open browser"
    
    Do NOT use this for general questions like "Search for X", "Research Y", or "Who is Z?".
    For those, use the backend search tools.
    
    Args:
        query: What to search for in Chrome
    """
    try:
        logger.info(f"🌐 Opening Chrome to search: {query}")
        
        # Encode the query for URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        # Open Chrome with the search URL
        subprocess.run(["open", "-a", "Google Chrome", search_url], check=True)
        
        return f"🌐 Chrome opened with search results for '{query}'. You can see the results visually in your browser!"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Failed to open Chrome: {e}"
    except Exception as e:
        return f"⚠️ Error opening Chrome: {e}"

@function_tool
async def open_website(url: str) -> str:
    """
    Open a specific website in Chrome.
    
    Use this when user wants to visit a specific website.
    
    Args:
        url: Website URL to open (with or without https://)
    """
    try:
        logger.info(f"🌐 Opening website: {url}")
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        # Open Chrome with the URL
        subprocess.run(["open", "-a", "Google Chrome", url], check=True)
        
        return f"🌐 Opened {url} in Chrome for you!"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Failed to open website: {e}"
    except Exception as e:
        return f"⚠️ Error opening website: {e}"

# Export browser tools
BROWSER_TOOLS = [
    search_on_chrome,
    open_website,
]
