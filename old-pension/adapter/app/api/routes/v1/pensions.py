"""
API routes for pension-related operations.
"""
from fastapi import APIRouter, Depends, HTTPException
import pika
import json

from app.api.dependencies import verify_api_key
from app.db.session import get_db_connection
from app.core.config import RABBITMQ_URL

router = APIRouter()

@router.get("/")
async def get_pensions(api_key: str = Depends(verify_api_key)):
    """
    Get a list of pensions from the Old Pension system
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # Sample query - in a real app, you'd have actual tables and queries
            cursor.execute("SELECT 1 as id, 'P12345' as pension_id, 'John Doe' as beneficiary, 5000 as amount UNION SELECT 2, 'P67890', 'Jane Smith', 6000")
            pensions = cursor.fetchall()
        
        connection.close()
        return {"status": "success", "data": pensions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_pension(data: dict, api_key: str = Depends(verify_api_key)):
    """
    Create a new pension application
    """
    if not data or not data.get('beneficiary') or not data.get('amount'):
        raise HTTPException(status_code=400, detail="Beneficiary name and amount are required")
    
    try:
        # Connect to RabbitMQ to publish a message
        connection_params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Declare a queue
        channel.queue_declare(queue='pension_events')
        
        # Publish message
        message = json.dumps({
            'event': 'pension_application_submitted',
            'data': data
        })
        
        channel.basic_publish(
            exchange='',
            routing_key='pension_events',
            body=message
        )
        
        connection.close()
        
        return {
            "status": "success",
            "message": "Pension application submitted successfully",
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))