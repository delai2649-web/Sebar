import os
import logging
import asyncio
from pyrogram import Client, idle, filters
from pyrogram.types import Message, CallbackQuery

from config import Config, Messages
from database import db
from utils.keyboards import main_menu, control_panel, group_menu, store_menu
from plugins.broadcast import BroadcastManager, broadcast_callback_handler
from plugins.groups import GroupManager, group_callback_handler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('downloads', exist_ok=True)
os.makedirs('userbot_session', exist_ok=True)

class AutoSebarBot:
    def __init__(self):
        self.client = Client(
            Config.SESSION_NAME,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workdir=".",
            parse_mode="html"
        )
        self.broadcast_manager = BroadcastManager(self.client)
        self.group_manager = GroupManager(self.client)
        self.setup_handlers()
    
    def setup_handlers(self):
        # Command handlers
        @self.client.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            user = message.from_user
            
            # Add user to database
            await db.add_user(
                user_id=user.id,
                username=user.username,
                full_name=user.first_name + (" " + user.last_name if user.last_name else ""),
                phone=None
            )
            
            await message.reply_text(
                Messages.WELCOME.format(name=user.first_name),
                reply_markup=main_menu(),
                disable_web_page_preview=False
            )
        
        @self.client.on_message(filters.command("panel") & filters.private)
        async def panel_handler(client: Client, message: Message):
            await self.show_control_panel(message)
        
        # Callback handlers
        @self.client.on_callback_query()
        async def callback_handler(client: Client, callback: CallbackQuery):
            data = callback.data
            user_id = callback.from_user.id
            
            if data == "main_menu":
                await callback.edit_message_text(
                    Messages.WELCOME.format(name=callback.from_user.first_name),
                    reply_markup=main_menu(),
                    disable_web_page_preview=False
                )
            
            elif data == "panel_control":
                await self.show_control_panel(callback.message, edit=True)
            
            elif data == "store":
                await callback.edit_message_text(
                    Messages.STORE_MENU,
                    reply_markup=store_menu(),
                    disable_web_page_preview=False
                )
            
            elif data.startswith("package_"):
                package = data.replace("package_", "")
                await self.handle_package_selection(callback, package)
            
            elif data in ["set_groups", "add_group", "list_groups", "join_group", "scan_groups"]:
                await group_callback_handler(client, callback)
            
            elif data in ["start_broadcast", "confirm_broadcast", "cancel_broadcast"]:
                await broadcast_callback_handler(client, callback)
            
            elif data == "set_message":
                await callback.edit_message_text(
                    "✍️ <b>Atur Pesan Broadcast</b>\n\n"
                    "Kirimkan pesan yang ingin disimpan sebagai template.\n"
                    "Bisa berupa teks, foto, video, atau dokumen dengan caption.\n\n"
                    "Untuk tombol inline, gunakan format:\n"
                    "<code>[Button Text](https://t.me/link)</code>",
                    reply_markup=main_menu()
                )
            
            elif data == "toggle_auto":
                new_status = await db.toggle_auto_promo(user_id)
                status_text = "✅ AKTIF" if new_status else "❌ NONAKTIF"
                await callback.answer(f"Auto Promosi: {status_text}", show_alert=True)
                await self.show_control_panel(callback.message, edit=True)
            
            elif data == "try_free":
                await callback.edit_message_text(
                    "🎁 <b>COBA GRATIS</b>\n\n"
                    "✅ Anda mendapatkan paket FREE selama 1 hari!\n"
                    "• Maksimal 5 grup\n"
                    "• Delay 120 detik\n"
                    "• Fitur dasar broadcast\n\n"
                    "Klik '🚀 Buat Userbot' untuk mulai!",
                    reply_markup=main_menu()
                )
            
            else:
                await callback.answer("Fitur dalam pengembangan!", show_alert=True)
        
        # Message handlers untuk input
        @self.client.on_message(filters.private & filters.text)
        async def text_handler(client: Client, message: Message):
            # Handle link grup
            if message.text.startswith(('https://t.me/', 't.me/')):
                gm = GroupManager(client)
                success, msg = await gm.join_group_via_link(message.from_user.id, message.text)
                await message.reply_text(msg)
            
            # Handle template message
            elif message.text and not message.text.startswith('/'):
                # Simpan sebagai template
                template_id = await db.save_template(
                    user_id=message.from_user.id,
                    name=f"Template {datetime.now().strftime('%H:%M')}",
                    message_text=message.text,
                    is_default=True
                )
                await message.reply_text(
                    f"✅ Template disimpan!\n\n"
                    f"Preview:\n<code>{message.text[:100]}...</code>",
                    reply_markup=control_panel()
                )
        
        @self.client.on_message(filters.private & filters.photo)
        async def photo_handler(client: Client, message: Message):
            template_id = await db.save_template(
                user_id=message.from_user.id,
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
        
        @self.client.on_message(filters.private & filters.video)
        async def video_handler(client: Client, message: Message):
            template_id = await db.save_template(
                user_id=message.from_user.id,
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
    
    async def show_control_panel(self, message, edit=False):
        user_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
        user = await db.get_user(user_id)
        
        if not user:
            await message.reply_text("Silakan /start terlebih dahulu.")
            return
        
        group_count = await db.get_group_count(user_id)
        package = Config.PACKAGES.get(user['package'], Config.PACKAGES['FREE'])
        
        text = Messages.PANEL_CONTROL.format(
            auto_status="✅ Aktif" if user['auto_promo'] else "❌ Nonaktif",
            pm_status="✅ Aktif" if user['pm_permit'] else "❌ Nonaktif",
            user_id=user_id,
            package=user['package'],
            expiry=user['expiry_date'],
            total_groups=group_count,
            max_groups=package['max_groups']
        )
        
        # Tambahkan tombol toggle
        keyboard = control_panel(user['auto_promo'], user['pm_permit'])
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
    
    async def handle_package_selection(self, callback: CallbackQuery, package: str):
        user_id = callback.from_user.id
        pkg = Config.PACKAGES.get(package)
        
        if not pkg:
            await callback.answer("Paket tidak valid!", show_alert=True)
            return
        
        if package == "FREE":
            # Langsung aktifkan FREE
            await db.extend_package(user_id, "FREE", pkg['days'])
            await callback.edit_message_text(
                f"✅ Paket FREE diaktifkan!\n\n"
                f"📅 Masa aktif: {pkg['days']} hari\n"
                f"👥 Max grup: {pkg['max_groups']}\n"
                f"⏱️ Delay: {pkg['delay']} detik",
                reply_markup=control_panel()
            )
        else:
            # Tampilkan instruksi pembayaran
            text = (
                f"💳 <b>Pembayaran Paket {package}</b>\n\n"
                f"Harga: Rp {pkg['price']:,}\n"
                f"Masa aktif: {pkg['days']} hari\n"
                f"Max grup: {pkg['max_groups']}\n"
                f"Delay: {pkg['delay']} detik\n\n"
                f"Silakan transfer ke:\n"
            )
            
            for method, number in Config.PAYMENT_CHANNELS.items():
                if number:
                    text += f"• {method.upper()}: <code>{number}</code>\n"
            
            text += f"\nKirim bukti pembayaran ke admin @admin"
            
            await callback.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="store")
                ]])
            )
    
    async def run(self):
        await db.init()
        await self.client.start()
        logger.info("Auto Sebar Bot started!")
        await idle()
        await self.client.stop()

if __name__ == "__main__":
    from datetime import datetime
    bot = AutoSebarBot()
    asyncio.run(bot.run())
