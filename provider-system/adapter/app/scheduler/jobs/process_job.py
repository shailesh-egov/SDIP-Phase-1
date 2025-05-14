import requests
from datetime import datetime

PROCESS_URL = "http://localhost:5002/provider/request/process-requests"


def process_pending_requests():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = requests.get(PROCESS_URL)

        print(f"[POLL] {now} → {response.status_code} {response.text}")

    except Exception as e:
        print(f"[POLL] {now} → ERROR: {e}")


