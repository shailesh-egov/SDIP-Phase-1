import os
import logging
from logging.handlers import RotatingFileHandler


# Read environment config
ENV = os.environ.get("ENV", "prod").lower()
LOG_FILE = os.environ.get("LOG_FILE", "consumer.log")
LOG_LEVEL = logging.DEBUG if ENV == "dev" else logging.INFO

# Create logs directory relative to app/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, LOG_FILE),
            maxBytes=5 * 1024 * 1024,
            backupCount=3
        )
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
