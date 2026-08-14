"""
Native macOS Contacts Resolver for Arya
Uses AppleScript to fetch and format phone numbers dynamically from the user's Address Book.
"""

import subprocess
import re
import logging

logger = logging.getLogger("arya-agent")

def get_phone_number_from_contacts(name_query: str) -> str:
    """Fetch the contact's phone number natively from macOS Contacts and format it for WhatsApp."""
    
    # Escape quotes
    safe_name = name_query.replace('"', '\\"')
    
    script = f'''
    tell application "Contacts"
        try
            set thePerson to first person whose name contains "{safe_name}"
            set theNumber to value of first phone of thePerson
            return theNumber
        on error
            return "not_found"
        end try
    end tell
    '''
    
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    out = result.stdout.strip()
    
    if "not_found" in out or not out:
        logger.warning(f"No contacts found natively for '{name_query}'")
        return None
        
    # We got a number like "998-914-7064" or "+91 99891 47064"
    best_number = out
    
    # Normalize: keep digits and + sign only
    clean_number = re.sub(r'[^\d\+]', '', best_number)
    
    if not clean_number.startswith('+') and len(clean_number) >= 10:
        # Add default country code if missing (assumed +91 for this specific user given context)
        # We take the last 10 digits to be safe if it's longer
        clean_number = "+91" + clean_number[-10:]
        
    logger.info(f"Resolved native contact: '{name_query}' -> {clean_number}")
    return clean_number
