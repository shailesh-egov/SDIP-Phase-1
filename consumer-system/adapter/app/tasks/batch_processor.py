"""
Batch processing tasks for the Old Pension Adapter.
"""
import uuid
import datetime
import threading
import schedule
import time
import logging
from sqlalchemy import select

from app.db.models import SessionLocal, batch_tracker
from app.db.session import get_db_connection
from app.services.data_exchange_service import send_request_to_provider_service
from app.core.config import BATCH_SIZE, SCHEDULER_TIME

logger = logging.getLogger(__name__)

def process_batch(batch_data):
    logger.info("Processing batch")
    try:
        # ...existing code...
        logger.info("Batch processed successfully")
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        raise

def batch_process_citizens():
    """
    Scheduled batch job to process citizens from the Old Pension system
    """
    try:
        logger.info(f"Starting batch process at {datetime.datetime.now().isoformat()}")
        
        # Check if there's an incomplete batch
        session = SessionLocal()
        incomplete_batch = session.execute(
            select([batch_tracker]).where(batch_tracker.c.status.in_(["pending", "processing"]))
        ).fetchone()
        
        if incomplete_batch:
            logger.info(f"Found incomplete batch: {incomplete_batch.batch_id}")
            # Resume from last processed aadhar
            last_aadhar = incomplete_batch.last_aadhar
            request_id = incomplete_batch.request_id
            
            # Logic to resume processing would go here
            pass
        else:
            # Start a new batch
            
            # Get last run timestamp
            last_run_record = session.execute(
                select([batch_tracker]).order_by(batch_tracker.c.last_run.desc())
            ).fetchone()
            
            if last_run_record:
                last_run = last_run_record.last_run
                # Query new/updated records since last run
                query = f"""
                SELECT aadhar, name, age, gender, caste, location 
                FROM citizens 
                WHERE created_on >= '{last_run}' OR updated_on >= '{last_run}'
                ORDER BY aadhar
                LIMIT {BATCH_SIZE}
                """
            else:
                # First run - query all records
                query = f"""
                SELECT aadhar, name, age, gender, caste, location 
                FROM citizens 
                ORDER BY aadhar
                LIMIT {BATCH_SIZE}
                """
        
        session.close()
        
        # Connect to the database
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # In a real implementation, you'd execute the actual query
            # This is just a sample for the example
            cursor.execute("SELECT 1 as aadhar, 'John Doe' as name, 65 as age, 'male' as gender, 'X' as caste, 'CityA' as location UNION SELECT 2, 'Jane Smith', 70, 'female', 'Y', 'CityB'")
            citizens = cursor.fetchall()
        
        connection.close()
        
        if citizens:
            # Prepare verification request
            request_data = {
                "header": {
                    "request_id": str(uuid.uuid4()),
                    "request_type": "inclusion",
                    "tenant_id": "pension_system",
                    "timestamp": datetime.datetime.now().isoformat()
                },
                "body": {
                    "citizens": citizens,
                    "criteria": [
                        {
                            "field": "age",
                            "operator": ">",
                            "value": 60
                        },
                        {
                            "field": "gender",
                            "operator": "=",
                            "value": "male"
                        }
                    ]
                }
            }
            
            # Send the request - using the async send function via a threading workaround
            # since we're in a non-async context
            def send_request_sync():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(send_request_to_provider_service(request_data))
                loop.close()
                return result
            
            result = send_request_sync()
            logger.info(f"Processed {len(citizens)} citizens, result: {result}")
    except Exception as e:
        logger.error(f"Error in batch_process_citizens: {str(e)}")

def start_scheduler():
    """
    Start the scheduler for batch processing
    """
    schedule.every().day.at(SCHEDULER_TIME).do(batch_process_citizens)
    
    # Run the scheduler in a separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info(f"Scheduler started, will run at {SCHEDULER_TIME}")
    
    return scheduler_thread