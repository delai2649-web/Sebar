import re
import random
import string
from datetime import datetime
from typing import Optional, List

def generate_token(length: int = 10) -> str:
    """Generate random token"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def format_duration(seconds: int) -> str:
    """Format detik ke readable"""
    if seconds < 60:
        return f"{seconds}d"
    elif seconds < 3600:
        return f"{seconds//60}m"
    elif seconds < 86400:
        return f"{seconds//3600}j"
    else:
        return f"{seconds//86400}h"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate teks"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."

def get_expiry_text(expiry_date: str) -> str:
    """Format expiry dengan status"""
    try:
        expiry = datetime.fromisoformat(expiry_date)
        now = datetime.now()
        diff = expiry - now
        
        if diff.days < 0:
            return f"❌ EXPIRED"
        elif diff.days <= 3:
            return f"⚠️ {diff.days} hari lagi"
        else:
            return expiry.strftime("%d-%m-%Y %H:%M")
    except:
        return "Unknown"

def format_number(num: int) -> str:
    """Format angka"""
    return f"{num:,}".replace(",", ".")

def extract_invite_hash(link: str) -> Optional[str]:
    """Extract hash dari link grup"""
    patterns = [
        r't\.me/\+?([\w-]+)$',
        r't\.me/joinchat/([\w-]+)$'
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

def is_valid_group_link(link: str) -> bool:
    """Cek validitas link"""
    patterns = [
        r'^https?://t\.me/\+[\w-]+$',
        r'^https?://t\.me/joinchat/[\w-]+$',
        r'^https?://t\.me/[\w_]+$'
    ]
    return any(re.match(pattern, link) for pattern in patterns)
