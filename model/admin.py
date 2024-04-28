from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import bcrypt
import logging


AdminRouter = APIRouter(tags=["Admin"])
logger = logging.getLogger(__name__)


# CRUD operations for admin

@AdminRouter.get("/admin/", response_model=list)
async def read_admins(
    db=Depends(get_db)
):
    query = "SELECT adminID FROM admin"
    db[0].execute(query)
    admins = [{"adminID": admin[0]} for admin in db[0].fetchall()]
    return admins


@AdminRouter.post("/login/admin", response_model=dict)
async def admin_login(
    admin_id: int = Form(...), 
    admin_pass: str = Form(...), 
    db=Depends(get_db)
):
    query = "SELECT adminID FROM admin WHERE adminID = %s AND adminPass = %s"
    db[0].execute(query, (admin_id, admin_pass))
    admin = db[0].fetchone()
    if admin:
        return {"adminID": admin[0], "message": "Log In Successful"}
    else:
        # Check if admin ID exists
        query_check_id = "SELECT adminID FROM admin WHERE adminID = %s"
        db[0].execute(query_check_id, (admin_id,))
        existing_id = db[0].fetchone()
        if not existing_id:
            raise HTTPException(status_code=404, detail="Admin account does not exist with the provided ID")
        else:
            raise HTTPException(status_code=401, detail="Incorrect password provided")
        
