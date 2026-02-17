import os
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid
)

from config import Config
from database import db

class UserbotGenerator:
    def __init__(self):
        self.pending_clients = {}  # Simpan client sementara
    
    async def start_creation(self, user_id: int, phone: str, package_type: str) -> tuple:
        """Mulai proses pembuatan userbot"""
        session_name = f"userbot_{user_id}_{int(asyncio.get_event_loop().time())}"
        session_path = os.path.join(Config.USERBOT_DIR, session_name)
        
        # Buat client baru
        client = Client(
            session_path,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            phone_number=phone
        )
        
        try:
            await client.connect()
            sent_code = await client.send_code(phone)
            
            # Simpan client sementara
            self.pending_clients[user_id] = {
                'client': client,
                'phone': phone,
                'phone_code_hash': sent_code.phone_code_hash,
                'session_name': session_name,
                'package_type': package_type
            }
            
            # Simpan state ke database
            await db.set_otp_state(
                user_id=user_id,
                phone=phone,
                phone_code_hash=sent_code.phone_code_hash,
                session_name=session_name,
                package_type=package_type,
                step='otp'
            )
            
            return True, "OTP_SENT"
            
        except PhoneNumberInvalid:
            await client.disconnect()
            return False, "Nomor telepon tidak valid!"
        except Exception as e:
            await client.disconnect()
            return False, f"Error: {str(e)}"
    
    async def verify_otp(self, user_id: int, otp: str) -> tuple:
        """Verifikasi kode OTP"""
        state = await db.get_otp_state(user_id)
        if not state or state['step'] != 'otp':
            return False, "Sesi tidak ditemukan atau sudah expired!"
        
        pending = self.pending_clients.get(user_id)
        if not pending:
            return False, "Sesi tidak ditemukan!"
        
        client = pending['client']
        phone = pending['phone']
        phone_code_hash = pending['phone_code_hash']
        
        try:
            # Sign in dengan OTP
            await client.sign_in(phone, phone_code_hash, otp)
            
            # Berhasil tanpa 2FA
            return await self._finalize_userbot(user_id)
            
        except SessionPasswordNeeded:
            # Butuh 2FA
            await db.set_otp_state(
                user_id=user_id,
                phone=phone,
                phone_code_hash=phone_code_hash,
                session_name=pending['session_name'],
                package_type=pending['package_type'],
                step='2fa'
            )
            pending['step'] = '2fa'
            return True, "2FA_NEEDED"
            
        except PhoneCodeInvalid:
            return False, "Kode OTP salah!"
        except PhoneCodeExpired:
            return False, "Kode OTP sudah expired!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def verify_2fa(self, user_id: int, password: str) -> tuple:
        """Verifikasi 2FA password"""
        state = await db.get_otp_state(user_id)
        if not state or state['step'] != '2fa':
            return False, "Sesi tidak ditemukan!"
        
        pending = self.pending_clients.get(user_id)
        if not pending:
            return False, "Sesi tidak ditemukan!"
        
        client = pending['client']
        
        try:
            await client.check_password(password)
            return await self._finalize_userbot(user_id)
            
        except PasswordHashInvalid:
            return False, "Password salah!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def _finalize_userbot(self, user_id: int) -> tuple:
        """Selesaikan pembuatan userbot"""
        pending = self.pending_clients.get(user_id)
        if not pending:
            return False, "Sesi tidak ditemukan!"
        
        client = pending['client']
        
        # Get user info
        me = await client.get_me()
        
        # Get package duration
        package = Config.PACKAGES.get(pending['package_type'], {})
        duration = package.get('duration_days', 30)
        
        # Simpan ke database
        token = await db.create_userbot(
            owner_id=user_id,
            session_name=pending['session_name'],
            phone=pending['phone'],
            user_id=me.id,
            username=me.username or me.first_name,
            package_type=pending['package_type'],
            duration_days=duration
        )
        
        # Disconnect client (akan dijalankan lagi nanti)
        await client.disconnect()
        
        # Clear state
        await db.clear_otp_state(user_id)
        del self.pending_clients[user_id]
        
        return True, {
            'name': me.first_name,
            'user_id': me.id,
            'token': token
        }
    
    async def cancel_creation(self, user_id: int):
        """Batalkan pembuatan"""
        pending = self.pending_clients.get(user_id)
        if pending:
            try:
                await pending['client'].disconnect()
            except:
                pass
            del self.pending_clients[user_id]
        
        await db.clear_otp_state(user_id)

# Singleton
userbot_gen = UserbotGenerator()
