import aiosqlite
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class Database:
    def __init__(self):
        self.db_path = "sebar.db"
    
    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Users (bot utama)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned INTEGER DEFAULT 0
                )
            ''')
            
            # Userbots (session yang dibuat)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS userbots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    session_name TEXT UNIQUE,
                    phone TEXT,
                    user_id INTEGER,
                    username TEXT,
                    token TEXT UNIQUE,
                    package_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expiry_date TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    auto_promo INTEGER DEFAULT 0,
                    pm_permit INTEGER DEFAULT 0,
                    FOREIGN KEY (owner_id) REFERENCES users(user_id)
                )
            ''')
            
            # Payments
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    userbot_id INTEGER,
                    package_type TEXT,
                    amount INTEGER,
                    status TEXT DEFAULT 'pending',
                    qris_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP
                )
            ''')
            
            # OTP State (untuk proses pembuatan)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS otp_states (
                    user_id INTEGER PRIMARY KEY,
                    phone TEXT,
                    phone_code_hash TEXT,
                    session_name TEXT,
                    package_type TEXT,
                    step TEXT DEFAULT 'phone',  -- phone, otp, 2fa, done
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Groups untuk broadcast
            await db.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userbot_id INTEGER,
                    group_id INTEGER,
                    group_title TEXT,
                    status TEXT DEFAULT 'active',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    # User methods
    async def add_user(self, user_id: int, username: str, full_name: str, phone: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, username, full_name, phone)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, full_name, phone))
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # Userbot methods
    async def create_userbot(self, owner_id: int, session_name: str, phone: str, 
                            user_id: int, username: str, package_type: str, 
                            duration_days: int) -> str:
        # Generate token
        token = f"LIFE-UBOT:{secrets.token_urlsafe(64)}"
        expiry = datetime.now() + timedelta(days=duration_days)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO userbots 
                (owner_id, session_name, phone, user_id, username, token, package_type, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (owner_id, session_name, phone, user_id, username, token, package_type, expiry))
            await db.commit()
        
        return token
    
    async def get_userbot(self, owner_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM userbots 
                WHERE owner_id = ? AND is_active = 1
                ORDER BY created_at DESC LIMIT 1
            ''', (owner_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_userbot_by_token(self, token: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM userbots WHERE token = ?', (token,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # OTP State methods
    async def set_otp_state(self, user_id: int, phone: str = None, 
                          phone_code_hash: str = None, session_name: str = None,
                          package_type: str = None, step: str = 'phone'):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO otp_states 
                (user_id, phone, phone_code_hash, session_name, package_type, step)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, phone, phone_code_hash, session_name, package_type, step))
            await db.commit()
    
    async def get_otp_state(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM otp_states WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def clear_otp_state(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM otp_states WHERE user_id = ?', (user_id,))
            await db.commit()
    
    # Toggle auto promo
    async def toggle_auto_promo(self, userbot_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            # Get current
            async with db.execute('SELECT auto_promo FROM userbots WHERE id = ?', (userbot_id,)) as cursor:
                row = await cursor.fetchone()
                current = row[0] if row else 0
            
            new_status = 0 if current else 1
            await db.execute('UPDATE userbots SET auto_promo = ? WHERE id = ?', (new_status, userbot_id))
            await db.commit()
            return new_status == 1
    
    # Payment methods
    async def create_payment(self, user_id: int, package_type: str, amount: int, qris_url: str = None) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO payments (user_id, package_type, amount, qris_url)
                VALUES (?, ?, ?, ?)
            ''', (user_id, package_type, amount, qris_url))
            await db.commit()
            return cursor.lastrowid
    
    async def confirm_payment(self, payment_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE payments SET status = 'paid', paid_at = ? WHERE id = ?
            ''', (datetime.now(), payment_id))
            await db.commit()

db = Database()
