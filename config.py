import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Credentials
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Admin
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///auto_sebar.db")
    
    # Paths
    SESSION_NAME = "userbot_session/main"
    DOWNLOADS_DIR = "downloads/"
    LOGS_DIR = "logs/"
    
    # Broadcast Settings
    DEFAULT_DELAY = 30  # detik
    DEFAULT_PACKAGE = "BASIC"
    
    # Package Limits
    PACKAGES = {
        "FREE": {"max_groups": 5, "delay": 120, "days": 1, "price": 0},
        "BASIC": {"max_groups": 50, "delay": 60, "days": 7, "price": 20000},
        "STANDARD": {"max_groups": 150, "delay": 30, "days": 30, "price": 50000},
        "PRO": {"max_groups": 500, "delay": 10, "days": 30, "price": 100000},
        "ENTERPRISE": {"max_groups": 9999, "delay": 5, "days": 365, "price": 500000}
    }
    
    # Auto Features
    AUTO_JOIN_GROUPS = True
    AUTO_LEAVE_BANNED = True
    CAPTCHA_SOLVER = False
    
    # Payment (contoh)
    PAYMENT_CHANNELS = {
        "dana": os.getenv("DANA_NUMBER"),
        "gopay": os.getenv("GOPAY_NUMBER"),
        "ovo": os.getenv("OVO_NUMBER")
    }

class Messages:
    WELCOME = """
👋 <b>Halo, {name}!</b>

🚀 Anda selangkah lebih dekat menuju <b>Era Baru Promosi!</b> di @JasebXBot

Lupakan cara lama yang membuang waktu & tenaga. Bersama saya, promosi ke puluhan/ratusan grup ada dalam genggaman Anda, siap menerima pesan promosi secara <b>otomatis, terjadwal, dan tanpa batas.</b>

⭐ <b>Klik menu di bawah untuk memulai revolusi promosi Anda!</b>

🔔 <b>Ads:</b> <a href='https://t.me/NokosID_UBot'>Beli Akun OLD Untuk UBOT? Otomatis DI Sini AJA @NokosID_UBot!!!</a>
"""
    
    PANEL_CONTROL = """
🚀 <b>Panel Kontrol Auto Promosi</b> 🚀

┏━━━━━━━━━━━━━━━━━━━━━┓
┃ ⭐ <b>Auto Promosi:</b> {auto_status}
┃ 🛡️ <b>PM Permit:</b> {pm_status}
┃ 🆔 <b>ID Userbot:</b> <code>{user_id}</code>
┃ 💎 <b>Paket:</b> {package}
┃ 📅 <b>Kedaluwarsa:</b> {expiry}
┃ 📊 <b>Total Grup:</b> {total_groups}/{max_groups}
┗━━━━━━━━━━━━━━━━━━━━━┛

🔔 <b>Ads:</b> <a href='https://t.me/NokosID_UBot'>Beli Akun OLD Untuk UBOT? Otomatis DI Sini AJA @NokosID_UBot!!!</a>
"""
    
    GROUP_MENU = """
🎯 <b>Pengaturan Target Grup:</b>

📊 <b>Statistik Grup:</b>
• Total Grup: {total_groups}
• Aktif: {active_groups}
• Diblokir: {banned_groups}
• Pending: {pending_groups}
"""
    
    STORE_MENU = """
🛍️ <b>MENU STORE & LAYANAN</b>

Silakan pilih kategori produk yang ingin Anda akses di bawah ini:

💎 <b>Paket Tersedia:</b>
• FREE - Rp 0 (1 hari, 5 grup)
• BASIC - Rp 20.000 (7 hari, 50 grup)
• STANDARD - Rp 50.000 (30 hari, 150 grup)
• PRO - Rp 100.000 (30 hari, 500 grup)
• ENTERPRISE - Rp 500.000 (365 hari, unlimited)
"""
