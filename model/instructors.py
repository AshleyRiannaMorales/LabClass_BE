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
            SELECT instructorID, instructorEmail
            FROM instructor
            WHERE instructorID = %s OR instructorEmail = %s
        """
        db[0].execute(query_check_instructor, (IDorEmail, IDorEmail))
        instructor = db[0].fetchone()

        if not instructor:
            raise HTTPException(status_code=404, detail="Instructor not found or credentials do not match.")

        # Retrieve the instructorID and instructorEmail from the query result
        instructorID = instructor[0]
        instructorEmail = instructor[1]

        # Query the instructor_accounts table to get the stored password
        query_get_password = """
            SELECT instructorPassword
            FROM instructor_accounts
            WHERE instructorID = %s
        """
        db[0].execute(query_get_password, (instructorID,))
        stored_password = db[0].fetchone()

        if not stored_password:
            raise HTTPException(status_code=500, detail="Password not found for the instructor.")

        # Check if the provided password matches the stored password
        if password != stored_password[0]:
            raise HTTPException(status_code=401, detail="Incorrect password provided.")

        return {"message": "Login successful!", "instructorID": instructorID, "instructorEmail": instructorEmail}
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
        # Verify if the instructorID and oldPassword match
        query_verify_password = """
            SELECT instructorPassword
            FROM instructor_accounts
            WHERE instructorID = %s
        """
        db[0].execute(query_verify_password, (instructorID,))
        stored_password = db[0].fetchone()

        if not stored_password:
            raise HTTPException(status_code=404, detail="Instructor not found.")

        # Check if the provided oldPassword matches the stored password
        if oldPassword != stored_password[0]:
            raise HTTPException(status_code=401, detail="Incorrect old password.")

        # Update the instructor's password with the new password
        query_update_password = """
            UPDATE instructor_accounts
            SET instructorPassword = %s
            WHERE instructorID = %s
        """
        db[0].execute(query_update_password, (newPassword, instructorID))
        db[1].commit()

        return {"message": "Password updated successfully."}
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error updating instructor password: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    finally:
        db[0].close()