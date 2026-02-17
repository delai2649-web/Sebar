import logging
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid, FloodWait
)

logger = logging.getLogger(__name__)

class OTPHandler:
    def __init__(self):
        self.pending_sessions = {}
    
    async def send_otp(self, client: Client, phone: str) -> tuple:
        """Kirim kode OTP"""
        try:
            await client.connect()
            sent_code = await client.send_code(phone)
            return True, sent_code.phone_code_hash
            
        except PhoneNumberInvalid:
            return False, "Nomor telepon tidak valid!"
        except FloodWait as e:
            return False, f"Terlalu banyak percobaan. Tunggu {e.value} detik."
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def verify_otp(self, client: Client, phone: str, phone_code_hash: str, otp: str) -> tuple:
        """Verifikasi OTP"""
        try:
            await client.sign_in(phone, phone_code_hash, otp)
            return True, "SUCCESS"
            
        except PhoneCodeInvalid:
            return False, "Kode OTP salah!"
        except PhoneCodeExpired:
            return False, "Kode OTP sudah expired!"
        except SessionPasswordNeeded:
            return True, "2FA_REQUIRED"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def verify_2fa(self, client: Client, password: str) -> tuple:
        """Verifikasi 2FA password"""
        try:
            await client.check_password(password)
            return True, "SUCCESS"
            
        except PasswordHashInvalid:
            return False, "Password 2FA salah!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def format_otp(self, otp_input: str) -> str:
        """Format input OTP (hapus spasi)"""
        return otp_input.replace(' ', '').replace('-', '')

# Singleton
otp_handler = OTPHandler()
