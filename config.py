import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # Bot utama
    
    # Admin
    OWNER_ID = int(os.getenv("OWNER_ID"))
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sebar.db")
    
    # Paths
    USERBOT_DIR = "userbots/"
    
    # Payment
    QRIS_API_KEY = os.getenv("QRIS_API_KEY")  # Untuk QRIS otomatis
    QRIS_STATIC = os.getenv("QRIS_STATIC")     # QRIS statis (backup)
    
    # Harga Paket
    PACKAGES = {
        "basic_hemat": {
            "name": "Basic Hemat (Non-Garansi)",
            "price": 5000,
            "duration_days": 30,
            "garansi": False,
            "token_backup": False,
            "fitur": ["Auto Promosi", "Atur Grup", "Jeda", "Timer", "PM Permit", "Base Reply"]
        },
        "basic_sultan": {
            "name": "Basic Sultan (Bergaransi)",
            "price": 7000,
            "duration_days": 30,
            "garansi": True,
            "token_backup": True,
            "fitur": ["Auto Promosi", "Atur Grup", "Jeda", "Timer", "PM Permit", "Base Reply", "Extra Fitur"]
        },
        "wtb_basic": {
            "name": "WTB Basic",
            "price": 5000,
            "duration_days": 30,
            "garansi": False,
            "token_backup": False,
            "fitur": ["Base Reply/Auto Reply"]
        },
        "wtb_spesial": {
            "name": "WTB Spesial",
            "price": 10000,
            "duration_days": 30,
            "garansi": True,
            "token_backup": True,
            "fitur": ["Base Reply/Auto Reply", "Forward Support"]
        }
    }

class Messages:
    WELCOME = """
👋 <b>Halo, {name}!</b>

🚀 Selamat datang di <b>Userbot Sebar & WTB</b>

Lupakan cara lama yang membuang waktu & tenaga. Bersama kami, promosi ke puluhan/ratusan grup ada dalam genggaman Anda.

⭐ <b>Klik menu di bawah untuk memulai!</b>
"""
    
    NEED_SUBSCRIPTION = """
🔔 <b>Diperlukan Langganan</b> 🔔

🚀 Anda harus berlangganan untuk dapat membuat userbot.

📝 Pilih salah satu tombol di bawah ini untuk melanjutkan proses pembelian.
"""
    
    CREATE_USERBOT = """
🚀 <b>Buat Userbot</b>

Silakan bagikan nomor telepon Anda untuk membuat userbot.

📱 Format: <code>+628xxxxxxxxxx</code>

🔒 Nomor Anda aman dan terenkripsi.
"""
    
    OTP_SENT = """
⏳ <b>Sedang mengirim kode otentikasi...</b>

🔑 <b>Silakan Periksa Kode OTP Dari Akun Resmi Telegram.</b>

🔔 Kirim Code Dengan Format: <code>1 2 3 4 5</code> (Spasi)

📝 Ketik <code>/cancel</code> Untuk Membatalkan.
"""
    
    ENTER_2FA = """
🔐 <b>Akun Anda Dilindungi 2FA</b>

Silakan Masukkan Kata Sandi Anda.
"""
    
    USERBOT_CREATED = """
🎉 <b>Userbot Berhasil Diaktifkan!</b>

👤 <b>Nama:</b> {name}
🆔 <b>ID:</b> <code>{user_id}</b>

🔑 <b>Token Garansi Anda:</b>
<code>{token}</code>

⚠️ <b>HARAP SIMPAN TOKEN INI BAIK-BAIK!</b>

Ketik /start untuk melihat menu promosi.

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
┗━━━━━━━━━━━━━━━━━━━━━┛

🔔 <b>Ads:</b> <a href='https://t.me/NokosID_UBot'>Beli Akun OLD Untuk UBOT? Otomatis DI Sini AJA @NokosID_UBot!!!</a>
"""
