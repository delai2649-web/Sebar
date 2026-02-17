import asyncio
import logging
from datetime import datetime
from pyrogram import Client
from pyrogram.errors import FloodWait, UserBannedInChannel, ChatWriteForbidden

from database import db

logger = logging.getLogger(__name__)

class BroadcastManager:
    def __init__(self, client: Client):
        self.client = client
        self.active_broadcasts = {}
    
    async def start_broadcast(self, user_id: int, userbot_id: int = None):
        """Mulai broadcast"""
        # Get userbot
        if not userbot_id:
            userbot = await db.get_userbot(user_id)
            if not userbot:
                return False, "Userbot tidak ditemukan!"
            userbot_id = userbot['id']
        else:
            # Get dari ID
            async with db.get_connection() as conn:
                row = await conn.fetchone(
                    'SELECT * FROM userbots WHERE id = ?', (userbot_id,)
                )
                userbot = dict(row) if row else None
        
        if not userbot or not userbot['is_active']:
            return False, "Userbot tidak aktif!"
        
        # Cek expiry
        expiry = datetime.fromisoformat(userbot['expiry_date'])
        if datetime.now() > expiry:
            return False, "Masa aktif userbot telah habis!"
        
        # Cek auto_promo
        if not userbot['auto_promo']:
            return False, "Auto Promosi belum diaktifkan!"
        
        # Get template
        template = await db.get_default_template(user_id)
        if not template:
            return False, "Belum ada template pesan!"
        
        # Get groups
        groups = await db.get_user_groups(userbot_id)
        if not groups:
            return False, "Belum ada grup target!"
        
        # Jalankan broadcast
        asyncio.create_task(self._execute_broadcast(user_id, userbot_id, template, groups))
        
        return True, f"Broadcast dimulai ke {len(groups)} grup"
    
    async def _execute_broadcast(self, owner_id: int, userbot_id: int, template: dict, groups: list):
        """Eksekusi broadcast"""
        # Load userbot client
        session_path = f"userbots/{template.get('session_name', 'unknown')}"
        
        try:
            userbot_client = Client(
                session_path,
                api_id=self.client.api_id,
                api_hash=self.client.api_hash
            )
            await userbot_client.start()
            
            success = 0
            failed = 0
            
            for group in groups:
                try:
                    if template['media_type'] == 'photo':
                        await userbot_client.send_photo(
                            group['group_id'],
                            photo=template['media_file_id'],
                            caption=template['message_text']
                        )
                    elif template['media_type'] == 'video':
                        await userbot_client.send_video(
                            group['group_id'],
                            video=template['media_file_id'],
                            caption=template['message_text']
                        )
                    else:
                        await userbot_client.send_message(
                            group['group_id'],
                            text=template['message_text']
                        )
                    
                    success += 1
                    await asyncio.sleep(30)  # Delay default
                    
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception as e:
                    failed += 1
                    logger.error(f"Error sending to {group['group_id']}: {e}")
            
            await userbot_client.stop()
            
            # Notify owner
            await self.client.send_message(
                owner_id,
                f"✅ Broadcast selesai!\n\n"
                f"✅ Berhasil: {success}\n"
                f"❌ Gagal: {failed}"
            )
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await self.client.send_message(
                owner_id,
                f"❌ Broadcast error: {str(e)}"
            )
