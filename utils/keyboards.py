from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def main_menu(has_userbot: bool = False):
    """Menu utama"""
    if has_userbot:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Buat Userbot", callback_data="create_userbot")],
            [InlineKeyboardButton("🛒 Toko", callback_data="store"),
             InlineKeyboardButton("🔑 Klaim Token", callback_data="claim_token")],
            [InlineKeyboardButton("📚 Panduan", callback_data="guide"),
             InlineKeyboardButton("💡 Fitur", callback_data="features")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Buat Userbot", callback_data="create_userbot")],
            [InlineKeyboardButton("🎁 Coba Gratis", callback_data="try_free")],
            [InlineKeyboardButton("📚 Panduan Buat", callback_data="guide_create"),
             InlineKeyboardButton("💡 Fitur Unggulan", callback_data="features")]
        ])

def subscription_menu():
    """Menu langganan"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Beli Userbot", callback_data="buy_userbot")],
        [InlineKeyboardButton("🎁 Hadiahkan Userbot", callback_data="gift_userbot")],
        [InlineKeyboardButton("🌐 Beli Username Grup", callback_data="buy_username"),
         InlineKeyboardButton("🚀 Beli Reseller", callback_data="buy_reseller")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")]
    ])

def package_menu():
    """Pilih tipe layanan"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 (Full Fitur) Basic", callback_data="package_basic"),
         InlineKeyboardButton("💎 (Full Fitur) Spesial", callback_data="package_spesial")],
        [InlineKeyboardButton("💬 WTB Basic", callback_data="package_wtb_basic"),
         InlineKeyboardButton("🔥 WTB Spesial", callback_data="package_wtb_spesial")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]
    ])

def basic_type_menu():
    """Pilih tipe basic"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Basic Hemat (Rp 5,000)", callback_data="basic_hemat")],
        [InlineKeyboardButton("💎 Basic Sultan (Rp 7,000)", callback_data="basic_sultan")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")]
    ])

def confirm_payment_menu(price: int):
    """Konfirmasi pembayaran"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➖", callback_data="decrease"),
         InlineKeyboardButton("📅 1 Bulan", callback_data="duration"),
         InlineKeyboardButton("➕", callback_data="increase")],
        [InlineKeyboardButton(f"✅ Bayar Rp. {price:,}", callback_data="pay_now")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")]
    ])

def cancel_button():
    """Tombol batal"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Batal", callback_data="cancel_creation")
    ]])

def control_panel(auto_promo: bool = False, pm_permit: bool = False):
    """Panel kontrol userbot"""
    keyboard = [
        [InlineKeyboardButton("▶️ Mulai Promosi", callback_data="start_promo")],
        [InlineKeyboardButton("🛒 Toko", callback_data="store"),
         InlineKeyboardButton("🧩 Fitur Ekstra", callback_data="extra")],
        [InlineKeyboardButton("✍️ Atur Pesan", callback_data="set_message"),
         InlineKeyboardButton("🎯 Atur Grup", callback_data="set_groups")],
        [InlineKeyboardButton("⏱️ Atur Jeda", callback_data="set_delay")],
        [InlineKeyboardButton("📚 Panduan Pakai", callback_data="guide_usage")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]
    ]
    
    # Tambah tombol toggle di atas
    toggle_text = "🔴 Matikan Auto" if auto_promo else "🟢 Aktifkan Auto"
    keyboard.insert(0, [InlineKeyboardButton(toggle_text, callback_data="toggle_auto")])
    
    return InlineKeyboardMarkup(keyboard)
