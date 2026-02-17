import functools
import logging
from pyrogram.types import Message, CallbackQuery
from config import Config

logger = logging.getLogger(__name__)

def admin_only(func):
    """Decorator untuk command khusus admin"""
    @functools.wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        user_id = update.from_user.id if isinstance(update, CallbackQuery) else update.from_user.id
        
        if user_id not in Config.ADMIN_IDS and user_id != Config.OWNER_ID:
            if isinstance(update, Message):
                await update.reply_text("⛔ Command ini hanya untuk admin!")
            elif isinstance(update, CallbackQuery):
                await update.answer("⛔ Admin only!", show_alert=True)
            return
        
        return await func(client, update, *args, **kwargs)
    return wrapper

def owner_only(func):
    """Decorator untuk command khusus owner"""
    @functools.wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        user_id = update.from_user.id if isinstance(update, CallbackQuery) else update.from_user.id
        
        if user_id != Config.OWNER_ID:
            if isinstance(update, Message):
                await update.reply_text("⛔ Command ini hanya untuk owner!")
            elif isinstance(update, CallbackQuery):
                await update.answer("⛔ Owner only!", show_alert=True)
            return
        
        return await func(client, update, *args, **kwargs)
    return wrapper

def private_chat_only(func):
    """Decorator untuk command hanya di private chat"""
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if message.chat.type != "private":
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def group_chat_only(func):
    """Decorator untuk command hanya di grup"""
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if message.chat.type == "private":
            await message.reply_text("⚠️ Command ini hanya bisa digunakan di grup!")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper

def log_command(func):
    """Decorator untuk logging command"""
    @functools.wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        user = update.from_user if isinstance(update, Message) else update.from_user
        command = update.text if isinstance(update, Message) else update.data
        
        logger.info(f"Command '{command}' used by {user.id} (@{user.username})")
        
        try:
            return await func(client, update, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper

def rate_limit(calls: int = 5, period: int = 60):
    """Decorator untuk rate limiting"""
    users = {}
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            user_id = update.from_user.id if isinstance(update, CallbackQuery) else update.from_user.id
            now = __import__('time').time()
            
            if user_id not in users:
                users[user_id] = []
            
            # Hapus calls yang sudah expired
            users[user_id] = [t for t in users[user_id] if now - t < period]
            
            if len(users[user_id]) >= calls:
                remaining = period - (now - users[user_id][0])
                msg = f"⏳ Rate limit! Coba lagi dalam {int(remaining)} detik."
                
                if isinstance(update, Message):
                    await update.reply_text(msg)
                elif isinstance(update, CallbackQuery):
                    await update.answer(msg, show_alert=True)
                return
            
            users[user_id].append(now)
            return await func(client, update, *args, **kwargs)
        return wrapper
    return decorator

def require_active_package(func):
    """Decorator untuk cek apakah user punya paket aktif"""
    @functools.wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        from database import db
        from datetime import datetime
        
        user_id = update.from_user.id if isinstance(update, CallbackQuery) else update.from_user.id
        user = await db.get_user(user_id)
        
        if not user:
            msg = "❌ Anda belum terdaftar. Ketik /start"
            if isinstance(update, Message):
                await update.reply_text(msg)
            elif isinstance(update, CallbackQuery):
                await update.answer(msg, show_alert=True)
            return
        
        expiry = datetime.fromisoformat(user['expiry_date'])
        if datetime.now() > expiry:
            msg = "❌ Masa aktif habis! Perpanjang di /store"
            if isinstance(update, Message):
                await update.reply_text(msg)
            elif isinstance(update, CallbackQuery):
                await update.answer(msg, show_alert=True)
            return
        
        return await func(client, update, *args, **kwargs)
    return wrapper
