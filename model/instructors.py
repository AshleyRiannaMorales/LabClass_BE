from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import bcrypt
import logging

InstructorsRouter = APIRouter(tags=["Instructors"])
logger = logging.getLogger(__name__)

# CRUD operations for instructors

@InstructorsRouter.get("/instructors/", response_model=list)
async def read_instructors(
    db=Depends(get_db)
):
    query = "SELECT instructorID, instructorEmail, instructorUsername, instructorFName, instructorLName FROM instructor"
    db[0].execute(query)
    instructors = [{"instructorID": instructor[0], "instructorEmail": instructor[1], 
                    "instructorUsername": instructor[2], "instructorFName": instructor[3], 
                    "instructorLName": instructor[4]} for instructor in db[0].fetchall()]
    return instructors

@InstructorsRouter.post("/signup/instructors", response_model=dict)
async def instructor_signup(
    email: str = Form(...), 
    username: str = Form(...), 
    fname: str = Form(...),
    lname: str = Form(...),
    password: str = Form(...), 
    db=Depends(get_db)
):
    try:
        # Check if email already exists
        db[0].execute("SELECT * FROM instructor WHERE instructorEmail = %s", (email,))
        existing_email = db[0].fetchone()
        if existing_email:
            raise HTTPException(status_code=422, detail="Email already exists")

        # Validate password strength
        if len(password) < 8:
            raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")

        # Insert the instructor data into the database
        query = "INSERT INTO instructor (instructorEmail, instructorUsername, instructorFName, instructorLName, instructorPass) VALUES (%s, %s, %s, %s, %s)"
        db[0].execute(query, (email, username, fname, lname, password))

        # Retrieve the last inserted ID using LAST_INSERT_ID()
        db[0].execute("SELECT LAST_INSERT_ID()")
        new_instructor_id = db[0].fetchone()[0]
        db[1].commit()

        # Return success response
        return {
            "instructorID": new_instructor_id,
            "instructorEmail": email,
            "instructorUsername": username,
            "instructorFName": fname,
            "instructorLName": lname
        }
    except Exception as e:
        logger.exception("Error during instructor signup: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


@InstructorsRouter.post("/login/instructor", response_model=dict, tags=["Instructors"])
async def instructor_login(
    instructor_email: str = Form(...), 
    instructor_pass: str = Form(...), 
    db=Depends(get_db)
):
    query = "SELECT instructorID, instructorEmail, instructorUsername, instructorFName, instructorLName FROM instructor WHERE instructorEmail = %s AND instructorPass = %s"
    db[0].execute(query, (instructor_email, instructor_pass))
    instructor = db[0].fetchone()
    if instructor:
        return {
            "instructorID": instructor[0], 
            "instructorEmail": instructor[1], 
            "instructorUsername": instructor[2], 
            "instructorFName": instructor[3], 
            "instructorLName": instructor[4],
            "message": "Log In Successful"
        }
    raise HTTPException(status_code=404, detail="Instructor not found")

@InstructorsRouter.put("/instructors/{instructor_id}", response_model=dict)
async def update_instructor(
    instructor_id: int,
    email: str = Form(...),
    username: str = Form(...),
    fname: str = Form(...),
    lname: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    # Update instructor information in the database 
    query = "UPDATE instructor SET instructorEmail = %s, instructorUsername = %s, instructorFName = %s, instructorLName = %s, instructorPass = %s WHERE instructorID = %s"
    db[0].execute(query, (email, username, fname, lname, password, instructor_id))

    # Check if the update was successful
    if db[0].rowcount > 0:
        db[1].commit()
        return {"message": "Instructor updated successfully"}
    
    # If no rows were affected, instructor not found
    raise HTTPException(status_code=404, detail="Instructor not found")

@InstructorsRouter.delete("/instructors/{instructor_id}", response_model=dict)
async def delete_instructor(
    instructor_id: int,
    db=Depends(get_db)
):
    try:
        # Check if the instructor exists
        query_check_instructor = "SELECT instructorID FROM instructor WHERE instructorID = %s"
        db[0].execute(query_check_instructor, (instructor_id,))
        existing_instructor = db[0].fetchone()

        if not existing_instructor:
            raise HTTPException(status_code=404, detail="Instructor not found")

        # Delete the instructor
        query_delete_instructor = "DELETE FROM instructor WHERE instructorID = %s"
        db[0].execute(query_delete_instructor, (instructor_id,))
        db[1].commit()

        return {"message": "Instructor deleted successfully"}
    except Exception as e:
        # Handle other exceptions if necessary
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        # Close the database cursor
        db[0].close()