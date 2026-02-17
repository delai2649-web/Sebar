from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Buat Userbot", callback_data="panel_control")],
        [InlineKeyboardButton("🛒 Toko", callback_data="store"),
         InlineKeyboardButton("🔑 Klaim Token", callback_data="claim_token")],
        [InlineKeyboardButton("📚 Panduan Buat", callback_data="guide_create"),
         InlineKeyboardButton("💡 Fitur Unggulan", callback_data="features")],
        [InlineKeyboardButton("🎁 Coba Gratis", callback_data="try_free")]
    ])

def control_panel(auto_promo: bool = False, pm_permit: bool = False):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Mulai Promosi", callback_data="start_broadcast")],
        [InlineKeyboardButton("🛒 Toko", callback_data="store"),
         InlineKeyboardButton("🧩 Fitur Ekstra", callback_data="extra_features")],
        [InlineKeyboardButton("✍️ Atur Pesan", callback_data="set_message"),
         InlineKeyboardButton("🎯 Atur Grup", callback_data="set_groups")],
        [InlineKeyboardButton("⏱️ Atur Jeda", callback_data="set_delay")],
        [InlineKeyboardButton("📚 Panduan Pakai", callback_data="guide_usage")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]
    ])

def group_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Topik Grup", callback_data="group_topics")],
        [InlineKeyboardButton("💡 Tambah Grup", callback_data="add_group"),
         InlineKeyboardButton("🗑️ Hapus Grup", callback_data="delete_group")],
        [InlineKeyboardButton("📚 Daftar Grup", callback_data="list_groups")],
        [InlineKeyboardButton("🚀 Gabung Grup", callback_data="join_group"),
         InlineKeyboardButton("👋 Keluar Grup", callback_data="leave_group")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]
    ])

def store_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Perpanjang Masa Aktif", callback_data="extend_active")],
        [InlineKeyboardButton("🎁 Hadiahkan Userbot", callback_data="gift_bot")],
        [InlineKeyboardButton("🌐 Beli Username Grup", callback_data="buy_username"),
         InlineKeyboardButton("🚀 Beli Reseller", callback_data="buy_reseller")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu")]
    ])

def package_selection():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆓 FREE (1 hari)", callback_data="package_FREE")],
        [InlineKeyboardButton("💎 BASIC - Rp 20k", callback_data="package_BASIC")],
        [InlineKeyboardButton("⭐ STANDARD - Rp 50k", callback_data="package_STANDARD")],
        [InlineKeyboardButton("👑 PRO - Rp 100k", callback_data="package_PRO")],
        [InlineKeyboardButton("🏢 ENTERPRISE - Rp 500k", callback_data="package_ENTERPRISE")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="store")]
    ])

def broadcast_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Mulai Sekarang", callback_data="broadcast_now")],
        [InlineKeyboardButton("⏰ Jadwalkan", callback_data="broadcast_schedule")],
        [InlineKeyboardButton("🔄 Auto Repeat", callback_data="broadcast_repeat")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="panel_control")]
    ])

def confirm_broadcast(group_count: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Ya, Kirim ke {group_count} Grup", callback_data="confirm_broadcast")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_broadcast")]
    ])
