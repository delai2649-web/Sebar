import os
import sys
import logging
import asyncio
from datetime import datetime

from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, Messages
from database import db
from utils.keyboards import main_menu, control_panel, group_menu, store_menu, package_selection
from utils.helpers import get_expiry_text, format_number

# Setup logging
os.makedirs('logs', exist_ok=True)
os.makedirs('downloads', exist_ok=True)
os.makedirs('userbot_session', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Client
app = Client(
    "sebar_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir=".",
    parse_mode="html"
)

# ========== COMMAND HANDLERS ==========

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    """Handler untuk /start"""
    user = message.from_user
    
    # Add user ke database
    await db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.first_name + (" " + user.last_name if user.last_name else ""),
        phone=None
    )
    
    welcome_text = Messages.WELCOME.format(name=user.first_name)
    
    await message.reply_text(
        welcome_text,
        reply_markup=main_menu(),
        disable_web_page_preview=False
    )

@app.on_message(filters.command("panel") & filters.private)
async def panel_handler(client: Client, message: Message):
    """Handler untuk /panel"""
    await show_control_panel(message)

@app.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, message: Message):
    """Handler untuk /help"""
    text = """
<b>📚 Bantuan Auto Sebar Bot</b>

<b>Perintah Tersedia:</b>
• /start - Mulai bot
• /panel - Panel kontrol
• /help - Bantuan ini

<b>Cara Penggunaan:</b>
1. Klik '🚀 Buat Userbot'
2. Atur pesan broadcast di '✍️ Atur Pesan'
3. Tambah grup di '🎯 Atur Grup'
4. Klik '▶️ Mulai Promosi'

<b>Butuh bantuan?</b> Hubungi @admin
"""
    await message.reply_text(text)

# ========== CALLBACK HANDLERS ==========

