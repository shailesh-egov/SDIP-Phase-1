"""
Main application initialization for the Provider Adapter.
"""
from fastapi import FastAPI, Depends
from app.api.routes import api_router
from app.core.config import PROJECT_NAME, PROJECT_DESCRIPTION, VERSION, CONTEXT_PATH
# from app.tasks.job_processor import start_scheduler, setup_rabbitmq
from app.db.models import metadata, engine
from sqlalchemy.exc import OperationalError
import pika
import time
import logging
from app.scheduler import scheduler

logger = logging.getLogger(__name__)

# Add logging to application startup
logger.info("Starting Provider Adapter application")

# Initialize FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    version=VERSION
)

# Update API routes to use CONTEXT_PATH
define_context_path = f"{CONTEXT_PATH}"
app.include_router(api_router, prefix=define_context_path)


# Define root endpoint
@app.get(f"{CONTEXT_PATH}/health", tags=["status"])
async def root():
    """
    Root endpoint to check service status
    """
    return {
        "service": PROJECT_NAME,
        "status": "running",
        "version": VERSION
    }

# Ensure MySQL and RabbitMQ are started before the service starts
@app.on_event("startup")
def check_dependencies():
    # Check MySQL connection
    while True:
        try:
            engine.connect()
            print("MySQL is up and running.")
            break
        except OperationalError:
            print("Waiting for MySQL to be ready...")
            time.sleep(5)

# Initialize RabbitMQ and start the scheduler when the application starts
@app.on_event("startup")
async def startup_event():
    # Create all tables
    metadata.create_all(engine)
    # Setup RabbitMQ queues
    # setup_rabbitmq()
    # Start the scheduler for processing jobs
    # start_scheduler()



@app.on_event("startup")
def on_startup():
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.stop()

logger.info("Application started successfully")