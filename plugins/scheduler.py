from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from database import db
from config import Config

logger = logging.getLogger(__name__)

class BroadcastScheduler:
    def __init__(self, client):
        self.client = client
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.jobs = {}
    
    async def add_schedule(self, user_id: int, template_id: int, 
                          schedule_time: datetime, repeat: str = 'once'):
        """Tambah jadwal broadcast"""
        from .broadcast import BroadcastManager
        
        bm = BroadcastManager(self.client)
        
        job_id = f"broadcast_{user_id}_{template_id}_{schedule_time.timestamp()}"
        
        if repeat == 'once':
            trigger = 'date'
            run_date = schedule_time
        elif repeat == 'daily':
            trigger = CronTrigger(hour=schedule_time.hour, minute=schedule_time.minute)
        elif repeat == 'weekly':
            trigger = CronTrigger(day_of_week=schedule_time.weekday(), 
                                hour=schedule_time.hour, minute=schedule_time.minute)
        else:
            return False, "Tipe repeat tidak valid"
        
        job = self.scheduler.add_job(
            func=self._run_scheduled_broadcast,
            trigger=trigger,
            id=job_id,
            args=[user_id, template_id],
            replace_existing=True
        )
        
        self.jobs[job_id] = {
            'user_id': user_id,
            'template_id': template_id,
            'schedule_time': schedule_time,
            'repeat': repeat
        }
        
        # Simpan ke database
        async with db.conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO scheduled_broadcasts 
                (user_id, template_id, schedule_time, repeat_type, next_run)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, template_id, schedule_time, repeat, schedule_time))
            await db.conn.commit()
        
        return True, job_id
    
    async def _run_scheduled_broadcast(self, user_id: int, template_id: int):
        """Eksekusi broadcast terjadwal"""
        from .broadcast import BroadcastManager
        
        bm = BroadcastManager(self.client)
        await bm.start_broadcast(user_id, template_id, skip_confirmation=True)
        
        # Update last_run
        await db.update_user(user_id, last_scheduled_run=datetime.now())
    
    def remove_schedule(self, job_id: str):
        """Hapus jadwal"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            return True
        return False
    
    def get_user_schedules(self, user_id: int):
        """Get semua jadwal user"""
        return {k: v for k, v in self.jobs.items() if v['user_id'] == user_id}
