# ==============================
# app/scheduler.py
# ==============================
from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Callable

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

    def schedule_every_seconds(self, task_id: int, seconds: int, func: Callable, next_run_time: datetime | None = None):
        jid = f"task_{task_id}"
        trig = IntervalTrigger(seconds=seconds)
        self._job_ids[task_id] = self.sched.add_job(func, trig, id=jid, replace_existing=True, next_run_time=next_run_time)

    def schedule_once_at(self, task_id: int, run_date: datetime, func: Callable):
        jid = f"task_once_{task_id}_{int(run_date.timestamp())}"
        self.sched.add_job(func, 'date', id=jid, run_date=run_date, replace_existing=False)

    def remove(self, task_id: int):
        jid = f"task_{task_id}"
        try:
            self.sched.remove_job(jid)
        except Exception:
            pass
        self._job_ids.pop(task_id, None)
