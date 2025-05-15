"""
Database models and connection handling for the Old Pension Adapter.
"""
from sqlalchemy import  create_engine, Column, String, Integer, Float, DateTime, JSON, MetaData, Table ,Text
from sqlalchemy.orm import sessionmaker
import datetime


from app.core.config import MYSQL_DB_URL


from app.core.logger import get_logger

logger = get_logger(__name__)


# Initialize engine with pymysql driver
engine = create_engine(MYSQL_DB_URL.replace('mysql://', 'mysql+pymysql://'))
metadata = MetaData()

# Define tables
verify_results = Table(
    "verify_results",
    metadata,
    Column("aadhar", String(64), primary_key=True),
    Column("request_id", String(50), primary_key=True),
    Column("criteria_results", JSON),
    Column("match_score", Float),
    Column("stored_at", DateTime),
)

search_results = Table(
    "search_results",
    metadata,
    Column("aadhar", String(64), primary_key=True),
    Column("request_id", String(50), primary_key=True),
    Column("citizen_data", JSON),
    Column("stored_at", DateTime),
)

batch_tracker = Table(
    "batch_tracker",
    metadata,
    Column("batch_id", String(50), primary_key=True),
    Column("request_id", String(50)),
    Column("last_aadhar", String(12)),
    Column("last_run", DateTime),
    Column("status", String(20)),
    Column("request_payload", JSON),  # New column to store request payload
    Column("last_part_processed", Integer, nullable=False, default=0),
    Column("last_index",         Integer,     nullable=False, default=-1),
)


citizens = Table(
    "citizens",
    metadata,
    Column("aadhar", String(12), primary_key=True),
    Column("name", String(100)),
    Column("age", Integer),
    Column("gender", String(10)),
    Column("caste", String(50)),
    Column("phone_number", String(10)),
    Column("location", String(100)),
    Column("created_on", DateTime),
    Column("updated_on", DateTime),
)

# Create tables
metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    Get a database session.
    Returns a SQLAlchemy session.
    """
    session = SessionLocal()
    try:
        return session
    finally:
        session.close()



def insert_default_api_key():
    logger.info("Inserting default API key into the database")
    try:
        # ...existing code...
        logger.info("Default API key inserted successfully")
    except Exception as e:
        logger.error(f"Error inserting default API key: {str(e)}")
        raise