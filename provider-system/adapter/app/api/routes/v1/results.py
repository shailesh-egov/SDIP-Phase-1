from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

import json

from app.api.dependencies import require_roles_factory, verify_api_key
from app.db.models import SessionLocal, request_tracker
from app.core.config import RESULTS_DIR, ENCRYPTION_KEYS, CURRENT_KEY_ID
from app.utils.key_manager import KeyManager
from app.utils.encryptor import Encryptor


from app.core.logger import get_logger

logger = get_logger(__name__)

# Initialize KeyManager and Encryptor
key_manager = KeyManager(ENCRYPTION_KEYS, CURRENT_KEY_ID)
encryptor = Encryptor(key_manager)



router = APIRouter()


@router.get("/{request_id}/{part}.json")
async def get_results(request_id: str, part: str,user_info: dict = Depends(require_roles_factory(["admin", "data_writer"])), api_key: dict = Depends(verify_api_key)):
    """
    Returns the decrypted results file for a specific request and part.
    """
    logger.info(f"Received request to fetch results for request_id: {request_id}, part: {part}")
    try:
        # Check if result file exists
        file_path = RESULTS_DIR / request_id / f"{part}.json"
        logger.debug(f"Checking if file exists at path: {file_path}")

        if not file_path.exists():
            logger.warning(f"Result file {part}.json not found for request {request_id}")
            raise HTTPException(status_code=404, detail=f"Result file {part}.json not found for request {request_id}")

        # Verify tenant_id has access to this request
        session = SessionLocal()
        logger.debug(f"Fetching request tracker record for request_id: {request_id}")
        status_record = session.execute(
            select(request_tracker).where(
                request_tracker.c.request_id == request_id,
                request_tracker.c.tenant_id == api_key["tenant_id"]
            )
        ).fetchone()
        session.close()

        if not status_record:
            logger.warning(f"Unauthorized access attempt for request_id: {request_id}")
            raise HTTPException(status_code=403, detail="Not authorized to access this request")
        else:
            logger.info(f"status_rocord : {status_record}")

        # Read and decrypt the file contents
        with open(file_path, "r") as file:
            encrypted_data = json.load(file)

        decrypted_data = encryptor.decrypt(encrypted_data)

        logger.info(f"Returning decrypted result for request_id: {request_id}, part: {part}")
        return decrypted_data

    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))