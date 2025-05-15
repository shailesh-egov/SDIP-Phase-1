"""
Database models and connection handling for the Food Department Adapter.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, MetaData, Table
from sqlalchemy.orm import sessionmaker
import datetime
import json


from app.core.config import DEFAULT_API_KEY, DEFAULT_TENANT_ID, DEFAULT_DEPARTMENT, MYSQL_DB_URL


from app.core.logger import get_logger

logger = get_logger(__name__)


# Initialize engine with pymysql driver
engine = create_engine(MYSQL_DB_URL.replace('mysql://', 'mysql+pymysql://'))
metadata = MetaData()

# Define tables
request_tracker = Table(
    "request_tracker",
    metadata,
    Column("tenant_id", String(50), primary_key=True),
    Column("request_id", String(50), primary_key=True),
    Column("status", String(20)),
    Column("files", JSON),
    Column("error", String(255)),
    Column("created_at", DateTime),
    Column("request_payload", JSON),
    Column("last_processed_index", Integer, default=0)
)

api_keys = Table(
    "api_keys",
    metadata,
    Column("api_key", String(50), primary_key=True),
    Column("tenant_id", String(50)),
    Column("department", String(100)),
    Column("created_at", DateTime),
)

citizens = Table(
    "citizens",
    metadata,
    Column("aadhar", String(12), primary_key=True),
    Column("name", String(100)),
    Column("age", Integer),
    Column("gender", String(10)),
    Column("caste", String(50)),
    Column("location", String(100)),
    Column("phone_number", String(10)),
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

# Insert default API key if not exists


def insert_default_api_key():
    logger.info("Inserting default API key into the database")
    try:
        session = SessionLocal()
        
        # Check if API key already exists
        existing_key = session.execute(
            api_keys.select().where(api_keys.c.api_key == DEFAULT_API_KEY)
        ).fetchone()
        
        if not existing_key:
            # Insert the default API key
            session.execute(
                api_keys.insert().values(
                    api_key=DEFAULT_API_KEY,
                    tenant_id=DEFAULT_TENANT_ID,
                    department=DEFAULT_DEPARTMENT,
                    created_at=datetime.datetime.now()
                )
            )
            session.commit()
            logger.info("Default API key inserted successfully")
        
        session.close()
    except Exception as e:
        logger.error(f"Error inserting default API key: {str(e)}")
        raise

# Call function to insert default API key
insert_default_api_key()