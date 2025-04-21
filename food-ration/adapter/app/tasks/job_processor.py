"""
Task processing functionality for the Food Department Adapter.
"""
import pika
import json
import threading
import schedule
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

from app.services.request_processor import process_verify_request, process_search_request

def process_job(job_data):
    logger.info("Processing job")
    try:
        # Use asyncio to run the async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job_data['processor'](job_data['request_data']))
        loop.close()
        logger.info("Job processed successfully")
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        raise

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
        method_frame, header_frame, body = channel.basic_get(queue='verify', auto_ack=False)
        if method_frame:
            request_data = json.loads(body)
            process_job({'processor': process_verify_request, 'request_data': request_data})
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            print(f"Processed inclusion job: {request_data['header']['request_id']}")
        
        # Process exclusion jobs
        method_frame, header_frame, body = channel.basic_get(queue='search_jobs', auto_ack=False)
        if method_frame:
            request_data = json.loads(body)
            process_job({'processor': process_search_request, 'request_data': request_data})
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            print(f"Processed exclusion job: {request_data['header']['request_id']}")
        
        connection.close()
    except Exception as e:
        print(f"Error in process_jobs: {str(e)}")

# def setup_rabbitmq():
#     """
#     Initialize RabbitMQ queues.
#     """
#     try:
#         connection_params = pika.URLParameters(RABBITMQ_URL)
#         connection = pika.BlockingConnection(connection_params)
#         channel = connection.channel()
        
#         # Declare queues
#         channel.queue_declare(queue='verify_jobs', durable=True)
#         channel.queue_declare(queue='search_jobs', durable=True)
        
#         connection.close()
#         print("RabbitMQ queues initialized")
#     except Exception as e:
#         print(f"Error setting up RabbitMQ: {str(e)}")