@app.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    """Handler untuk semua callback button"""
    data = callback.data
    user_id = callback.from_user.id
    
    try:
        # Main Menu
        if data == "main_menu":
            await callback.edit_message_text(
                Messages.WELCOME.format(name=callback.from_user.first_name),
                reply_markup=main_menu(),
                disable_web_page_preview=False
            )
        
        # Panel Control
        elif data == "panel_control":
            await show_control_panel(callback.message, edit=True)
        
        # Toggle Auto Promosi
        elif data == "toggle_auto":
            new_status = await db.toggle_auto_promo(user_id)
            status_text = "AKTIF ✅" if new_status else "NONAKTIF ❌"
            await callback.answer(f"Auto Promosi: {status_text}", show_alert=True)
            await show_control_panel(callback.message, edit=True)
        
        # Store/Shop
        elif data == "store":
            await callback.edit_message_text(
                Messages.STORE_MENU,
                reply_markup=store_menu(),
                disable_web_page_preview=False
            )
        
        # Package Selection
        elif data.startswith("package_"):
            package = data.replace("package_", "")
            await handle_package_selection(callback, package)
        
        # Group Management
        elif data == "set_groups":
            await show_group_menu(callback)
        
        elif data == "add_group":
            await callback.edit_message_text(
                "📎 <b>Tambah Grup</b>\n\n"
                "Kirim link invite grup (https://t.me/+xxxxx)\n"
                "atau forward pesan dari grup.\n\n"
                "⏳ Menunggu input...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Batal", callback_data="set_groups")
                ]])
            )
        
        elif data == "list_groups":
            await show_group_list(callback)
        
        # Message Settings
        elif data == "set_message":
            await callback.edit_message_text(
                "✍️ <b>Atur Pesan Broadcast</b>\n\n"
                "Kirimkan pesan yang ingin disimpan sebagai template.\n"
                "Bisa berupa teks, foto, video, atau dokumen.\n\n"
                "Format tombol: [Text](https://t.me/link)",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="panel_control")
                ]])
            )
        
        # Broadcast
        elif data == "start_broadcast":
            await callback.answer("Memulai broadcast...", show_alert=False)
            await start_broadcast(client, callback)
        
        # Try Free
        elif data == "try_free":
            await callback.edit_message_text(
                "🎁 <b>COBA GRATIS</b>\n\n"
                "✅ Anda mendapatkan paket FREE selama 1 hari!\n"
                "• Maksimal 5 grup\n"
                "• Delay 120 detik\n\n"
                "Klik '🚀 Buat Userbot' untuk mulai!",
                reply_markup=main_menu()
            )
        
        # Claim Token
        elif data == "claim_token":
            await callback.edit_message_text(
                "🔑 <b>Klaim Token</b>\n\n"
                "Fitur ini akan segera hadir!",
                reply_markup=main_menu()
            )
        
        # Guide & Features
        elif data == "guide_create":
            await callback.edit_message_text(
                "📚 <b>Panduan Buat Userbot</b>\n\n"
                "1. Klik '🚀 Buat Userbot'\n"
                "2. Atur pesan broadcast\n"
                "3. Tambahkan target grup\n"
                "4. Aktifkan Auto Promosi\n"
                "5. Mulai broadcast!",
                reply_markup=main_menu()
            )
        
        elif data == "features":
            await callback.edit_message_text(
                "💡 <b>Fitur Unggulan</b>\n\n"
                "✅ Auto broadcast ke ratusan grup\n"
                "✅ Support teks, foto, video\n"
                "✅ Delay system anti-ban\n"
                "✅ Template management\n"
                "✅ Real-time statistics\n"
                "✅ Scheduled broadcast",
                reply_markup=main_menu()
            )
        
        else:
            await callback.answer("Fitur dalam pengembangan!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer("Terjadi kesalahan!", show_alert=True)

# ========== MESSAGE HANDLERS ==========

@app.on_message(filters.private & filters.text & ~filters.command(["start", "panel", "help"]))
async def text_handler(client: Client, message: Message):
    """Handler untuk text input"""
    user_id = message.from_user.id
    
    # Cek apakah sedang menunggu input grup
    if message.text.startswith(('https://t.me/', 't.me/')):
        # Proses link grup
        from plugins.groups import GroupManager
        gm = GroupManager(client)
        success, msg = await gm.join_group_via_link(user_id, message.text)
        await message.reply_text(msg, reply_markup=control_panel())
        return
    
    # Simpan sebagai template
    template_id = await db.save_template(
        user_id=user_id,
        name=f"Template {datetime.now().strftime('%H:%M')}",
        message_text=message.text,
        is_default=True
    )
    
    await message.reply_text(
        f"✅ Template disimpan!\n\n"
        f"Preview:\n<code>{message.text[:100]}{'...' if len(message.text) > 100 else ''}</code>",
        reply_markup=control_panel()
    )

@app.on_message(filters.private & filters.photo)
async def photo_handler(client: Client, message: Message):
    """Handler untuk foto template"""
    user_id = message.from_user.id
    
    template_id = await db.save_template(
        user_id=user_id,
        name=f"Photo {datetime.now().strftime('%H:%M')}",
        message_text=message.caption or "",
        media_type="photo",
        media_file_id=message.photo.file_id,
        is_default=True
    )
    
    await message.reply_text(
        "✅ Template foto disimpan!",
        reply_markup=control_panel()
    )

@app.on_message(filters.private & filters.video)
async def video_handler(client: Client, message: Message):
    """Handler untuk video template"""
    user_id = message.from_user.id
    
    template_id = await db.save_template(
        user_id=user_id,
        name=f"Video {datetime.now().strftime('%H:%M')}",
        message_text=message.caption or "",
        media_type="video",
        media_file_id=message.video.file_id,
        is_default=True
    )
    
    await message.reply_text(
        "✅ Template video disimpan!",
        reply_markup=control_panel()
    )

# ========== HELPER FUNCTIONS ==========

async def show_control_panel(message, edit=False):
    """Tampilkan panel kontrol"""
    user_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        text = "Silakan /start terlebih dahulu."
        if edit:
            await message.edit_text(text)
        else:
            await message.reply_text(text)
        return
    
    group_count = await db.get_group_count(user_id)
    package = Config.PACKAGES.get(user['package'], Config.PACKAGES['FREE'])
    
    text = Messages.PANEL_CONTROL.format(
        auto_status="✅ Aktif" if user['auto_promo'] else "❌ Nonaktif",
        pm_status="✅ Aktif" if user['pm_permit'] else "❌ Nonaktif",
        user_id=user_id,
        package=user['package'],
        expiry=get_expiry_text(user['expiry_date']),
        total_groups=group_count,
        max_groups=package['max_groups']
    )
    
    # Buat keyboard dengan tombol toggle
    keyboard = control_panel()
    keyboard.inline_keyboard.insert(0, [
        InlineKeyboardButton(
            "🔴 Matikan Auto" if user['auto_promo'] else "🟢 Aktifkan Auto",
            callback_data="toggle_auto"
        )
    ])
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=False)
    else:
        await message.reply_text(text, reply_markup=keyboard, disable_web_page_preview=False)

