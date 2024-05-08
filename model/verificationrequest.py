from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import logging

VerificationRequests = APIRouter(tags=["Verification Requests"])
logger = logging.getLogger(__name__)


@VerificationRequests.get("/all_verification_request", response_model=list)
async def get_all_verification_requests(
    db=Depends(get_db)
):
    try:
        # Query the database for pending verification requests
        query = """
            SELECT requestID, instructorID, instructorEmail, CONCAT(instructorFirstName, " ", instructorLastName) AS instructorName, status,
            created_at, updated_at
            FROM verification_requests
        """
        db[0].execute(query)
        all_verifreq = [
            {
                "requestID": request[0],
                "instructorID": request[1],
                "instructorEmail": request[2],
                "instructorName": request[3],
                "status": request[4],
                "created_at": request[5],
                "updated_at": request[6]
            }
            for request in db[0].fetchall()
        ]
        return all_verifreq
    
    except Exception as e:
        logger.exception("Error retrieving pending verification requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@VerificationRequests.get("/new_verification_request", response_model=list)
async def get_new_verification_requests(
    db=Depends(get_db)
):
    try:
        # Query the database for pending verification requests
        query = """
            SELECT requestID, instructorID, instructorEmail, CONCAT(instructorFirstName, " ", instructorLastName) AS instructorName, status,
            created_at, updated_at
            FROM verification_requests ORDER BY requestID DESC
        """
        db[0].execute(query)
        new_verifreq = [
            {
                "requestID": request[0],
                "instructorID": request[1],
                "instructorEmail": request[2],
                "instructorName": request[3],
                "status": request[4],
                "created_at": request[5],
                "updated_at": request[6]
            }
            for request in db[0].fetchall()
        ]
        return new_verifreq
    
    except Exception as e:
        logger.exception("Error retrieving pending verification requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@VerificationRequests.get("/old_verification_request", response_model=list)
async def get_old_verification_requests(
    db=Depends(get_db)
):
    try:
        # Query the database for pending verification requests
        query = """
            SELECT requestID, instructorID, instructorEmail, CONCAT(instructorFirstName, " ", instructorLastName) AS instructorName, status,
            created_at, updated_at
            FROM verification_requests ORDER BY requestID ASC
        """
        db[0].execute(query)
        old_verifreq = [
            {
                "requestID": request[0],
                "instructorID": request[1],
                "instructorEmail": request[2],
                "instructorName": request[3],
                "status": request[4],
                "created_at": request[5],
                "updated_at": request[6]
            }
            for request in db[0].fetchall()
        ]
        return old_verifreq
    
    except Exception as e:
        logger.exception("Error retrieving pending verification requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
   
   
@VerificationRequests.get("/pending_verification", response_model=list)
async def get_pending_verification_requests(
    db=Depends(get_db)
):
    try:
        # Query the database for pending verification requests
        query = """
            SELECT requestID, instructorID, instructorEmail, CONCAT(instructorFirstName, " ", instructorLastName) AS instructorName
            FROM verification_requests WHERE status = 'pending'
        """
        db[0].execute(query)
        pending_requests = [
            {
                "requestID": request[0],
                "instructorID": request[1],
                "instructorEmail": request[2],
                "instructorName": request[3]
            }
            for request in db[0].fetchall()
        ]
        return pending_requests
    except Exception as e:
        logger.exception("Error retrieving pending verification requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@VerificationRequests.get("/approved_verification_request", response_model=list)
async def get_approved_verification_requests(
    db=Depends(get_db)
):
    try:
        # Query the database for approved verification requests
        query = """
            SELECT requestID, instructorID, instructorEmail, CONCAT(instructorFirstName, " ", instructorLastName) AS instructorName
            FROM verification_requests
            WHERE status = 'Approved'
        """
        db[0].execute(query)
        approved_verifreq = [
            {
                "requestID": request[0],
                "instructorID": request[1],
                "instructorEmail": request[2],
                "instructorName": request[3]
            }
            for request in db[0].fetchall()
        ]
        return approved_verifreq
    
    except Exception as e:
        logger.exception("Error retrieving approved verification requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")