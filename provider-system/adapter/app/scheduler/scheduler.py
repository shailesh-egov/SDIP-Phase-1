from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduler.jobs.process_job import process_pending_requests
from app.utils.cron_token import get_cron_trigger
import logging

logger = logging.getLogger(__name__)


scheduler = BackgroundScheduler()

def schedule_process_job():
    """
    Schedule the process_pending_requests job using a strict cron trigger from .env.
    """
    try:
        trigger = get_cron_trigger()
    except Exception as e:
        logger.error(f"Invalid cron config: {e}. Stopping app startup.")
        raise  # or sys.exit(1)
    scheduler.add_job(
        process_pending_requests,
        trigger=trigger,
        id="process-pending",
        replace_existing=True
    )
    logger.info(" Scheduled job: process_pending_requests")


def start():
    schedule_process_job()
    scheduler.start()
    logger.info(" Scheduler started.")

def stop():
    scheduler.shutdown()
    logger.info(" Scheduler stopped.")
