from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def start():
    scheduler.start()

def add_cron(func, hours, job_id):
    scheduler.add_job(
        func=func,
        trigger=CronTrigger(hour=",".join(map(str, hours)), minute=0),
        id=job_id,
        replace_existing=True
    )
