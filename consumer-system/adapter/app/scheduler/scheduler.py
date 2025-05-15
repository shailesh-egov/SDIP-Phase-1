from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduler.jobs.poll_job import poll_pending_requests
from app.utils.cron_token import get_cron_trigger
import logging

logger = logging.getLogger(__name__)


scheduler = BackgroundScheduler()

def schedule_polling_job():
    """
    Schedule the poll_pending_requests job using a strict cron trigger from .env.
    """
    try:
        trigger = get_cron_trigger()
    except Exception as e:
        logger.error(f"Invalid cron config: {e}. Stopping app startup.")
        raise  # or sys.exit(1)
    
    scheduler.add_job(
        poll_pending_requests,
        trigger=trigger,
        id="poll-pending",
        replace_existing=True
    )
    logger.info("✅ Scheduled job: poll_pending_requests")


def start():
    schedule_polling_job()
    scheduler.start()
    print("✅ Scheduler started.")

def stop():
    scheduler.shutdown()
    print("🛑 Scheduler stopped.")
