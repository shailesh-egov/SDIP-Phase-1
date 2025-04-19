"""
Service for processing data exchange requests in the Food Department adapter.
"""
import json
import uuid
import datetime
from pathlib import Path
from sqlalchemy import select, update

from app.db.models import SessionLocal, request_tracker
from app.db.session import get_db_connection
from app.core.config import RESULTS_DIR

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

async def process_inclusion_request(request_data):
    """
    Processes an inclusion request (verifying citizens against criteria).
    """
    try:
        header = request_data["header"]
        body = request_data["body"]
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
                "request_type": "inclusion",
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
        with open(result_file, "w") as f:
            json.dump(response_data, f, indent=2)
        
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
        
        print(f"Inclusion request {request_id} processed successfully")
        
    except Exception as e:
        print(f"Error processing inclusion request: {str(e)}")
        
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

async def process_exclusion_request(request_data):
    """
    Processes an exclusion request (searching for citizens matching criteria).
    """
    try:
        header = request_data["header"]
        body = request_data["body"]
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
        query = f"SELECT * FROM citizens WHERE {where_clause}"
        
        # Execute query
        cursor.execute(query, params)
        
        # Process results in batches
        batch_size = 10000
        file_index = 1
        files = []
        has_more = True
        
        while has_more:
            batch = cursor.fetchmany(batch_size)
            
            if not batch:
                has_more = False
                continue
            
            # Prepare response for this batch
            response_data = {
                "header": {
                    "request_id": request_id,
                    "request_type": "exclusion",
                    "tenant_id": tenant_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "completed",
                    "part": file_index,
                    "has_more_parts": has_more
                },
                "body": {
                    "citizens": batch
                }
            }
            
            # Save results to file
            result_file = result_dir / f"{file_index}.json"
            with open(result_file, "w") as f:
                json.dump(response_data, f, indent=2)
            
            files.append(f"/results/{request_id}/{file_index}.json")
            file_index += 1
        
        cursor.close()
        connection.close()
        
        # Update tracker with completed status and file list
        session = SessionLocal()
        session.execute(
            update(request_tracker)
            .where(request_tracker.c.request_id == request_id)
            .values(
                status="completed",
                files=json.dumps(files)
            )
        )
        session.commit()
        session.close()
        
        print(f"Exclusion request {request_id} processed successfully")
        
    except Exception as e:
        print(f"Error processing exclusion request: {str(e)}")
        
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