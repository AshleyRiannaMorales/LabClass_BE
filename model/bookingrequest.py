from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db

BookingRequestRouter = APIRouter(tags=["Booking Requests"])

# CRUD operations for booking requests

@BookingRequestRouter.get("/booking-requests/", response_model=list)
async def read_booking_requests(
    db=Depends(get_db)
):
    query = "SELECT * FROM booking_request"
    db[0].execute(query)
    booking_requests = [{
        "bookingRequestID": booking[0],
        "instructorID": booking[1],
        "computerLabID": booking[2],
        "bookingDate": booking[3],
        "bookingStartTime": booking[4],
        "bookingEndTime": booking[5],
        "bookingPurpose": booking[6],
        "bookingReqStatus": booking[7],  # Include booking status
        "adminID": booking[8]  # Include admin ID
    } for booking in db[0].fetchall()]
    return booking_requests

@BookingRequestRouter.get("/booking-requests/{booking_request_id}", response_model=dict)
async def read_booking_request(
    booking_request_id: int, 
    db=Depends(get_db)
):
    query = "SELECT * FROM booking_request WHERE bookingRequestID = %s"
    db[0].execute(query, (booking_request_id,))
    booking_request = db[0].fetchone()
    if booking_request:
        return {
            "bookingRequestID": booking_request[0],
            "instructorID": booking_request[1],
            "computerLabID": booking_request[2],
            "bookingDate": booking_request[3],
            "bookingStartTime": booking_request[4],
            "bookingEndTime": booking_request[5],
            "bookingPurpose": booking_request[6],
            "bookingReqStatus": booking_request[7],  # Include booking status
            "adminID": booking_request[8]  # Include admin ID
        }
    raise HTTPException(status_code=404, detail="Booking request not found")


@BookingRequestRouter.post("/booking-requests/", response_model=dict)
async def create_booking_request(
    instructorID: int = Form(...),
    computer_lab_id: int = Form(...),
    booking_date: str = Form(...),
    booking_start_time: str = Form(...),
    booking_end_time: str = Form(...),
    booking_purpose: str = Form(...),
    db=Depends(get_db)
):
    # Set default values
    booking_req_status = 'Pending'
    
    # Insert the booking request into the database
    query = """
        INSERT INTO booking_request 
        (instructorID, computerLabID, bookingDate, bookingStartTime, bookingEndTime, bookingPurpose, bookingReqStatus) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    db[0].execute(query, (instructorID, computer_lab_id, booking_date, booking_start_time, booking_end_time, booking_purpose, booking_req_status))
    db[1].commit()

    # Retrieve the last inserted ID using LAST_INSERT_ID()
    db[0].execute("SELECT LAST_INSERT_ID()")
    new_booking_request_id = db[0].fetchone()[0]

    return {"bookingRequestID": new_booking_request_id}


@BookingRequestRouter.put("/booking-requests/{booking_request_id}", response_model=dict)
async def update_booking_request(
    booking_request_id: int,
    instructorID: int = Form(...),
    computer_lab_id: int = Form(...),
    booking_date: str = Form(...),
    booking_start_time: str = Form(...),
    booking_end_time: str = Form(...),
    booking_purpose: str = Form(...),
    booking_req_status: str = Form(...),
    db=Depends(get_db)
):
    # Update the booking request in the database
    query = """
        UPDATE booking_request 
        SET instructorID = %s, computerLabID = %s, 
            bookingDate = %s, bookingStartTime = %s, bookingEndTime = %s, 
            bookingPurpose = %s, bookingReqStatus = %s
        WHERE bookingRequestID = %s
    """
    db[0].execute(query, (instructorID, computer_lab_id, booking_date, booking_start_time, booking_end_time, booking_purpose, booking_req_status, booking_request_id))
    db[1].commit()

    return {"message": "Booking request updated successfully"}


@BookingRequestRouter.delete("/booking-requests/{booking_request_id}", response_model=dict)
async def delete_booking_request(
    booking_request_id: int,
    db=Depends(get_db)
):
    query = "DELETE FROM booking_request WHERE bookingRequestID = %s"
    db[0].execute(query, (booking_request_id,))
    db[1].commit()

    return {"message": "Booking request deleted successfully"}