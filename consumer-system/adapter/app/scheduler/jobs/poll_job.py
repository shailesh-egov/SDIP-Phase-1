import requests
from datetime import datetime

AUTH_URL = "http://localhost:5001/old-age-pension/request/auth/login"
FETCH_URL = "http://localhost:5001/old-age-pension/request/fetch_pending_requests"

USERNAME = "rohit"       # Replace with your actual username
PASSWORD = "rohit@123"   # Replace with your actual password

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
            print(f"[POLL] {now} → Auth failed: {auth_response.status_code} - {auth_response.text}")
            return
        
        token = auth_response.json().get("access_token")
        if not token:
            print(f"[POLL] {now} → Token missing in response")
            return

        # Step 2: Call protected API with token
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(FETCH_URL, headers=headers)

        print(f"[POLL] {now} → {response.status_code} {response.text}")

    except Exception as e:
        print(f"[POLL] {now} → ERROR: {e}")


