import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

PROCESS_URL = "http://localhost:5002/provider/request/process-requests"


def process_pending_requests():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = requests.get(PROCESS_URL)

        logger.info(f"[POLL] {now} → {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"[POLL] {now} → ERROR: {e}")


