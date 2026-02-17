import os
import sys
import logging
import asyncio
import re
from datetime import datetime

from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, Messages
from database import db
from utils.keyboards import (
    main_menu, subscription_menu, package_menu, basic_type_menu, 
    confirm_payment_menu, cancel_button, control_panel
)
from utils.helpers import get_expiry_text, format_number
from plugins.userbot_generator import userbot_gen
from plugins.broadcast import BroadcastManager

# Setup logging
os.makedirs('logs', exist_ok=True)
os.makedirs(Config.USERBOT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Client Bot Utama
app = Client(
    "sebar_main_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# State management
user_states = {}

# ========== COMMAND HANDLERS ==========

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    """Handler /start"""
    user = message.from_user
    
    # Add/update user
    await db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.first_name + (" " + user.last_name if user.last_name else "")
    )
    
    # Cek apakah sudah punya userbot
    userbot = await db.get_userbot(user.id)
    has_userbot = userbot is not None
    
    await message.reply_text(
        Messages.WELCOME.format(name=user.first_name),
        reply_markup=main_menu(has_userbot)
    )

@app.on_message(filters.command("cancel") & filters.private)
async def cancel_handler(client: Client, message: Message):
    """Handler /cancel"""
    user_id = message.from_user.id
    
    # Cancel userbot creation
    await userbot_gen.cancel_creation(user_id)
    
    # Clear state
    if user_id in user_states:
        del user_states[user_id]
    
    await message.reply_text(
        "❌ Proses dibatalkan.",
        reply_markup=main_menu()
    )

@app.on_message(filters.command("panel") & filters.private)
async def panel_handler(client: Client, message: Message):
    """Handler /panel"""
    await show_control_panel(message)

# ========== CALLBACK HANDLERS ==========

@app.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    """Handler semua callback"""
    data = callback.data
    user_id = callback.from_user.id
    
    try:
        # Main Menu
        if data == "main_menu":
            userbot = await db.get_userbot(user_id)
            await callback.edit_message_text(
                Messages.WELCOME.format(name=callback.from_user.first_name),
                reply_markup=main_menu(userbot is not None)
            )
        
        # Create Userbot Flow
        elif data == "create_userbot":
            # Cek apakah sudah punya userbot aktif
            userbot = await db.get_userbot(user_id)
            if userbot:
                await callback.answer("Anda sudah memiliki userbot aktif!", show_alert=True)
                return
            
            # Tampilkan menu langganan
            await callback.edit_message_text(
                Messages.NEED_SUBSCRIPTION,
                reply_markup=subscription_menu()
            )
        
        elif data == "buy_userbot":
            await callback.edit_message_text(
                "🔔 <b>Pilih Tipe Layanan</b>\n\n"
                "Silakan pilih paket yang sesuai dengan kebutuhan Anda:",
                reply_markup=package_menu()
            )
        
        elif data == "package_basic":
            await callback.edit_message_text(
                "⭐ <b>PILIH TIPE LAYANAN BASIC</b> ⭐\n\n"
                "Silakan pilih jenis layanan yang Anda inginkan.\n"
                "Perbedaan utama terletak pada garansi dan backup.",
                reply_markup=basic_type_menu()
            )
        
        elif data in ["basic_hemat", "basic_sultan"]:
            package = Config.PACKAGES.get(data)
            price = package['price']
            
            # Simpan state
            user_states[user_id] = {
                'step': 'waiting_phone',
                'package_type': data,
                'price': price,
                'duration': 1
            }
            
            await callback.edit_message_text(
                Messages.CREATE_USERBOT,
                reply_markup=cancel_button()
            )
        
        elif data == "cancel_creation":
            if user_id in user_states:
                del user_states[user_id]
            await userbot_gen.cancel_creation(user_id)
            
            await callback.edit_message_text(
                Messages.WELCOME.format(name=callback.from_user.first_name),
                reply_markup=main_menu()
            )
        
        elif data == "cancel":
            await callback.edit_message_text(
                Messages.WELCOME.format(name=callback.from_user.first_name),
                reply_markup=main_menu()
            )
        
        # Panel Control
        elif data == "panel_control":
            await show_control_panel(callback.message, edit=True)
        
        elif data == "toggle_auto":
            userbot = await db.get_userbot(user_id)
            if not userbot:
                await callback.answer("Anda belum memiliki userbot!", show_alert=True)
                return
            
            new_status = await db.toggle_auto_promo(userbot['id'])
            status_text = "AKTIF ✅" if new_status else "NONAKTIF ❌"
            await callback.answer(f"Auto Promosi: {status_text}", show_alert=True)
            await show_control_panel(callback.message, edit=True)
        
        # Store
        elif data == "store":
            await callback.edit_message_text(
                "🛍️ <b>MENU STORE & LAYANAN</b>\n\n"
                "Silakan pilih kategori produk:",
                reply_markup=subscription_menu()
            )
        
        # Fitur lainnya
        elif data == "guide":
            await callback.edit_message_text(
                "📚 <b>Panduan Penggunaan</b>\n\n"
                "1. Beli/Buat Userbot\n"
                "2. Login dengan nomor telepon\n"
                "3. Masukkan kode OTP\n"
                "4. Atur pesan broadcast\n"
                "5. Tambahkan grup target\n"
                "6. Aktifkan Auto Promosi\n\n"
                "Bot akan otomatis mengirim pesan ke semua grup!",
                reply_markup=main_menu()
            )
        
        elif data == "features":
            await callback.edit_message_text(
                "💡 <b>Fitur Unggulan</b>\n\n"
                "✅ Auto Broadcast 24/7\n"
                "✅ Multi Media (Teks, Foto, Video)\n"
                "✅ Sistem Delay Anti-Ban\n"
                "✅ Manajemen Grup Otomatis\n"
                "✅ Token Garansi & Backup\n"
                "✅ Pembayaran QRIS Otomatis\n"
                "✅ Support 2FA\n"
                "✅ Panel Kontrol Real-time",
                reply_markup=main_menu()
            )
        
        elif data == "try_free":
            await callback.edit_message_text(
                "🎁 <b>COBA GRATIS</b>\n\n"
                "✅ Paket FREE aktif 1 hari!\n"
                "• Max 5 grup\n"
                "• Delay 120 detik\n"
                "• Fitur dasar\n\n"
                "Klik 🚀 Buat Userbot untuk mulai!",
                reply_markup=main_menu()
            )
        
        else:
            await callback.answer("Fitur dalam pengembangan!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer("Terjadi kesalahan!", show_alert=True)

# ========== MESSAGE HANDLERS ==========

@app.on_message(filters.private & filters.text & ~filters.command(["start", "cancel", "panel", "help"]))
async def text_handler(client: Client, message: Message):
    """Handle text input (OTP, 2FA, Phone, dll)"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Cek state user
    state = user_states.get(user_id)
    otp_state = await db.get_otp_state(user_id)
    
    # Step 1: Input nomor telepon
    if state and state.get('step') == 'waiting_phone':
        # Validasi nomor telepon
        if not re.match(r'^\+[1-9]\d{7,14}$', text):
            await message.reply_text(
                "❌ Format nomor salah!\n\n"
                "Gunakan format internasional:\n"
                "<code>+628xxxxxxxxxx</code>",
                reply_markup=cancel_button()
            )
            return
        
        # Mulai proses pembuatan userbot
        package_type = state['package_type']
        
        await message.reply_text("⏳ Sedang mengirim kode OTP...")
        
        success, result = await userbot_gen.start_creation(user_id, text, package_type)
        
        if success:
            user_states[user_id]['step'] = 'waiting_otp'
            await message.reply_text(
                Messages.OTP_SENT,
                reply_markup=cancel_button()
            )
        else:
            await message.reply_text(
                f"❌ {result}\n\nCoba lagi atau ketik /cancel",
                reply_markup=cancel_button()
            )
    
    # Step 2: Input OTP
    elif otp_state and otp_state['step'] == 'otp':
        # Validasi format OTP (5 digit dengan spasi atau tidak)
        otp_clean = text.replace(' ', '')
        if not otp_clean.isdigit() or len(otp_clean) < 4:
            await message.reply_text(
                "❌ Format kode salah!\n\n"
                "Kirim dengan format: <code>1 2 3 4 5</code> atau <code>12345</code>",
                reply_markup=cancel_button()
            )
            return
        
        await message.reply_text("⏳ Memverifikasi kode...")
        
        success, result = await userbot_gen.verify_otp(user_id, otp_clean)
        
        if success:
            if result == "2FA_NEEDED":
                await db.set_otp_state(
                    user_id=user_id,
                    step='2fa',
                    phone=otp_state['phone'],
                    phone_code_hash=otp_state['phone_code_hash'],
                    session_name=otp_state['session_name'],
                    package_type=otp_state['package_type']
                )
                await message.reply_text(
                    Messages.ENTER_2FA,
                    reply_markup=cancel_button()
                )
            else:
                # Berhasil dibuat
                await message.reply_text(
                    Messages.USERBOT_CREATED.format(
                        name=result['name'],
                        user_id=result['user_id'],
                        token=result['token']
                    ),
                    reply_markup=control_panel()
                )
                if user_id in user_states:
                    del user_states[user_id]
        else:
            await message.reply_text(
                f"❌ {result}\n\nCoba lagi atau ketik /cancel",
                reply_markup=cancel_button()
            )
    
    # Step 3: Input 2FA Password
    elif otp_state and otp_state['step'] == '2fa':
        await message.reply_text("⏳ Memverifikasi password...")
        
        success, result = await userbot_gen.verify_2fa(user_id, text)
        
        if success:
            await message.reply_text(
                Messages.USERBOT_CREATED.format(
                    name=result['name'],
                    user_id=result['user_id'],
                    token=result['token']
                ),
                reply_markup=control_panel()
            )
            if user_id in user_states:
                del user_states[user_id]
        else:
            await message.reply_text(
                f"❌ {result}\n\nCoba lagi atau ketik /cancel",
                reply_markup=cancel_button()
            )
    
    # Default: Template message
    else:
        # Simpan sebagai template broadcast
        template_id = await db.save_template(
            user_id=user_id,
            name=f"Template {datetime.now().strftime('%H:%M')}",
            message_text=text,
            is_default=True
        )
        
        await message.reply_text(
            "✅ Template disimpan!\n\n"
            f"Preview:\n<code>{text[:100]}{'...' if len(text) > 100 else ''}</code>",
            reply_markup=control_panel()
        )

@app.on_message(filters.private & filters.photo)
async def photo_handler(client: Client, message: Message):
    """Handle foto template"""
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
    """Handle video template"""
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
    userbot = await db.get_userbot(user_id)
    
    if not userbot:
        text = "❌ Anda belum memiliki userbot!\n\nKetik /start untuk membuat."
        if edit:
            await message.edit_text(text, reply_markup=main_menu())
        else:
            await message.reply_text(text, reply_markup=main_menu())
        return
    
    package = Config.PACKAGES.get(userbot['package_type'], {})
    
    text = Messages.PANEL_CONTROL.format(
        auto_status="✅ Aktif" if userbot['auto_promo'] else "❌ Nonaktif",
        pm_status="✅ Aktif" if userbot['pm_permit'] else "❌ Nonaktif",
        user_id=userbot['user_id'],
        package=package.get('name', userbot['package_type']),
        expiry=get_expiry_text(userbot['expiry_date'])
    )
    
    keyboard = control_panel(userbot['auto_promo'], userbot['pm_permit'])
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.reply_text(text, reply_markup=keyboard)

# ========== MAIN ==========

async def main():
    """Main function"""
    await db.init()
    await app.start()
    logger.info("🚀 Sebar Bot Started!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
