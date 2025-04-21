"""
Configuration settings for the Food Department Adapter.
"""
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
from urllib.parse import urlparse


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Settings
API_KEYS_ENABLED = True
DEFAULT_API_KEY = "secret123"
DEFAULT_TENANT_ID = "pension_system"
DEFAULT_DEPARTMENT = "Old Pension"

MYSQL_DB_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://admin:1234@mysql-db:3306/food_ration_db')

url = urlparse(MYSQL_DB_URL)

# Database Settings
DB_CONFIG = {
    'host': url.hostname,
    'port': url.port or 3306,
    'user': url.username,
    'password': url.password,
    'db': url.path.lstrip('/'),
}

# Local Database Settings
LOCAL_DB_URL = MYSQL_DB_URL

# Results directory
RESULTS_DIR = Path(os.environ.get('RESULTS_DIR', './results'))
RESULTS_DIR.mkdir(exist_ok=True)

# Batch Processing Settings
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))  # Default to 100 if not set

# API Settings
PROJECT_NAME = "Food Department Adapter API"
PROJECT_DESCRIPTION = "Provider Service for Food Ration System"
VERSION = "1.0.0"