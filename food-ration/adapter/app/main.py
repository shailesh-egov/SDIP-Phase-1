"""
Main application initialization for the Food Department Adapter.
"""
from fastapi import FastAPI, Depends
from app.api.routes import api_router
from app.core.config import PROJECT_NAME, PROJECT_DESCRIPTION, VERSION
# from app.tasks.job_processor import start_scheduler, setup_rabbitmq
from app.db.models import metadata, engine
from sqlalchemy.exc import OperationalError
import pika
import time
import logging

logger = logging.getLogger(__name__)

# Add logging to application startup
logger.info("Starting Food Ration Adapter application")

# Initialize FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    version=VERSION
)

# Include API routes
app.include_router(api_router)

# Define root endpoint
@app.get("/health", tags=["status"])
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

    # Check RabbitMQ connection
    # while True:
    #     try:
    #         connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    #         connection.close()
    #         print("RabbitMQ is up and running.")
    #         break
    #     except pika.exceptions.AMQPConnectionError:
    #         print("Waiting for RabbitMQ to be ready...")
    #         time.sleep(5)

# Initialize RabbitMQ and start the scheduler when the application starts
@app.on_event("startup")
async def startup_event():
    # Create all tables
    metadata.create_all(engine)
    # Setup RabbitMQ queues
    # setup_rabbitmq()
    # Start the scheduler for processing jobs
    # start_scheduler()

logger.info("Application started successfully")