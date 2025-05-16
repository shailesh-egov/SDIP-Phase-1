"""
Configuration settings for the Old Pension Adapter.
"""
import base64
import json
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Settings
API_KEY = os.environ.get('API_KEY', 'secret123')
PROVIDER_SERVICE_URL = os.environ.get('PROVIDER_SERVICE_URL', 'http://localhost:5002/provider')

# Database Settings
DB_CONFIG = {
    'host': os.environ.get('DATABASE_URL', 'mysql://admin:1234@mysql-db:3306/pension_db').split('@')[1].split('/')[0],
    'user': os.environ.get('DATABASE_URL', 'mysql://admin:1234@mysql-db:3306/pension_db').split('://')[1].split(':')[0],
    'password': os.environ.get('DATABASE_URL', 'mysql://admin:1234@mysql-db:3306/pension_db').split(':')[2].split('@')[0],
    'db': os.environ.get('DATABASE_URL', 'mysql://admin:1234@mysql-db:3306/pension_db').split('/')[-1],
}

# Define MYSQL_DB_URL for MySQL database connection
MYSQL_DB_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://admin:1234@mysql-db:3306/pension_db')

# Batch Processing Settings
BATCH_SIZE = 10000
SCHEDULER_TIME = "01:00"  # 1 AM

# API Settings
PROJECT_NAME = "Old Pension Adapter API"
PROJECT_DESCRIPTION = "Consumer Adapter for Old Pension System"
VERSION = "1.0.0"


# Process the ENCRYPTION_KEYS environment variable
ENCRYPTION_KEYS = {
    k: base64.b64decode(v) for k, v in json.loads(os.getenv("ENCRYPTION_KEYS")).items()
}
CURRENT_KEY_ID = os.getenv("CURRENT_KEY_ID")


KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM')
KEYCLOAK_URL = f"http://localhost:8080/realms/{KEYCLOAK_REALM}"
TOKEN_URL = f"{KEYCLOAK_URL}/protocol/openid-connect/token"
CERTS_URL = f"{KEYCLOAK_URL}/protocol/openid-connect/certs"
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')