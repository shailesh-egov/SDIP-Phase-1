"""
Service for handling data exchange with the provider system.
"""
from fastapi import HTTPException, Request
import httpx
import json
import uuid
import datetime
import asyncio
import hashlib
import logging

from sqlalchemy import select, update

from app.core.config import API_KEY, PROVIDER_SERVICE_URL
from app.db.models import (
    SessionLocal, 
    batch_tracker, 
    verify_results, 
    search_results 
)

# app/utils/mask.py
from app.utils.mask import mask_id_with_hash

# app/utils/crypto_handler.py
from app.utils.key_manager import KeyManager
from app.utils.encryptor import Encryptor
from app.core.config import ENCRYPTION_KEYS, CURRENT_KEY_ID

# Initialize once and reuse
key_manager = KeyManager(ENCRYPTION_KEYS, CURRENT_KEY_ID)
encryptor = Encryptor(key_manager)


logger = logging.getLogger(__name__)

async def send_request_to_provider_service(request_data ,request:Request):
    """
    Sends a request to the Provider system's /provider/request endpoint
    """
    logger.info("Starting send_request_to_provider_service")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
            raise HTTPException(status_code=401, detail="Missing token")
    

    try:

    
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PROVIDER_SERVICE_URL}/request/create",
                json=request_data,
                headers={"X-API-Key": API_KEY,"Authorization": f"Bearer {token}"},
                timeout=30.0  # 30 second timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                request_id = response_data["header"]["request_id"]
                
                # Track the batch
                with SessionLocal() as session:
                    batch_id = str(uuid.uuid4())
                    session.execute(
                        batch_tracker.insert().values(
                            batch_id=batch_id,
                            request_id=request_id,
                            last_aadhar="",  # Will be populated during processing
                            last_run=datetime.datetime.now(),
                            status="pending",
                            request_payload=json.dumps(request_data)  # Store the request payload
                        )
                    )
                    session.commit()
                
                logger.info(f"Request {request_id} queued successfully")
                return {
                    "header": {
                        "request_id": request_id,
                        "status": "queued"
                    }
                }
            else:
                logger.error(f"Error sending request to Provider Service: {response.text}")
                return {
                    "header": {
                        "status": "error",
                        "message": f"Error communicating with Provider Service: {response.text}"
                    }
                }
    except Exception as e:
        logger.error(f"Error in send_request_to_Provider_service: {str(e)}")
        return {
            "header": {
                "status": "error",
                "message": f"Error sending request: {str(e)}"
            }
        }



async def poll_provider_service_results(request_id: str , request:Request):
    """
    Poll provider for a request, then fetch each part and process it.
    Uses batch_tracker.last_part_processed & last_index to resume on failure.
    """
    logger.info(f"Polling provider for request_id={request_id!r}")
    logger.info(f"Polling provider for request={request}")
    logger.info(f"Polling provider for request={request.headers}")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
            raise HTTPException(status_code=401, detail="Missing token")

    # 1) Load or initialize checkpoint
    with SessionLocal() as sess:
        row = sess.execute(
            select(
                batch_tracker.c.last_part_processed,
                batch_tracker.c.last_index
            ).where(batch_tracker.c.request_id == request_id)
        ).one_or_none()

    if row is None:
        last_part, last_index = 0, -1
        _update_status(request_id, "processing",
                       last_part_processed=0, last_index=-1)
    else:
        last_part, last_index = row

    try:

        # 2) Check provider status
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PROVIDER_SERVICE_URL}/request/status/{request_id}",
                headers={"X-API-Key": API_KEY,"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            resp.raise_for_status()
            body = resp.json()["body"]
            state = body["status"]

        if state == "failed":
            _update_status(request_id, "failed")
            return
        elif state != "completed":
            _update_status(request_id, "processing")
            return

        files = body["files"]

        # 3) For each new part
        for file_path in files:
            part = int(file_path.rsplit("/", 1)[-1].split(".")[0])
            # skip fully done parts
            if part < last_part or (part == last_part and last_index == -1 and last_part != 0):
                continue

            # 4) Fetch JSON for this part
            async with httpx.AsyncClient() as client:
                part_resp = await client.get(
                    f"{PROVIDER_SERVICE_URL}/results/{request_id}/{part}.json",
                    headers={"X-API-Key": API_KEY,"Authorization": f"Bearer {token}"},
                    timeout=30.0
                )
                part_resp.raise_for_status()
                data = part_resp.json()

            # 5) Process part with one session
            _process_one_part(request_id, part, data, last_part, last_index)

            # after successful part
            last_part, last_index = part, -1  # reset last_index for next part

        # 6) All parts done
        _update_status(request_id, "completed")
        logger.info(f"Request {request_id!r} fully completed")

    except Exception:
        logger.exception(f"Unhandled error for request_id={request_id!r}")
        _update_status(request_id, "error")
        raise


def _process_one_part(request_id, part, data, last_part, last_index):
    """
    Insert records for one part in bulk, checkpointing on first failure.
    """
    request_type = data["header"]["request_type"]
    body = data["body"]
    records = (
        body.get("results", [])
        if request_type == "verify"
        else body.get("citizens", [])
    )

    # determine starting index
    start_idx = last_index + 1 if part == last_part else 0

    start_idx = (last_index + 1) if (part == last_part) else 0

    # If we’re already past the end, mark the part done and skip it
    if start_idx >= len(records):
        _update_status(
            request_id,
            status="processing",
            last_part_processed=part,
            last_index=-1   # reset for the next part
        )
        return  # or `continue` if you're in a loop over parts


    batch = []

    # 1) Validate & transform
    for idx, item in enumerate(records[start_idx:], start_idx):
        try:
            if request_type == "verify":
                criteria_results = item.get("criteria_results", {})
                encrypted_data = encryptor.encrypt(criteria_results)
                masked_aadhar = mask_id_with_hash(item.get("aadhar", ""))
                batch.append({
                    "request_id":      request_id,
                    "aadhar":          masked_aadhar,
                    "criteria_results":encrypted_data,
                    "match_score":     item.get("match_score", 0.0),
                    "stored_at":       datetime.datetime.now(),
                })
            else:
                aadhar = item.get("aadhar") or hashlib.md5(item["name"].encode()).hexdigest()[:12]
                masked_aadhar = mask_id_with_hash(aadhar)
                encrypted_data = encryptor.encrypt(item)
                batch.append({
                    "request_id":   request_id,
                    "aadhar":       masked_aadhar,
                    "citizen_data": encrypted_data,
                    "stored_at":    datetime.datetime.now(),
                })
        except Exception as e:
            # on validation error, checkpoint and abort
            _update_status(request_id, "error",
                           last_part_processed=part,
                           last_index=idx)
            raise

    # 2) Bulk insert in one session
    if batch:
        table = verify_results if request_type == "verify" else search_results
        with SessionLocal() as sess:
            sess.execute(table.insert(), batch)
            sess.commit()

    # 3) Checkpoint end-of-part
    _update_status(request_id, "processing",
                   last_part_processed=part,
                   last_index=len(records) - 1)


def _update_status(request_id, status,
                   last_part_processed=None, last_index=None):
    """
    Atomically update batch_tracker for this request_id.
    """
    vals = {"status": status, "last_run": datetime.datetime.now()}
    if last_part_processed is not None:
        vals["last_part_processed"] = last_part_processed
    if last_index is not None:
        vals["last_index"] = last_index

    with SessionLocal() as sess:
        sess.execute(
            update(batch_tracker)
            .where(batch_tracker.c.request_id == request_id)
            .values(**vals)
        )
        sess.commit()
