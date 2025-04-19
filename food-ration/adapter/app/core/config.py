"""
Configuration settings for the Food Department Adapter.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# API Settings
API_KEYS_ENABLED = True
DEFAULT_API_KEY = "secret123"
DEFAULT_TENANT_ID = "pension_system"
DEFAULT_DEPARTMENT = "Old Pension"

MYSQL_DB_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://admin:1234@mysql-db:3306/food_ration_db')

# Database Settings
DB_CONFIG = {
    'host': MYSQL_DB_URL.split('@')[1].split('/')[0],
    'user': MYSQL_DB_URL.split('://')[1].split(':')[0],
    'password': MYSQL_DB_URL.split(':')[2].split('@')[0],
    'db': MYSQL_DB_URL.split('/')[-1],
}

# Local Database Settings
LOCAL_DB_URL = MYSQL_DB_URL

# RabbitMQ Settings
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://admin:1234@rabbitmq:5672')

# Results directory
RESULTS_DIR = Path("./results")
RESULTS_DIR.mkdir(exist_ok=True)

# Batch Processing Settings
BATCH_SIZE = 10000
SCHEDULER_TIME = "01:00"  # 1 AM

# API Settings
PROJECT_NAME = "Food Department Adapter API"
PROJECT_DESCRIPTION = "Provider Service for Food Ration System"
VERSION = "1.0.0"