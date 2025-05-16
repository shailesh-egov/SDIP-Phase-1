import requests
from datetime import datetime
import os

from app.core.logger import get_logger

logger = get_logger(__name__)

AUTH_URL = os.environ.get('AUTH_URL')
FETCH_URL = os.environ.get('FETCH_URL')

USERNAME =  os.environ.get('CRONJOB_UERNAME')      # Replace with your actual username , who have all the access 
PASSWORD = os.environ.get('CRONJOB_PASSWORD')   # Replace with your actual password

def poll_pending_requests():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        # Step 1: Get token
        login_payload = {
            "username": USERNAME,
            "password": PASSWORD
        }
        auth_response = requests.post(AUTH_URL, json=login_payload)
        
        if auth_response.status_code != 200:
            logger.warning(f"[POLL] {now} -> Auth failed: {auth_response.status_code} - {auth_response.text}")
            return
        
        token = auth_response.json().get("access_token")
        if not token:
            logger.error(f"[POLL] {now} -> Token - missing in response")
            return

        # Step 2: Call protected API with token
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(FETCH_URL, headers=headers)

        logger.info(f"[POLL] {now} -> {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"[POLL] {now} -> ERROR: {e}")


