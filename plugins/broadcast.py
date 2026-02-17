import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import (
    FloodWait, UserBannedInChannel, ChatWriteForbidden, 
    PeerIdInvalid, ChannelInvalid, SlowmodeWait
)

from config import Config, Messages
from database import db
from utils.keyboards import broadcast_options, confirm_broadcast

logger = logging.getLogger(__name__)

class BroadcastManager:
    def __init__(self, client: Client):
        self.client = client
        self.active_broadcasts = {}
    
    async def start_broadcast(self, user_id: int, template_id: int = None, 
                             skip_confirmation: bool = False):
        """Memulai broadcast ke semua grup user"""
        
        user = await db.get_user(user_id)
        if not user:
            return False, "User tidak ditemukan"
        
        # Cek expiry
        expiry = datetime.fromisoformat(user['expiry_date'])
        if datetime.now() > expiry:
            return False, "❌ Masa aktif Anda telah habis. Silakan perpanjang di Toko."
        
        # Cek auto_promo
        if not user['auto_promo']:
            return False, "⚠️ Auto Promosi belum diaktifkan. Aktifkan di Panel Kontrol."
        
        # Get template
        if template_id:
            templates = await db.get_templates(user_id)
            template = next((t for t in templates if t['id'] == template_id), None)
        else:
            template = await db.get_default_template(user_id)
        
        if not template:
            return False, "⚠️ Belum ada template pesan. Buat di menu 'Atur Pesan'."
        
        # Get groups
        groups = await db.get_user_groups(user_id, status='active')
        if not groups:
            return False, "⚠️ Belum ada grup aktif. Tambahkan grup di menu 'Atur Grup'."
        
        # Cek limit paket
        package = Config.PACKAGES.get(user['package'], Config.PACKAGES['FREE'])
        if len(groups) > package['max_groups']:
            groups = groups[:package['max_groups']]
        
        if not skip_confirmation:
            return True, {
                'template': template,
                'groups': groups,
                'package': package
            }
        
        # Mulai broadcast
        await self._execute_broadcast(user_id, template, groups, package['delay'])
        return True, "Broadcast dimulai"
    
    async def _execute_broadcast(self, user_id: int, template: dict, 
                                groups: list, delay: int):
        """Eksekusi broadcast dengan tracking"""
        
        self.active_broadcasts[user_id] = {
            'status': 'running',
            'total': len(groups),
            'success': 0,
            'failed': 0,
            'current': 0,
            'start_time': datetime.now()
        }
        
        # Kirim status awal
        status_msg = await self.client.send_message(
            user_id,
            f"🚀 <b>Memulai Broadcast...</b>\n"
            f"📊 Total Grup: {len(groups)}\n"
            f"⏱️ Delay: {delay} detik\n"
            f"📝 Template: {template['name']}"
        )
        
        for i, group in enumerate(groups, 1):
            if user_id not in self.active_broadcasts:
                break  # Dibatalkan
            
            self.active_broadcasts[user_id]['current'] = i
            
            try:
                # Kirim pesan sesuai tipe
                if template['media_type'] == 'photo':
                    await self.client.send_photo(
                        chat_id=group['group_id'],
                        photo=template['media_file_id'],
                        caption=template['message_text'],
                        parse_mode='html'
                    )
                elif template['media_type'] == 'video':
                    await self.client.send_video(
                        chat_id=group['group_id'],
                        video=template['media_file_id'],
                        caption=template['message_text'],
                        parse_mode='html'
                    )
                elif template['media_type'] == 'document':
                    await self.client.send_document(
                        chat_id=group['group_id'],
                        document=template['media_file_id'],
                        caption=template['message_text'],
                        parse_mode='html'
                    )
                else:
                    await self.client.send_message(
                        chat_id=group['group_id'],
                        text=template['message_text'],
                        parse_mode='html',
                        disable_web_page_preview=False
                    )
                
                # Sukses
                self.active_broadcasts[user_id]['success'] += 1
                await db.log_broadcast(user_id, template['id'], group['group_id'], 'success')
                await db.update_group_status(group['group_id'], 'active')
                
                # Update status setiap 5 grup
                if i % 5 == 0 or i == len(groups):
                    await self._update_status(status_msg, user_id)
                
            except FloodWait as e:
                logger.warning(f"FloodWait: {e.value}s")
                await asyncio.sleep(e.value)
                # Retry
                continue
                
            except (UserBannedInChannel, ChatWriteForbidden) as e:
                self.active_broadcasts[user_id]['failed'] += 1
                await db.log_broadcast(user_id, template['id'], group['group_id'], 'failed', str(e))
                await db.update_group_status(group['group_id'], 'banned', str(e))
                
            except (PeerIdInvalid, ChannelInvalid) as e:
                self.active_broadcasts[user_id]['failed'] += 1
                await db.log_broadcast(user_id, template['id'], group['group_id'], 'failed', str(e))
                await db.update_group_status(group['group_id'], 'invalid', str(e))
                
            except Exception as e:
                self.active_broadcasts[user_id]['failed'] += 1
                await db.log_broadcast(user_id, template['id'], group['group_id'], 'failed', str(e))
                logger.error(f"Error broadcasting to {group['group_id']}: {e}")
            
            # Delay antar pesan
            await asyncio.sleep(delay)
        
        # Selesai
        await self._finish_broadcast(user_id, status_msg)
    
    async def _update_status(self, message: Message, user_id: int):
        """Update status broadcast"""
        data = self.active_broadcasts.get(user_id, {})
        
        text = (
            f"🚀 <b>Broadcast Berjalan...</b>\n\n"
            f"📊 Progress: {data['current']}/{data['total']}\n"
            f"✅ Berhasil: {data['success']}\n"
            f"❌ Gagal: {data['failed']}\n"
            f"⏳ Sisa: {data['total'] - data['current']}\n\n"
            f"⏱️ <i>Update otomatis...</i>"
        )
        
        try:
            await message.edit_text(text)
        except:
            pass
    
    async def _finish_broadcast(self, user_id: int, status_msg: Message):
        """Selesai broadcast"""
        data = self.active_broadcasts.get(user_id, {})
        duration = (datetime.now() - data['start_time']).total_seconds()
        
        text = (
            f"✅ <b>Broadcast Selesai!</b>\n\n"
            f"📊 Total Grup: {data['total']}\n"
            f"✅ Berhasil: {data['success']}\n"
            f"❌ Gagal: {data['failed']}\n"
            f"⏱️ Durasi: {duration/60:.1f} menit\n\n"
            f"🏠 Kembali ke Panel Kontrol?"
        )
        
        from utils.keyboards import control_panel
        await status_msg.edit_text(
            text,
            reply_markup=control_panel()
        )
        
        del self.active_broadcasts[user_id]
    
    def cancel_broadcast(self, user_id: int):
        """Batalkan broadcast"""
        if user_id in self.active_broadcasts:
            self.active_broadcasts[user_id]['status'] = 'cancelled'
            return True
        return False

