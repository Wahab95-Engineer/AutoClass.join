import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_meetings, get_accounts, add_meeting, add_log
from email_reader import fetch_meetings
from joiner import join_meeting
import os

scheduler = BackgroundScheduler(timezone="Asia/Karachi")

def check_meetings():
    now = datetime.now()
    for m in get_meetings("pending"):
        if not m["scheduled_time"]: continue
        try:
            sched = datetime.fromisoformat(m["scheduled_time"])
            early = sched - timedelta(minutes=int(os.getenv("JOIN_EARLY_MINUTES", 2)))
            if early <= now <= sched + timedelta(minutes=10):
                name = os.getenv("DISPLAY_NAME", "Student")
                threading.Thread(target=join_meeting, args=(m, name), daemon=True).start()
        except: pass

def sync_emails():
    for acc in get_accounts():
        for m in fetch_meetings(acc):
            add_meeting(m["title"], m["link"], m["platform"], m["scheduled_time"], m["source"])

def start():
    scheduler.add_job(check_meetings, "interval", minutes=1)
    scheduler.add_job(sync_emails, "interval", minutes=15)
    scheduler.start()
    add_log("⚡ Scheduler started")