@AdminRouter.put("/admin/verify/instructor/{request_id}", response_model=dict)
async def verify_instructor(
    request_id: int,
    db=Depends(get_db)
):
    try:
        # Check if the verification request with the given request_id exists
        query_check_request = "SELECT status FROM verification_requests WHERE requestID = %s"
        db[0].execute(query_check_request, (request_id,))
        verification_request = db[0].fetchone()

        if not verification_request:
            raise HTTPException(status_code=404, detail="Verification request not found.")

        current_status = verification_request[0]  # Assuming status is the first (and only) column in the result

        if current_status == 'approved':
            return {"message": "Verification request is already approved."}

        # Update the status of the verification request to 'approved'
        query_update_status = "UPDATE verification_requests SET status = 'approved' WHERE requestID = %s"
        db[0].execute(query_update_status, (request_id,))
        db[1].commit()

        return {"message": "Instructor verified successfully."}
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error verifying instructor: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
   
   
@AdminRouter.get("/admin/pending_verification", response_model=list)
async def get_pending_verification_requests(
    db=Depends(get_db)
):
    try:
        # Query the database for pending verification requests
        query = """
            SELECT requestID, instructorID, instructorEmail, instructorFirstName, instructorLastName
            FROM verification_requests WHERE status = 'pending'
        """
        db[0].execute(query)
        pending_requests = [
            {
                "requestID": request[0],
                "instructorID": request[1],
                "instructorEmail": request[2],
                "instructorFirstName": request[3],
                "instructorLastName": request[4]
            }
            for request in db[0].fetchall()
        ]
        return pending_requests
    except Exception as e:
        logger.exception("Error retrieving pending verification requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@AdminRouter.post("/admin/create_instructor_account", response_model=dict)
async def create_instructor_account(
    instructorID: int = Form(...),
    instructorEmail: str = Form(...),
    defaultPassword: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Check if the instructor with the provided instructorID and instructorEmail exists
        query_check_instructor = """
            SELECT instructorID FROM instructor WHERE instructorID = %s AND instructorEmail = %s
        """
        db[0].execute(query_check_instructor, (instructorID, instructorEmail))
        instructor = db[0].fetchone()

        if not instructor:
            raise HTTPException(status_code=404, detail="Instructor not found or credentials do not match.")

        # Insert the instructor account details into the instructor_accounts table
        query_insert_instructor_account = """
            INSERT INTO instructor_accounts (instructorID, instructorPassword)
            VALUES (%s, %s)
        """
        db[0].execute(query_insert_instructor_account, (instructorID, defaultPassword))
        db[1].commit()

        return {"message": "Instructor account created successfully."}
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error creating instructor account: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@AdminRouter.put("/admin/approve-booking-request/{booking_request_id}", response_model=dict)
async def approve_booking_request(booking_request_id: int, db=Depends(get_db)):
    try:
        # Update booking request status to 'Approved'
        query_approve = "UPDATE booking_request SET bookingReqStatus = 'Approved' WHERE bookingRequestID = %s"
        db[0].execute(query_approve, (booking_request_id,))
        db[1].commit()

        return {"message": "Booking request approved successfully."}
    except Exception as e:
        logger.exception("Error approving booking request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@AdminRouter.put("/admin/reject-booking-request/{booking_request_id}", response_model=dict)
async def reject_booking_request(booking_request_id: int, db=Depends(get_db)):
    try:
        # Update booking request status to 'Rejected'
        query_reject = "UPDATE booking_request SET bookingReqStatus = 'Rejected' WHERE bookingRequestID = %s"
        db[0].execute(query_reject, (booking_request_id,))
        db[1].commit()

        return {"message": "Booking request rejected successfully."}
    except Exception as e:
        logger.exception("Error rejecting booking request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@AdminRouter.get("/admin/pending-booking-requests", response_model=list)
async def get_pending_booking_requests(db=Depends(get_db)):
    try:
        # Retrieve pending booking requests
        query_pending_requests = "SELECT * FROM booking_request WHERE bookingReqStatus = 'Pending'"
        db[0].execute(query_pending_requests)
        pending_requests = [{
            "bookingRequestID": request[0],
            "instructorID": request[1],
            "computerLabID": request[2],
            "bookingDate": request[3],
            "bookingStartTime": request[4],
            "bookingEndTime": request[5],
            "bookingPurpose": request[6]
        } for request in db[0].fetchall()]

        return pending_requests
    except Exception as e:
        logger.exception("Error retrieving pending booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@AdminRouter.get("/admin/approved-booking-requests", response_model=list)
async def get_approved_booking_requests(db=Depends(get_db)):
    try:
        # Retrieve approved booking requests
        query_approved_requests = "SELECT * FROM booking_request WHERE bookingReqStatus = 'Approved'"
        db[0].execute(query_approved_requests)
        approved_requests = [{
            "bookingRequestID": request[0],
            "instructorID": request[1],
            "computerLabID": request[2],
            "bookingDate": request[3],
            "bookingStartTime": request[4],
            "bookingEndTime": request[5],
            "bookingPurpose": request[6],
            "bookingReqStatus": request[7]
        } for request in db[0].fetchall()]

        return approved_requests
    except Exception as e:
        logger.exception("Error retrieving approved booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@AdminRouter.get("/admin/rejected-booking-requests", response_model=list)
async def get_rejected_booking_requests(db=Depends(get_db)):
    try:
        # Retrieve rejected booking requests
        query_rejected_requests = "SELECT * FROM booking_request WHERE bookingReqStatus = 'Rejected'"
        db[0].execute(query_rejected_requests)
        rejected_requests = [{
            "bookingRequestID": request[0],
            "instructorID": request[1],
            "computerLabID": request[2],
            "bookingDate": request[3],
            "bookingStartTime": request[4],
            "bookingEndTime": request[5],
            "bookingPurpose": request[6],
            "bookingReqStatus": request[7]
        } for request in db[0].fetchall()]

        return rejected_requests
    except Exception as e:
        logger.exception("Error retrieving rejected booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

 
@AdminRouter.put("/admin/{admin_id}", response_model=dict)
async def update_admin(
    admin_id: int,
    admin_pass: str = Form(...),
    db=Depends(get_db)
):
    # Update admin information in the database 
    query = "UPDATE admin SET adminPass = %s WHERE adminID = %s"
    db[0].execute(query, (admin_pass, admin_id))

    # Check if the update was successful
    if db[0].rowcount > 0:
        db[1].commit()
        return {"message": "Admin updated successfully"}
    
    # If no rows were affected, admin not found
    raise HTTPException(status_code=404, detail="Admin not found")

@AdminRouter.delete("/admin/{admin_id}", response_model=dict)
async def delete_admin(
    admin_id: int,
    db=Depends(get_db)
):
    try:
        # Check if the admin exists
        query_check_admin = "SELECT adminID FROM admin WHERE adminID = %s"
        db[0].execute(query_check_admin, (admin_id,))
        existing_admin = db[0].fetchone()

        if not existing_admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        # Delete the admin
        query_delete_admin = "DELETE FROM admin WHERE adminID = %s"
        db[0].execute(query_delete_admin, (admin_id,))
        db[1].commit()

        return {"message": "Admin deleted successfully"}
    except Exception as e:
        # Handle other exceptions if necessary
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        # Close the database cursor
        db[0].close()