async def show_group_menu(callback: CallbackQuery):
    """Tampilkan menu grup"""
    user_id = callback.from_user.id
    
    from plugins.groups import GroupManager
    gm = GroupManager(app)
    stats = await gm.get_group_stats(user_id)
    
    text = f"""
🎯 <b>Pengaturan Target Grup</b>

📊 <b>Statistik Grup:</b>
• Total: {stats['total']}
• Aktif: {stats['active']}
• Diblokir: {stats['banned']}
• Pending: {stats['pending']}

💡 Pilih opsi di bawah:
"""
    
    await callback.edit_message_text(text, reply_markup=group_menu())

async def show_group_list(callback: CallbackQuery):
    """Tampilkan daftar grup"""
    user_id = callback.from_user.id
    groups = await db.get_user_groups(user_id)
    
    if not groups:
        text = "📭 Belum ada grup. Tambahkan grup terlebih dahulu."
    else:
        text = "📚 <b>Daftar Grup:</b>\n\n"
        for i, g in enumerate(groups[:20], 1):
            status_emoji = "🟢" if g['status'] == 'active' else "🔴"
            text += f"{i}. {status_emoji} {g['group_title'][:30]}\n"
        
        if len(groups) > 20:
            text += f"\n... dan {len(groups)-20} grup lainnya"
    
    await callback.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Kembali", callback_data="set_groups")
        ]])
    )

async def handle_package_selection(callback: CallbackQuery, package: str):
    """Handle pemilihan paket"""
    user_id = callback.from_user.id
    pkg = Config.PACKAGES.get(package)
    
    if not pkg:
        await callback.answer("Paket tidak valid!", show_alert=True)
        return
    
    if package == "FREE":
        await db.extend_package(user_id, "FREE", pkg['days'])
        await callback.edit_message_text(
            f"✅ Paket FREE diaktifkan!\n\n"
            f"📅 Masa aktif: {pkg['days']} hari\n"
            f"👥 Max grup: {pkg['max_groups']}\n"
            f"⏱️ Delay: {pkg['delay']} detik",
            reply_markup=control_panel()
        )
    else:
        text = (
            f"💳 <b>Pembayaran Paket {package}</b>\n\n"
            f"Harga: Rp {format_number(pkg['price'])}\n"
            f"Masa aktif: {pkg['days']} hari\n"
            f"Max grup: {pkg['max_groups']}\n"
            f"Delay: {pkg['delay']} detik\n\n"
            f"Silakan transfer ke:\n"
        )
        
        for method, number in Config.PAYMENT_CHANNELS.items():
            if number:
                text += f"• {method.upper()}: <code>{number}</code>\n"
        
        text += f"\nKirim bukti pembayaran ke admin"
        
        await callback.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="store")
            ]])
        )

async def start_broadcast(client: Client, callback: CallbackQuery):
    """Mulai broadcast"""
    user_id = callback.from_user.id
    
    from plugins.broadcast import BroadcastManager
    bm = BroadcastManager(client)
    
    result, msg = await bm.start_broadcast(user_id)
    
    if result and isinstance(msg, dict):
        template = msg['template']
        groups = msg['groups']
        
        preview = template['message_text'][:200] + "..." if len(template['message_text']) > 200 else template['message_text']
        
        text = (
            f"📋 <b>Konfirmasi Broadcast</b>\n\n"
            f"📝 Template: <code>{template['name']}</code>\n"
            f"📊 Target Grup: {len(groups)} grup\n"
            f"⏱️ Delay: {msg['package']['delay']} detik\n\n"
            f"📄 <b>Preview:</b>\n<code>{preview}</code>\n\n"
            f"Yakin ingin memulai?"
        )
        
        from utils.keyboards import confirm_broadcast
        await callback.edit_message_text(text, reply_markup=confirm_broadcast(len(groups)))
    else:
        await callback.answer(msg, show_alert=True)

# ========== MAIN ==========

async def main():
    """Main function"""
    await db.init()
    await app.start()
    logger.info("Auto Sebar Bot started!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
