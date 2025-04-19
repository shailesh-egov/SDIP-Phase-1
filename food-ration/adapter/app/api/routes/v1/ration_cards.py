"""
API routes for ration card operations in the Food Department Adapter.
"""
from fastapi import APIRouter, Depends, HTTPException
import pika
import json

from app.api.dependencies import verify_api_key
from app.db.session import get_db_connection
from app.core.config import RABBITMQ_URL

router = APIRouter()

@router.get("/")
async def get_ration_cards(api_key: dict = Depends(verify_api_key)):
    """
    Get a list of ration cards from the Food Department system
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # Sample query - in a real app, you'd have actual tables and queries
            cursor.execute("SELECT 1 as id, 'ABC123' as card_number, 'Active' as status UNION SELECT 2, 'XYZ456', 'Active'")
            ration_cards = cursor.fetchall()
        
        connection.close()
        return {"status": "success", "data": ration_cards}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_ration_card(data: dict, api_key: dict = Depends(verify_api_key)):
    """
    Create a new ration card
    """
    if not data or not data.get('card_number'):
        raise HTTPException(status_code=400, detail="Card number is required")
    
    try:
        # Connect to RabbitMQ to publish a message
        connection_params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Declare a queue
        channel.queue_declare(queue='food_department_events')
        
        # Publish message
        message = json.dumps({
            'event': 'ration_card_created',
            'data': data
        })
        
        channel.basic_publish(
            exchange='',
            routing_key='food_department_events',
            body=message
        )
        
        connection.close()
        
        return {
            "status": "success",
            "message": "Ration card creation request submitted",
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))