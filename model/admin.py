from fastapi import Depends, HTTPException, APIRouter, Form
from fastapi import HTTPException, status
from mysql.connector import errors
from .db import get_db
import bcrypt  
import logging
from datetime import timedelta 
from pydantic import BaseModel


AdminRouter = APIRouter(tags=["Admin"])
logger = logging.getLogger(__name__)

def format_time_from_duration(duration_str):
    """
    Convert a duration string (e.g., 'PT9H' or 'PT7H30M') or timedelta object
    into a formatted time string (e.g., '09:00' or '07:30').
    """
    if isinstance(duration_str, str) and duration_str.startswith("PT"):
        # If duration_str is a string and starts with 'PT', parse it as a timedelta
        duration = timedelta()
        for part in duration_str[2:].split('H'):
            if part.endswith('M'):
                duration += timedelta(minutes=int(part[:-1]))
            else:
                duration += timedelta(hours=int(part))
        
        # Format the timedelta as a time string
        hours, remainder = divmod(duration.seconds // 3600, 1)
        minutes = remainder * 60
        return f"{int(hours):02}:{int(minutes):02}"
    
    elif isinstance(duration_str, timedelta):
        # If duration_str is already a timedelta object, format it as a time string
        hours, remainder = divmod(duration_str.seconds // 3600, 1)
        minutes = remainder * 60
        return f"{int(hours):02}:{int(minutes):02}"

    return str(duration_str)  # Return the original value as string if not recognized


# CRUD operations for admin

@AdminRouter.get("/admin/", response_model=list)
async def read_admins(
    db=Depends(get_db)
):
    query = "SELECT adminID FROM admin"
    db[0].execute(query)
    admins = [{"adminID": admin[0]} for admin in db[0].fetchall()]
    return admins

@AdminRouter.get("/get/instructors/", response_model=list)
async def read_instructors(db=Depends(get_db)):
    query = "SELECT instructorID, instructorEmail, InstructorFirstName, InstructorLastName, InstructorMiddleName FROM instructor"
    db[0].execute(query)
    instructors = [
        {
            "instructorID": instructor[0],
            "instructorEmail": instructor[1],
            "InstructorFirstName": instructor[2],
            "InstructorLastName": instructor[3],
            "InstructorMiddleName": instructor[4]
        }
        for instructor in db[0].fetchall()
    ]
    return instructors

@AdminRouter.get("/admin/view/instructor_accounts/", response_model=list)
async def read_instructor_accounts(db=Depends(get_db)):
    try:
        query = """
            SELECT 
                ia.instructorID, 
                CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName, 
                i.instructorEmail,
                ia.instructorPassword, 
                ia.passwordLastUpdated 
            FROM 
                instructor_accounts ia
            JOIN 
                instructor i 
            ON 
                ia.instructorID = i.instructorID
        """
        db[0].execute(query)
        accounts = [
            {
                "instructorID": account[0],
                "instructorName": account[1],
                "instructorName": account[2],
                "instructorPassword": account[3],
                "passwordLastUpdated": account[4]
            }
            for account in db[0].fetchall()
        ]
        return accounts
    except Exception as e:
        logger.exception("Error fetching instructor accounts: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


@AdminRouter.post("/admin/create", response_model=dict)
async def create_admin(
    admin_id: int = Form(...),
    admin_pass: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Hash the password using bcrypt
        hashed_password = hash_password(admin_pass)

        # Check if the admin with the provided ID already exists
        query_check_admin = "SELECT adminID FROM admin WHERE adminID = %s"
        db[0].execute(query_check_admin, (admin_id,))
        existing_admin = db[0].fetchone()

        if existing_admin:
            raise HTTPException(status_code=400, detail="Admin with this ID already exists")

        # Insert the admin details into the database
        query_insert_admin = "INSERT INTO admin (adminID, adminPass) VALUES (%s, %s)"
        db[0].execute(query_insert_admin, (admin_id, hashed_password))
        db[1].commit()

        return {"message": "Admin created successfully"}
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error creating admin: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


@AdminRouter.post("/login/admin", response_model=dict)
async def admin_login(
    admin_id: int = Form(...), 
    admin_pass: str = Form(...), 
    db=Depends(get_db)
):
    try:
        # Hash the provided password
        hashed_password = hash_password(admin_pass)

        # Check if admin ID and hashed password match in the database
        query = "SELECT adminID, adminPass FROM admin WHERE adminID = %s"
        db[0].execute(query, (admin_id,))
        admin_data = db[0].fetchone()

        if admin_data:
            stored_password = admin_data[1]
            if bcrypt.checkpw(admin_pass.encode('utf-8'), stored_password.encode('utf-8')):
                return {"adminID": admin_data[0], "message": "Log In Successful"}
            else:
                raise HTTPException(status_code=401, detail="Incorrect password provided")
        else:
            raise HTTPException(status_code=404, detail="Admin account does not exist with the provided ID")
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error logging in admin: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
        
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found or credentials do not match.")

        # Hash the default password using bcrypt
        hashed_password = hash_password(defaultPassword)

        # Insert the instructor account details into the instructor_accounts table
        query_insert_instructor_account = """
            INSERT INTO instructor_accounts (instructorID, instructorPassword)
            VALUES (%s, %s)
        """
        db[0].execute(query_insert_instructor_account, (instructorID, hashed_password))
        db[1].commit()

        return {"message": "Instructor account created successfully."}
    except errors.IntegrityError as e:
        if e.errno == 1062:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Instructor account already created.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database integrity error.")
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error creating instructor account: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred.")
    
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
async def reject_booking_request(
    booking_request_id: int,
    reason: str = Form(...),  # Add this parameter to accept the rejection reason
    db=Depends(get_db)
):
    try:
        # Update booking request status to 'Rejected' and set the rejection reason
        query_reject = """
            UPDATE booking_request 
            SET bookingReqStatus = 'Rejected', rejectReason = %s 
            WHERE bookingRequestID = %s
        """
        db[0].execute(query_reject, (reason, booking_request_id))
        db[1].commit()

        return {"message": "Booking request rejected successfully."}
    except Exception as e:
        logger.exception("Error rejecting booking request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


 
@AdminRouter.put("/admin/{admin_id}", response_model=dict)
async def update_admin(
    admin_id: int,
    admin_pass: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Hash the provided password
        hashed_password = hash_password(admin_pass)

        # Update admin information in the database 
        query = "UPDATE admin SET adminPass = %s WHERE adminID = %s"
        db[0].execute(query, (hashed_password, admin_id))

        # Check if the update was successful
        if db[0].rowcount > 0:
            db[1].commit()
            return {"message": "Admin updated successfully"}
        
        # If no rows were affected, admin not found
        raise HTTPException(status_code=404, detail="Admin not found")
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error updating admin: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

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

        # Password hashing function using bcrypt
def hash_password(password: str):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Decode bytes to string for storage

#admin old pass: admin123
#new admin pass: UICAdmin2024