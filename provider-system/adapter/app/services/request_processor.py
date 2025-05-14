"""
Service for processing data exchange requests in the Food Department adapter.
"""
import json
import uuid
import datetime
import logging
from pathlib import Path
from sqlalchemy import select, update

from app.db.models import SessionLocal, request_tracker
from app.db.session import get_db_connection
from app.core.config import RESULTS_DIR, BATCH_SIZE

logger = logging.getLogger(__name__)

def calculate_string_similarity(str1, str2):
    """
    Calculate a simple string similarity score (0.0 to 1.0).
    """
    if not str1 or not str2:
        return 0.0
    
    str1 = str1.lower()
    str2 = str2.lower()
    
    # If strings are identical
    if str1 == str2:
        return 1.0
    
    # Compute Levenshtein distance (simplified approach)
    distance = sum(c1 != c2 for c1, c2 in zip(str1, str2)) + abs(len(str1) - len(str2))
    max_len = max(len(str1), len(str2))
    
    # Convert to similarity score
    similarity = 1.0 - (distance / max_len)
    return max(0.0, similarity)

async def process_request(request_data):
    """
    Processes a request based on its type (verify or search).
    """
    logger.info("Processing request")
    try:
        header = request_data.get('request_payload', {}).get('header', {})
        if not header:
            raise ValueError("Invalid request format: missing header")
        
        request_type = header["request_type"]        
        if request_type == "verify":
            await process_verify_request(request_data)
        elif request_type == "search":
            await process_search_request(request_data)
        else:
            logger.error(f"Unknown request type: {request_type}")
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "header": {
                "status": "failed",
                "error": str(e)
            }
        }
    return {
        "header": {
            "status": "completed"
        }
    }

