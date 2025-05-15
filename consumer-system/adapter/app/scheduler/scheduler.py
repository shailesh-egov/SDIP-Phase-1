from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduler.jobs.poll_job import poll_pending_requests

from app.core.logger import get_logger

logger = get_logger(__name__)

scheduler = BackgroundScheduler()

def start():
    scheduler.add_job(poll_pending_requests, 'interval', minutes=5)  # time start with execution(independent)
    # scheduler.add_job(poll_pending_requests, 'cron', minute='1')  # time depends on clock 
    scheduler.start()
    logger.info(" Scheduler started.")

def stop():
    scheduler.shutdown()
    logger.info(" Scheduler stopped.")
