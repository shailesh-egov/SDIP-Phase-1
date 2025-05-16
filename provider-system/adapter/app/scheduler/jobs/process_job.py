import requests
from datetime import datetime
from app.core.logger import get_logger
import os


PROCESS_URL = os.environ.get('PROCESS_URL')

logger = get_logger(__name__)

def process_pending_requests():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = requests.get(PROCESS_URL)
        
        logger.info(f"[POLL] {now} -> {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"[POLL] {now} -> ERROR: {e}")