async def process_verify_request(request_data):
    """
    Processes an inclusion request (verifying citizens against criteria).
    """
    logger.info("Processing inclusion request")
    try:
        request = request_data.get('request_payload', {})
        header = request["header"]
        body = request["body"]
        request_id = header["request_id"]
        tenant_id = header["tenant_id"]
        
        # Create directory for results
        result_dir = RESULTS_DIR / request_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # Update status to processing
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(status="processing")
        )
        session.commit()
        session.close()
        
        # Extract citizens and criteria
        citizens = body.get("citizens", [])
        criteria = body.get("criteria", [])
        
        # Process citizens
        results = []
        
        # Connect to the database
        connection = get_db_connection()
        
        for citizen in citizens:
            # Determine matching strategy
            if "aadhar" in citizen and citizen["aadhar"]:
                # Scenario 1: Match by aadhar (match_score = 1.00)
                with connection.cursor() as cursor:
                    # Query food ration database for matching citizen
                    cursor.execute(f"SELECT * FROM citizens WHERE aadhar = %s", (citizen["aadhar"],))
                    matched_citizen = cursor.fetchone()
                    
                    if matched_citizen:
                        # Evaluate criteria
                        criteria_results = []
                        for criterion in criteria:
                            field = criterion["field"]
                            operator = criterion["operator"]
                            value = criterion["value"]
                            
                            # Check if the field exists in the matched citizen
                            if field in matched_citizen:
                                match = False
                                
                                # Evaluate based on operator
                                if operator == "=":
                                    if isinstance(matched_citizen[field], str) and isinstance(value, str):
                                        match = matched_citizen[field].lower() == value.lower()
                                    else:
                                        match = matched_citizen[field] == value
                                elif operator == ">":
                                    match = matched_citizen[field] > value
                                elif operator == "<":
                                    match = matched_citizen[field] < value
                                
                                criteria_results.append({
                                    "field": field,
                                    "match": match
                                })
                        
                        # Add to results with match_score = 1.00
                        results.append({
                            "aadhar": citizen["aadhar"],
                            "criteria_results": criteria_results,
                            "match_score": 1.00
                        })
                    else:
                        # No match found
                        results.append({
                            "aadhar": citizen["aadhar"],
                            "criteria_results": [],
                            "match_score": 0.00
                        })
            else:
                # Scenario 2: Probabilistic matching
                with connection.cursor() as cursor:
                    # Build a query based on attributes
                    query_parts = []
                    params = []
                    
                    if "name" in citizen and citizen["name"]:
                        query_parts.append("name LIKE %s")
                        params.append(f"{citizen['name']}%")
                    
                    if "age" in citizen and citizen["age"]:
                        query_parts.append("ABS(age - %s) <= 2")
                        params.append(citizen["age"])
                    
                    if "gender" in citizen and citizen["gender"]:
                        query_parts.append("gender = %s")
                        params.append(citizen["gender"])
                    
                    if "caste" in citizen and citizen["caste"]:
                        query_parts.append("caste = %s")
                        params.append(citizen["caste"])
                    
                    if "location" in citizen and citizen["location"]:
                        query_parts.append("location LIKE %s")
                        params.append(f"{citizen['location']}%")
                    
                    if query_parts:
                        query = f"SELECT * FROM citizens WHERE {' AND '.join(query_parts)} LIMIT 1"
                        cursor.execute(query, params)
                        matched_citizen = cursor.fetchone()
                        
                        if matched_citizen:
                            # Calculate match score based on fields
                            match_score = 0.0
                            
                            # Name match (50%)
                            if "name" in citizen and "name" in matched_citizen:
                                name_similarity = calculate_string_similarity(
                                    citizen["name"], matched_citizen["name"]
                                )
                                match_score += 0.5 * name_similarity
                            
                            # Age match (30%)
                            if "age" in citizen and "age" in matched_citizen:
                                age_diff = abs(citizen["age"] - matched_citizen["age"])
                                age_similarity = max(0, 1 - (age_diff / 10))  # Allow up to 10 years difference
                                match_score += 0.3 * age_similarity
                            
                            # Gender match (20%)
                            if "gender" in citizen and "gender" in matched_citizen:
                                gender_match = 1 if citizen["gender"].lower() == matched_citizen["gender"].lower() else 0
                                match_score += 0.2 * gender_match
                            
                            # Only consider matches with score > 0.8
                            if match_score > 0.8:
                                # Evaluate criteria
                                criteria_results = []
                                for criterion in criteria:
                                    field = criterion["field"]
                                    operator = criterion["operator"]
                                    value = criterion["value"]
                                    
                                    if field in matched_citizen:
                                        match = False
                                        
                                        if operator == "=":
                                            if isinstance(matched_citizen[field], str) and isinstance(value, str):
                                                match = matched_citizen[field].lower() == value.lower()
                                            else:
                                                match = matched_citizen[field] == value
                                        elif operator == ">":
                                            match = matched_citizen[field] > value
                                        elif operator == "<":
                                            match = matched_citizen[field] < value
                                        
                                        criteria_results.append({
                                            "field": field,
                                            "match": match
                                        })
                                
                                # Add to results with calculated match_score (but less than 1.00)
                                results.append({
                                    "name": citizen.get("name", ""),
                                    "age": citizen.get("age", 0),
                                    "gender": citizen.get("gender", ""),
                                    "caste": citizen.get("caste", ""),
                                    "location": citizen.get("location", ""),
                                    "criteria_results": criteria_results,
                                    "match_score": min(0.99, match_score)  # Cap at 0.99 to indicate probabilistic
                                })
                            else:
                                # Match score too low
                                results.append({
                                    "name": citizen.get("name", ""),
                                    "age": citizen.get("age", 0),
                                    "gender": citizen.get("gender", ""),
                                    "criteria_results": [],
                                    "match_score": match_score
                                })
                        else:
                            # No match found
                            results.append({
                                "name": citizen.get("name", ""),
                                "age": citizen.get("age", 0),
                                "gender": citizen.get("gender", ""),
                                "criteria_results": [],
                                "match_score": 0.00
                            })
        
        connection.close()
        
        # Prepare response
        response_data = {
            "header": {
                "request_id": request_id,
                "request_type": "verify",
                "tenant_id": tenant_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "completed",
                "part": 1,
                "has_more_parts": False
            },
            "body": {
                "results": results
            }
        }
        
        # Save results to file
        result_file = result_dir / "1.json"

        # Encrypt and save to file
        from app.utils.common import encrypt_and_save_to_file
        encrypt_and_save_to_file(response_data, result_file)
        logger.info(f"Written result file: {result_file} with records")


        # Update tracker with completed status and file list
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(
                status="completed",
                files=json.dumps([f"/results/{request_id}/1.json"])
            )
        )
        session.commit()
        session.close()
        
        logger.info(f"verify request {request_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing verify request: {str(e)}")
        
        # Update tracker with error
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(
                status="failed",
                error=str(e)
            )
        )
        session.commit()
        session.close()

