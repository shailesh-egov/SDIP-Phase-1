from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduler.jobs.process_job import process_pending_requests
from app.core.logger import get_logger

scheduler = BackgroundScheduler()

logger = get_logger(__name__)
def start():
    scheduler.add_job(process_pending_requests, 'interval', minutes=5)  # time start with execution(independent)
    # scheduler.add_job(poll_pending_requests, 'cron', minute='1')  # time depends on clock 
    scheduler.start()
    logger.info(" Scheduler started.")

def stop():
    scheduler.shutdown()
    logger.info(" Scheduler stopped.")
