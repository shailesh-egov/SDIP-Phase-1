"""
Task processing functionality for the Food Department Adapter.
"""
import pika
import json
import threading
import schedule
import time
import asyncio

from app.core.config import RABBITMQ_URL, SCHEDULER_TIME
from app.services.request_processor import process_inclusion_request, process_exclusion_request

def process_jobs():
    """
    Processes jobs from the RabbitMQ queues.
    """
    try:
        # Connect to RabbitMQ
        connection_params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Process inclusion jobs
        method_frame, header_frame, body = channel.basic_get(queue='verify_jobs', auto_ack=False)
        if method_frame:
            request_data = json.loads(body)
            
            # Use asyncio to run the async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_inclusion_request(request_data))
            loop.close()
            
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            print(f"Processed inclusion job: {request_data['header']['request_id']}")
        
        # Process exclusion jobs
        method_frame, header_frame, body = channel.basic_get(queue='search_jobs', auto_ack=False)
        if method_frame:
            request_data = json.loads(body)
            
            # Use asyncio to run the async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_exclusion_request(request_data))
            loop.close()
            
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            print(f"Processed exclusion job: {request_data['header']['request_id']}")
        
        connection.close()
    except Exception as e:
        print(f"Error in process_jobs: {str(e)}")

def setup_rabbitmq():
    """
    Initialize RabbitMQ queues.
    """
    try:
        connection_params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Declare queues
        channel.queue_declare(queue='verify_jobs', durable=True)
        channel.queue_declare(queue='search_jobs', durable=True)
        
        connection.close()
        print("RabbitMQ queues initialized")
    except Exception as e:
        print(f"Error setting up RabbitMQ: {str(e)}")

def start_scheduler():
    """
    Start the scheduler for processing jobs.
    """
    schedule.every().day.at(SCHEDULER_TIME).do(process_jobs)
    
    # Also schedule to run every 5 minutes to keep checking for new jobs
    schedule.every(5).minutes.do(process_jobs)
    
    # Run the scheduler in a separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    print(f"Scheduler started, will run at {SCHEDULER_TIME} and every 5 minutes")
    
    return scheduler_thread