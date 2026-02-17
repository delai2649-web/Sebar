import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import InviteHashExpired, InviteHashInvalid, UserAlreadyParticipant

from database import db
from config import Config

class GroupManager:
    def __init__(self, client: Client):
        self.client = client
    
    async def join_group_via_link(self, user_id: int, link: str):
        """Join grup menggunakan link invite"""
        try:
            # Extract hash dari link
            match = re.search(r't\.me/\+?(\w+)', link) or re.search(r't\.me/joinchat/(\w+)', link)
            if not match:
                return False, "Link tidak valid"
            
            invite_hash = match.group(1)
            
            # Join grup
            chat = await self.client.join_chat(invite_hash)
            
            # Simpan ke database
            await db.add_group(
                user_id=user_id,
                group_id=chat.id,
                group_title=chat.title,
                group_username=chat.username,
                group_link=link,
                member_count=chat.members_count if hasattr(chat, 'members_count') else 0
            )
            
            return True, f"✅ Berhasil bergabung ke grup: {chat.title}"
            
        except UserAlreadyParticipant:
            return False, "⚠️ Anda sudah menjadi anggota grup ini"
        except (InviteHashExpired, InviteHashInvalid):
            return False, "❌ Link invite tidak valid atau sudah expired"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    async def leave_group(self, user_id: int, group_id: int):
        """Keluar dari grup"""
        try:
            await self.client.leave_chat(group_id)
            await db.update_group_status(group_id, 'left')
            return True, "✅ Berhasil keluar dari grup"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    async def scan_groups(self, user_id: int):
        """Scan semua grup yang dimiliki user"""
        try:
            dialogs = []
            async for dialog in self.client.get_dialogs():
                if dialog.chat.type in ['group', 'supergroup']:
                    # Cek apakah bot adalah member
                    try:
                        member = await self.client.get_chat_member(dialog.chat.id, "me")
                        if member:
                            dialogs.append({
                                'id': dialog.chat.id,
                                'title': dialog.chat.title,
                                'username': dialog.chat.username,
                                'members': dialog.chat.members_count if hasattr(dialog.chat, 'members_count') else 0
                            })
                    except:
                        continue
            
            # Simpan ke database
            for chat in dialogs:
                await db.add_group(
                    user_id=user_id,
                    group_id=chat['id'],
                    group_title=chat['title'],
                    group_username=chat['username'],
                    member_count=chat['members']
                )
            
            return True, f"✅ Berhasil scan {len(dialogs)} grup"
            
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    async def get_group_stats(self, user_id: int):
        """Get statistik grup"""
        groups = await db.get_user_groups(user_id)
        
        total = len(groups)
        active = len([g for g in groups if g['status'] == 'active'])
        banned = len([g for g in groups if g['status'] == 'banned'])
        pending = len([g for g in groups if g['status'] == 'pending'])
        
        return {
            'total': total,
            'active': active,
            'banned': banned,
            'pending': pending
        }

# Handler callback
async def group_callback_handler(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    gm = GroupManager(client)
    
    if data == "set_groups":
        stats = await gm.get_group_stats(user_id)
        user = await db.get_user(user_id)
        package = Config.PACKAGES.get(user['package'], Config.PACKAGES['FREE'])
        
        text = (
            f"🎯 <b>Pengaturan Target Grup</b>\n\n"
            f"📊 <b>Statistik Grup:</b>\n"
            f"• Total: {stats['total']}/{package['max_groups']}\n"
            f"• Aktif: {stats['active']}\n"
            f"• Diblokir: {stats['banned']}\n"
            f"• Pending: {stats['pending']}\n\n"
            f"💡 Pilih opsi di bawah:"
        )
        
        from utils.keyboards import group_menu
        await callback.edit_message_text(text, reply_markup=group_menu())
    
    elif data == "add_group":
        await callback.edit_message_text(
            "📎 <b>Tambah Grup</b>\n\n"
            "Kirim link invite grup (https://t.me/+xxxxx) atau forward pesan dari grup.\n\n"
            "⏳ Menunggu input...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Batal", callback_data="set_groups")
            ]])
        )
        # Set state untuk menunggu input
    
    elif data == "list_groups":
        groups = await db.get_user_groups(user_id)
        if not groups:
            text = "📭 Belum ada grup. Tambahkan grup terlebih dahulu."
        else:
            text = "📚 <b>Daftar Grup:</b>\n\n"
            for i, g in enumerate(groups[:20], 1):  # Limit 20
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
    
    elif data == "join_group":
        await callback.edit_message_text(
            "🚀 <b>Gabung Grup Otomatis</b>\n\n"
            "Fitur ini akan mencoba bergabung ke grup menggunakan link yang Anda sediakan.\n\n"
            "Kirim link grup (satu per satu atau multiple pisahkan dengan enter):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Batal", callback_data="set_groups")
            ]])
        )
    
    elif data == "scan_groups":
        await callback.edit_message_text("⏳ Scanning grup...")
        success, msg = await gm.scan_groups(user_id)
        await callback.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="set_groups")
            ]])
        )
