from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import bcrypt
import logging

InstructorsRouter = APIRouter(tags=["Instructors"])
logger = logging.getLogger(__name__)

# CRUD operations for instructors

@InstructorsRouter.get("/instructors/", response_model=list)
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

@InstructorsRouter.post("/verify/instructor", response_model=dict)
async def verify_instructor_request(
    instructorID: int = Form(...),
    instructorEmail: str = Form(...),
    instructorFirstName: str = Form(...),
    instructorLastName: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Insert a new verification request into the verification_requests table
        query = """
            INSERT INTO verification_requests (
                instructorID, instructorEmail, instructorFirstName, instructorLastName
            ) VALUES (%s, %s, %s, %s)
        """
        db[0].execute(query, (instructorID, instructorEmail, instructorFirstName, instructorLastName))
        db[1].commit()

        return {"message": "Verification request submitted successfully."}
    except Exception as e:
        logger.exception("Error submitting verification request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
 
@InstructorsRouter.post("/instructor/login", response_model=dict)
async def instructor_login(
    IDorEmail: str = Form(...),  # Can be instructorID or instructorEmail
    password: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Check if the instructor with the provided identifier (instructorID or instructorEmail) exists
        query_check_instructor = """
    SELECT ia.instructorID, i.instructorEmail, ia.instructorPassword
    FROM instructor i
    INNER JOIN instructor_accounts ia ON i.instructorID = ia.instructorID
    WHERE i.instructorID = %s OR i.instructorEmail = %s
"""
        db[0].execute(query_check_instructor, (IDorEmail, IDorEmail))
        instructor_data = db[0].fetchone()

        if instructor_data:
            stored_password_hash = instructor_data[2]
            # Verify the provided password against the stored hashed password
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                return {
                    "message": "Login successful!",
                    "instructorID": instructor_data[0],
                    "instructorEmail": instructor_data[1]
                }
            else:
                raise HTTPException(status_code=401, detail="Incorrect password provided")
        else:
            raise HTTPException(status_code=404, detail="Instructor not found or credentials do not match.")
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error during instructor login: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@InstructorsRouter.put("/instructor/update_password", response_model=dict)
async def update_password(
    instructorID: int = Form(...),
    oldPassword: str = Form(...),
    newPassword: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Verify if the instructorID exists and retrieve the hashed password
        query_verify_password = """
            SELECT instructorPassword
            FROM instructor_accounts
            WHERE instructorID = %s
        """
        db[0].execute(query_verify_password, (instructorID,))
        stored_password_hash = db[0].fetchone()

        if not stored_password_hash:
            raise HTTPException(status_code=404, detail="Instructor not found.")

        # Extract the hashed password from the tuple
        stored_password_hash = stored_password_hash[0]

        # Check if the provided oldPassword matches the stored hashed password
        if not bcrypt.checkpw(oldPassword.encode('utf-8'), stored_password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Incorrect old password.")

        # Hash the new password before updating it in the database
        hashed_new_password = bcrypt.hashpw(newPassword.encode('utf-8'), bcrypt.gensalt())

        # Update the instructor's password with the new hashed password
        query_update_password = """
            UPDATE instructor_accounts
            SET instructorPassword = %s
            WHERE instructorID = %s
        """
        db[0].execute(query_update_password, (hashed_new_password, instructorID))
        db[1].commit()

        return {"message": "Password updated successfully."}
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error updating instructor password: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    finally:
        db[0].close()

        # Password hashing function using bcrypt
def hash_password(password: str):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Decode bytes to string for storage

#instructorID: 100000
#instructorPassword: old pass-yaco123
#instructorPassword: new pass-yaco12345