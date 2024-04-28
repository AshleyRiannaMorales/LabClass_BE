# model/bookingrequest.py
from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import logging

BookingRequestRouter = APIRouter(tags=["Booking Requests"])
logger = logging.getLogger(__name__)

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
    } for booking in db[0].fetchall()]
    return booking_requests

@BookingRequestRouter.get("/booking-requests/newest-to-oldest", response_model=list)
async def read_booking_requests_from_newest_to_oldest(db=Depends(get_db)):
    try:
        # Retrieve booking requests sorted by creation date/time (newest to oldest)
        query = """
            SELECT * FROM booking_request
            ORDER BY bookingRequestID DESC
        """
        db[0].execute(query)
        booking_requests = [{
            "bookingRequestID": booking[0],
            "instructorID": booking[1],
            "computerLabID": booking[2],
            "bookingDate": booking[3],
            "bookingStartTime": booking[4],
            "bookingEndTime": booking[5],
            "bookingPurpose": booking[6],
            "bookingReqStatus": booking[7]
        } for booking in db[0].fetchall()]

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@BookingRequestRouter.get("/booking-requests/oldest-to-newest", response_model=list[dict])
async def read_booking_requests_from_oldest_to_newest(db=Depends(get_db)):
    try:
        # Retrieve booking requests sorted by creation date/time (oldest to newest)
        query = """
            SELECT * FROM booking_request
            ORDER BY bookingRequestID ASC
        """
        db[0].execute(query)
        booking_requests = [{
            "bookingRequestID": booking[0],
            "instructorID": booking[1],
            "computerLabID": booking[2],
            "bookingDate": booking[3],
            "bookingStartTime": booking[4],
            "bookingEndTime": booking[5],
            "bookingPurpose": booking[6],
            "bookingReqStatus": booking[7]
        } for booking in db[0].fetchall()]

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

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
    db=Depends(get_db)
):
    try:
        # Retrieve the current status of the booking request
        query_get_status = "SELECT bookingReqStatus FROM booking_request WHERE bookingRequestID = %s"
        db[0].execute(query_get_status, (booking_request_id,))
        current_status = db[0].fetchone()

        if not current_status:
            raise HTTPException(status_code=404, detail="Booking request not found")

        current_status = current_status[0]

        if current_status != "Pending":
            # If the current status is not Pending, reset it to Pending
            query_reset_status = "UPDATE booking_request SET bookingReqStatus = 'Pending' WHERE bookingRequestID = %s"
            db[0].execute(query_reset_status, (booking_request_id,))
            db[1].commit()

        # Update the booking request with the new credentials
        query_update = """
            UPDATE booking_request 
            SET instructorID = %s, computerLabID = %s, 
                bookingDate = %s, bookingStartTime = %s, bookingEndTime = %s, 
                bookingPurpose = %s
            WHERE bookingRequestID = %s
        """
        db[0].execute(query_update, (instructorID, computer_lab_id, booking_date, booking_start_time, booking_end_time, booking_purpose, booking_request_id))
        db[1].commit()

        return {"message": "Booking request updated successfully"}
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.exception("Error updating booking request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

@BookingRequestRouter.delete("/booking-requests/{booking_request_id}", response_model=dict)
async def delete_booking_request(
    booking_request_id: int,
    db=Depends(get_db)
):
    try:
        # Execute the DELETE query to remove the booking request
        query = "DELETE FROM booking_request WHERE bookingRequestID = %s"
        result = db[0].execute(query, (booking_request_id,))
        db[1].commit()

        # Check if any rows were affected (i.e., if the booking request was deleted)
        if result.rowcount == 0:
            # No rows were affected, so the booking request was not found
            raise HTTPException(status_code=404, detail="Booking request not found")

        # Booking request was successfully deleted
        return {"message": "Booking request deleted successfully"}
    except Exception as e:
        # Log the exception for troubleshooting
        logging.error(f"Failed to delete booking request: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete booking request")