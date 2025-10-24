# ==============================
# app/scheduler.py
# ==============================
from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import time as dtime
from typing import Callable, Dict

class TaskScheduler:
    def __init__(self):
        self.sched = BackgroundScheduler()
        self.sched.start()
        self._job_ids = {}

    def clear(self):
        self.sched.remove_all_jobs()
        self._job_ids.clear()

    def schedule_daily_fixed(self, task_id: int, hour: int, minute: int, func: Callable):
        jid = f"task_{task_id}"
        trig = CronTrigger(hour=hour, minute=minute)
        self._job_ids[task_id] = self.sched.add_job(func, trig, id=jid, replace_existing=True)

    def schedule_every_minutes(self, task_id: int, minutes: int, func: Callable):
        jid = f"task_{task_id}"
        trig = IntervalTrigger(minutes=minutes)
        self._job_ids[task_id] = self.sched.add_job(func, trig, id=jid, replace_existing=True)

    def schedule_every_hours(self, task_id: int, hours: int, func: Callable):
        jid = f"task_{task_id}"
        trig = IntervalTrigger(hours=hours)
        self._job_ids[task_id] = self.sched.add_job(func, trig, id=jid, replace_existing=True)

    def remove(self, task_id: int):
        jid = f"task_{task_id}"
        try:
            self.sched.remove_job(jid)
        except Exception:
            pass
        self._job_ids.pop(task_id, None)
