import aiosqlite
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config import Config

class Database:
    def __init__(self):
        self.db_path = "auto_sebar.db"
    
    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expiry_date TIMESTAMP,
                    package TEXT DEFAULT 'FREE',
                    is_active INTEGER DEFAULT 1,
                    auto_promo INTEGER DEFAULT 0,
                    pm_permit INTEGER DEFAULT 0,
                    delay_seconds INTEGER DEFAULT 30,
                    total_sent INTEGER DEFAULT 0,
                    total_success INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    wallet_balance INTEGER DEFAULT 0,
                    referrer_id INTEGER,
                    UNIQUE(user_id)
                )
            ''')
            
            # Groups table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    group_title TEXT,
                    group_username TEXT,
                    group_link TEXT,
                    member_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_broadcast TIMESTAMP,
                    error_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # Messages/Templates table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS message_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    message_text TEXT,
                    media_type TEXT,
                    media_file_id TEXT,
                    media_path TEXT,
                    buttons TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    use_count INTEGER DEFAULT 0,
                    is_default INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # Broadcast logs
            await db.execute('''
                CREATE TABLE IF NOT EXISTS broadcast_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    template_id INTEGER,
                    group_id INTEGER,
                    status TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            ''')
            
            # Scheduled broadcasts
            await db.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    template_id INTEGER,
                    schedule_time TIMESTAMP,
                    repeat_type TEXT DEFAULT 'once',
                    repeat_interval INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP
                )
            ''')
            
            # Transactions/Payments
            await db.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    amount INTEGER,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    payment_proof TEXT
                )
            ''')
            
            # Group topics (for forum groups)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS group_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    topic_id INTEGER,
                    topic_name TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            await db.commit()
    
    # User methods
    async def add_user(self, user_id: int, username: str, full_name: str, 
                       phone: str = None, referrer_id: int = None) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            expiry = datetime.now() + timedelta(days=1)  # FREE trial
            
            try:
                await db.execute('''
                    INSERT OR IGNORE INTO users 
                    (user_id, username, full_name, phone, expiry_date, referrer_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, full_name, phone, expiry, referrer_id))
                await db.commit()
                return True
            except Exception as e:
                print(f"Error adding user: {e}")
                return False
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_user(self, user_id: int, **kwargs) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            await db.execute(f'UPDATE users SET {fields} WHERE user_id = ?', values)
            await db.commit()
            return True
    
    async def toggle_auto_promo(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if user:
            new_status = 0 if user['auto_promo'] else 1
            await self.update_user(user_id, auto_promo=new_status)
            return new_status == 1
        return False
    
    async def extend_package(self, user_id: int, package: str, days: int):
        expiry = datetime.now() + timedelta(days=days)
        await self.update_user(user_id, package=package, expiry_date=expiry)
    
    # Group methods
    async def add_group(self, user_id: int, group_id: int, group_title: str,
                        group_username: str = None, group_link: str = None,
                        member_count: int = 0) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT OR REPLACE INTO groups 
                    (user_id, group_id, group_title, group_username, group_link, member_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, group_id, group_title, group_username, group_link, member_count))
                await db.commit()
                return True
            except Exception as e:
                print(f"Error adding group: {e}")
                return False
    
    async def get_user_groups(self, user_id: int, status: str = None) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = 'SELECT * FROM groups WHERE user_id = ?'
            params = [user_id]
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_group_count(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT COUNT(*) FROM groups WHERE user_id = ? AND status = "active"',
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def update_group_status(self, group_id: int, status: str, error_msg: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            if error_msg:
                await db.execute('''
                    UPDATE groups SET status = ?, error_message = ?, error_count = error_count + 1 
                    WHERE group_id = ?
                ''', (status, error_msg, group_id))
            else:
                await db.execute(
                    'UPDATE groups SET status = ? WHERE group_id = ?',
                    (status, group_id)
                )
            await db.commit()
    
    async def remove_group(self, user_id: int, group_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'DELETE FROM groups WHERE user_id = ? AND group_id = ?',
                (user_id, group_id)
            )
            await db.commit()
    
    # Message template methods
    async def save_template(self, user_id: int, name: str, message_text: str,
                          media_type: str = None, media_file_id: str = None,
                          buttons: str = None, is_default: bool = False) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            if is_default:
                await db.execute(
                    'UPDATE message_templates SET is_default = 0 WHERE user_id = ?',
                    (user_id,)
                )
            
            cursor = await db.execute('''
                INSERT INTO message_templates 
                (user_id, name, message_text, media_type, media_file_id, buttons, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, message_text, media_type, media_file_id, buttons, int(is_default)))
            await db.commit()
            return cursor.lastrowid
    
    async def get_templates(self, user_id: int) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM message_templates WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_default_template(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM message_templates 
                WHERE user_id = ? AND is_default = 1
                LIMIT 1
            ''', (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # Broadcast logs
    async def log_broadcast(self, user_id: int, template_id: int, group_id: int,
                          status: str, error_message: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO broadcast_logs 
                (user_id, template_id, group_id, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, template_id, group_id, status, error_message))
            
            # Update user stats
            if status == 'success':
                await db.execute('''
                    UPDATE users SET total_sent = total_sent + 1, total_success = total_success + 1 
                    WHERE user_id = ?
                ''', (user_id,))
            else:
                await db.execute('''
                    UPDATE users SET total_sent = total_sent + 1, total_failed = total_failed + 1 
                    WHERE user_id = ?
                ''', (user_id,))
            
            await db.commit()
    
    # Stats
    async def get_user_stats(self, user_id: int) -> Dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT total_sent, total_success, total_failed FROM users WHERE user_id = ?
            ''', (user_id,)) as cursor:
                user_stats = await cursor.fetchone()
            
            async with db.execute('''
                SELECT COUNT(*) as today_sent FROM broadcast_logs 
                WHERE user_id = ? AND DATE(sent_at) = DATE('now')
            ''', (user_id,)) as cursor:
                today_stats = await cursor.fetchone()
            
            return {
                'total_sent': user_stats['total_sent'] if user_stats else 0,
                'total_success': user_stats['total_success'] if user_stats else 0,
                'total_failed': user_stats['total_failed'] if user_stats else 0,
                'today_sent': today_stats['today_sent'] if today_stats else 0
            }

db = Database()
