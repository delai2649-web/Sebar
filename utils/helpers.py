import re
import random
import string
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict

def generate_token(length: int = 32) -> str:
    """Generate secure token"""
    return secrets.token_urlsafe(length)

def generate_random_string(length: int = 10) -> str:
    """Generate random string"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def parse_time_string(time_str: str) -> Optional[int]:
    """Parse string waktu ke detik"""
    units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    match = re.match(r'^(\d+)([smhd])$', time_str.lower())
    if match:
        value, unit = match.groups()
        return int(value) * units.get(unit, 0)
    return None

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

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate teks"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + suffix

def get_expiry_text(expiry_date: str) -> str:
    """Format expiry dengan status"""
    try:
        expiry = datetime.fromisoformat(expiry_date)
        now = datetime.now()
        diff = expiry - now
        
        if diff.days < 0:
            return f"❌ EXPIRED"
        elif diff.days == 0:
            hours = diff.seconds // 3600
            return f"⚠️ {hours}j lagi"
        elif diff.days <= 3:
            return f"⚠️ {diff.days}h lagi"
        else:
            return expiry.strftime("%d-%m-%Y %H:%M")
    except:
        return "Unknown"

def format_number(num: int) -> str:
    """Format angka dengan separator"""
    return f"{num:,}".replace(",", ".")

def is_valid_phone(phone: str) -> bool:
    """Validasi nomor telepon"""
    return bool(re.match(r'^\+[1-9]\d{7,14}$', phone))

def is_valid_otp(otp: str) -> bool:
    """Validasi format OTP"""
    otp_clean = otp.replace(' ', '')
    return otp_clean.isdigit() and 4 <= len(otp_clean) <= 6

def clean_phone_number(phone: str) -> str:
    """Bersihkan nomor telepon"""
    return phone.replace(' ', '').replace('-', '').replace('+', '').replace('(', '').replace(')', '')

def mask_phone(phone: str) -> str:
    """Masking nomor telepon"""
    if len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-3:]

def generate_qris_string(amount: int, merchant_name: str = "SEBAR BOT") -> str:
    """Generate QRIS string (simplified)"""
    # Ini placeholder, seharusnya integrate dengan payment gateway
    return f"QRIS-{generate_random_string(16)}-{amount}"

def time_ago(dt: datetime) -> str:
    """Format datetime ke time ago"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365} tahun lalu"
    elif diff.days > 30:
        return f"{diff.days // 30} bulan lalu"
    elif diff.days > 0:
        return f"{diff.days} hari lalu"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} jam lalu"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} menit lalu"
    else:
        return "baru saja"
