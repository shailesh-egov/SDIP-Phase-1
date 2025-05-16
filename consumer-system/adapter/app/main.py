"""
Main application initialization for the Old Pension Adapter.
"""
from fastapi import FastAPI, Depends
from app.api.routes import api_router
from app.core.config import PROJECT_NAME, PROJECT_DESCRIPTION, VERSION
from app.tasks.batch_processor import start_scheduler
from app.db.models import metadata, engine
from sqlalchemy.exc import OperationalError
import pika
import time
import os

from app.scheduler import scheduler

# Initialize FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    version=VERSION
)

# Include API routes
app.include_router(api_router, prefix="/consumer")

# Define root endpoint
@app.get("/consumer/health", tags=["status"])
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
    # rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
    # connection_params = pika.URLParameters(rabbitmq_url)
    # while True:
    #     try:
    #         connection = pika.BlockingConnection(connection_params)
    #         connection.close()
    #         print("RabbitMQ is up and running.")
    #         break
    #     except pika.exceptions.AMQPConnectionError:
    #         print("Waiting for RabbitMQ to be ready...")
    #         time.sleep(5)

# Start the scheduler when the application starts
@app.on_event("startup")
async def startup_event():
    # Create all tables
    metadata.create_all(engine)
    # Start the scheduler for batch processing
    start_scheduler()


@app.on_event("startup")
def on_startup():
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.stop()