async def process_search_request(request_data):
    """
    Processes an search_jobs request (searching for citizens matching criteria).
    """
    logger.info("Processing search request")
    try:
        request = request_data.get('request_payload', {})
        header = request["header"]
        body = request["body"]
        request_id = header["request_id"]
        tenant_id = header["tenant_id"]
        
        # Create directory for results
        result_dir = RESULTS_DIR / request_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # Update status to processing
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(status="processing")
        )
        session.commit()
        session.close()
        
        # Extract criteria
        criteria = body.get("criteria", [])
        
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Build SQL query based on criteria
        query_parts = []
        params = []
        
        for criterion in criteria:
            field = criterion["field"]
            operator = criterion["operator"]
            value = criterion["value"]
            
            if operator == "=":
                query_parts.append(f"{field} = %s")
            elif operator == ">":
                query_parts.append(f"{field} > %s")
            elif operator == "<":
                query_parts.append(f"{field} < %s")
            
            params.append(value)
        
        where_clause = " AND ".join(query_parts) if query_parts else "1=1"
        query = f"SELECT name, aadhar, phone_number FROM citizens WHERE {where_clause}"
        
        # Fetch last processed index from request_tracker
        last_index = 0
        files = []

        session = SessionLocal()
        result = session.execute(
            select(request_tracker.c.last_processed_index, request_tracker.c.files)
            .where(request_tracker.c.request_id == request_id)
        ).fetchone()
        session.close()

        if result:
            if result[0] is not None:
                last_index = result[0]
            if result[1]:
                try:
                    files = json.loads(result[1])
                except json.JSONDecodeError:
                    files = []

        logger.info(f"Resuming from last_processed_index: {last_index}, existing files: {len(files)}")

        batch_size = BATCH_SIZE
        file_index = (last_index // batch_size) + 1
        has_more = True

        # Remove LIMIT and OFFSET from query, handle batching via fetchmany and cursor scroll
        logger.debug(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        if last_index > 0:
            try:
                cursor.scroll(last_index, mode='absolute')
            except Exception as e:
                logger.warning(f"Unable to scroll to last_index {last_index}: {e}")
                return

        while has_more:
            batch = cursor.fetchmany(batch_size)

            if not batch:
                has_more = False
                continue

            # Prepare response for this batch
            response_data = {
                "header": {
                    "request_id": request_id,
                    "request_type": "search",
                    "tenant_id": tenant_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "completed",
                    "part": file_index,
                    "has_more_parts": True  # will be corrected after loop
                },
                "body": {
                    "citizens": batch
                }
            }

            # Encrypt and save to file
            from app.utils.common import encrypt_and_save_to_file
            result_file = result_dir / f"{file_index}.json"
            encrypt_and_save_to_file(response_data, result_file)
            logger.info(f"Written result file: {result_file} with {len(batch)} records")

            files.append(f"/results/{request_id}/{file_index}.json")
            file_index += 1
            last_index += len(batch)

            # Update tracker with current list of files after every batch
            session = SessionLocal()
            session.execute(
                update(request_tracker)
                .where(request_tracker.c.request_id == request_id)
                .values(
                    last_processed_index=last_index,
                    files=json.dumps(files)
                )
            )
            session.commit()
            session.close()
            logger.debug(f"Updated tracker with {len(files)} files and last_processed_index {last_index}")

        if files:
            from app.utils.common import decrypt_file
            response_path = result_dir / f"{file_index - 1}.json"

            # Decrypt the file first
            decrypted_content = decrypt_file(response_path)

            # Update has_more_parts flag
            decrypted_content["header"]["has_more_parts"] = False

            # Re-encrypt and save it again
            from app.utils.common import encrypt_and_save_to_file
            encrypt_and_save_to_file(decrypted_content, response_path)

        cursor.close()
        connection.close()
        
        # Update tracker with completed status (files already updated in batching)
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(
                status="completed"
            )
        )
        session.commit()
        session.close()
        
        logger.info(f"search_jobs request {request_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing search_jobs request: {str(e)}")
        
        # Update tracker with error
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(
                status="failed",
                error=str(e)
            )
        )
        session.commit()
        session.close()