# Handler untuk callback
async def broadcast_callback_handler(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    
    if data == "start_broadcast":
        bm = BroadcastManager(client)
        result, msg = await bm.start_broadcast(user_id)
        
        if result and isinstance(msg, dict):
            # Tampilkan konfirmasi
            template = msg['template']
            groups = msg['groups']
            
            preview = template['message_text'][:200] + "..." if len(template['message_text']) > 200 else template['message_text']
            
            text = (
                f"📋 <b>Konfirmasi Broadcast</b>\n\n"
                f"📝 Template: <code>{template['name']}</code>\n"
                f"📊 Target Grup: {len(groups)} grup\n"
                f"⏱️ Delay: {msg['package']['delay']} detik\n\n"
                f"📄 <b>Preview Pesan:</b>\n"
                f"<code>{preview}</code>\n\n"
                f"Yakin ingin memulai broadcast?"
            )
            
            await callback.edit_message_text(
                text,
                reply_markup=confirm_broadcast(len(groups))
            )
        else:
            await callback.answer(msg, show_alert=True)
    
    elif data == "confirm_broadcast":
        await callback.edit_message_text("🚀 Memulai broadcast...")
        bm = BroadcastManager(client)
        await bm.start_broadcast(user_id, skip_confirmation=True)
    
    elif data == "cancel_broadcast":
        await callback.edit_message_text(
            "❌ Broadcast dibatalkan.",
            reply_markup=control_panel()
        )
