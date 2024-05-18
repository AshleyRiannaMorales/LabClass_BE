from fastapi import Depends, HTTPException, APIRouter, Form, status
from .db import get_db
import logging
from typing import List, Dict
from datetime import timedelta 


BookingRequestRouter = APIRouter(tags=["Booking Requests"])
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

# CRUD operations for booking requests

@BookingRequestRouter.get("/booking-requests/", response_model=list)
async def read_booking_requests(db=Depends(get_db)):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
        """
        db[0].execute(query)
        booking_requests = []

        for booking in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": booking[0],
                "instructorID": booking[1],
                "instructorName": booking[9],  # Using the combined instructor name from index 9
                "computerLabID": booking[2],
                "bookingDate": booking[3],
                "bookingStartTime": format_time_from_duration(booking[4]),
                "bookingEndTime": format_time_from_duration(booking[5]),
                "bookingPurpose": booking[6],
                "bookingReqStatus": booking[7]
            }
            booking_requests.append(formatted_booking)

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

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

    # Check for time conflicts
    conflict_query = """
        SELECT 1 FROM first_sem_sched
        WHERE computerLabID = %s AND
              schedDay = DAYNAME(%s) AND
              (%s < schedEndTime AND %s > schedStartTime)
    """
    db[0].execute(conflict_query, (computer_lab_id, booking_date, booking_end_time, booking_start_time))
    conflict = db[0].fetchone()
    
    if conflict:
        raise HTTPException(status_code=409, detail="Time conflict with an existing schedule")

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

@BookingRequestRouter.put("/booking-requests/{booking_request_id}/cancel", response_model=dict)
async def cancel_booking_request(
    booking_request_id: int, 
    db=Depends(get_db)
):
    try:
        # Fetch the booking request to ensure it exists
        query = """
            SELECT bookingRequestID, instructorID, bookingReqStatus
            FROM booking_request
            WHERE bookingRequestID = %s
        """
        db[0].execute(query, (booking_request_id,))
        booking_request = db[0].fetchone()

        if not booking_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking request not found")

        # Check if the booking request is already cancelled or approved
        if booking_request[2] in ["Cancelled", "Approved"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Booking request is already {booking_request[2].lower()}")

        # Update the status to 'Cancelled'
        update_query = """
            UPDATE booking_request
            SET bookingReqStatus = 'Cancelled'
            WHERE bookingRequestID = %s
        """
        db[0].execute(update_query, (booking_request_id,))
        db[1].commit()

        return {"message": "Booking request cancelled successfully"}
    except HTTPException as e:
        raise e  # Ensure HTTPExceptions are propagated properly
    except Exception as e:
        logger.exception("Error cancelling booking request: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred.")
    
@BookingRequestRouter.get("/booking-requests/instructor/{instructor_id}", response_model=list)
async def read_booking_requests_by_instructor(instructor_id: int, db=Depends(get_db)):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.instructorID = %s
        """
        db[0].execute(query, (instructor_id,))
        booking_requests = []

        for booking in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": booking[0],
                "instructorID": booking[1],
                "instructorName": booking[9],  # Using the combined instructor name from index 9
                "computerLabID": booking[2],
                "bookingDate": booking[3],
                "bookingStartTime": format_time_from_duration(booking[4]),
                "bookingEndTime": format_time_from_duration(booking[5]),
                "bookingPurpose": booking[6],
                "bookingReqStatus": booking[7]
            }
            booking_requests.append(formatted_booking)

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests for instructor: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

@BookingRequestRouter.get("/booking-requests/newest-to-oldest", response_model=list)
async def read_booking_requests_from_newest_to_oldest(db=Depends(get_db)):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            ORDER BY br.bookingRequestID DESC
        """
        db[0].execute(query)
        booking_requests = []

        for booking in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": booking[0],
                "instructorID": booking[1],
                "instructorName": booking[9],  # Using the combined instructor name from index 9
                "computerLabID": booking[2],
                "bookingDate": booking[3],
                "bookingStartTime": format_time_from_duration(booking[4]),
                "bookingEndTime": format_time_from_duration(booking[5]),
                "bookingPurpose": booking[6],
                "bookingReqStatus": booking[7]
            }
            booking_requests.append(formatted_booking)

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

@BookingRequestRouter.get("/booking-requests/oldest-to-newest", response_model=list)
async def read_booking_requests_from_oldest_to_newest(db=Depends(get_db)):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            ORDER BY br.bookingRequestID ASC
        """
        db[0].execute(query)
        booking_requests = []

        for booking in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": booking[0],
                "instructorID": booking[1],
                "instructorName": booking[9],  # Using the combined instructor name from index 9
                "computerLabID": booking[2],
                "bookingDate": booking[3],
                "bookingStartTime": format_time_from_duration(booking[4]),
                "bookingEndTime": format_time_from_duration(booking[5]),
                "bookingPurpose": booking[6],
                "bookingReqStatus": booking[7]
            }
            booking_requests.append(formatted_booking)

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
        
@BookingRequestRouter.get("/booking-requests/instructor/{instructor_id}/newest-to-oldest", response_model=list)
async def read_booking_requests_by_instructor_newest_to_oldest(instructor_id: int, db=Depends(get_db)):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.instructorID = %s
            ORDER BY br.bookingRequestID DESC
        """
        db[0].execute(query, (instructor_id,))
        booking_requests = []

        for booking in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": booking[0],
                "instructorID": booking[1],
                "instructorName": booking[9],  # Using the combined instructor name from index 9
                "computerLabID": booking[2],
                "bookingDate": booking[3],
                "bookingStartTime": format_time_from_duration(booking[4]),
                "bookingEndTime": format_time_from_duration(booking[5]),
                "bookingPurpose": booking[6],
                "bookingReqStatus": booking[7]
            }
            booking_requests.append(formatted_booking)

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests for instructor: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

@BookingRequestRouter.get("/booking-requests/instructor/{instructor_id}/oldest-to-newest", response_model=list)
async def read_booking_requests_by_instructor_oldest_to_newest(instructor_id: int, db=Depends(get_db)):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.instructorID = %s
            ORDER BY br.bookingRequestID ASC
        """
        db[0].execute(query, (instructor_id,))
        booking_requests = []

        for booking in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": booking[0],
                "instructorID": booking[1],
                "instructorName": booking[9],  # Using the combined instructor name from index 9
                "computerLabID": booking[2],
                "bookingDate": booking[3],
                "bookingStartTime": format_time_from_duration(booking[4]),
                "bookingEndTime": format_time_from_duration(booking[5]),
                "bookingPurpose": booking[6],
                "bookingReqStatus": booking[7]
            }
            booking_requests.append(formatted_booking)

        return booking_requests
    except Exception as e:
        logger.exception("Error retrieving booking requests for instructor: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

@BookingRequestRouter.get("/booking-requests/{booking_request_id}", response_model=dict)
async def read_booking_request(
    booking_request_id: int, 
    db=Depends(get_db)
):
    try:
        query = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorID, CONCAT(i.instructorFirstName, ' ', i.instructorLastName) AS instructorName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.bookingRequestID = %s
        """
        db[0].execute(query, (booking_request_id,))
        booking_request = db[0].fetchone()

        if booking_request:
            formatted_booking = {
                "bookingRequestID": booking_request[0],
                "instructorID": booking_request[1],
                "instructorName": f"{booking_request[9]}",  # Using the combined instructor name from index 9
                "computerLabID": booking_request[2],
                "bookingDate": booking_request[3],
                "bookingStartTime": format_time_from_duration(booking_request[4]),
                "bookingEndTime": format_time_from_duration(booking_request[5]),
                "bookingPurpose": booking_request[6],
                "bookingReqStatus": booking_request[7],  # Include booking status
            }
            return formatted_booking

        raise HTTPException(status_code=404, detail="Booking request not found")
    except Exception as e:
        logger.exception("Error retrieving booking request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

@BookingRequestRouter.get("/pending-booking-requests", response_model=List[Dict])
async def get_pending_booking_requests(db=Depends(get_db)):
    try:
        # Retrieve pending booking requests
        query_pending_requests = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorFirstName, i.instructorLastName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.bookingReqStatus = 'Pending'
        """

        db[0].execute(query_pending_requests)
        pending_requests = []

        for request in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": request[0],
                "instructorID": request[1],
                "instructorName": f"{request[8]} {request[9]}",  # Concatenate first name and last name
                "computerLabID": request[2],
                "bookingDate": request[3],
                "bookingStartTime": format_time_from_duration(request[4]),
                "bookingEndTime": format_time_from_duration(request[5]),
                "bookingPurpose": request[6],
                "bookingReqStatus": request[7]
            } 
            pending_requests.append(formatted_booking)

        return pending_requests
    
    except Exception as e:
        logger.exception("Error retrieving pending booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@BookingRequestRouter.get("/approved-booking-requests", response_model=List[Dict])
async def get_approved_booking_requests(db=Depends(get_db)):
    try:
        # Retrieve approved booking requests
        query_approved_requests = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorFirstName, i.instructorLastName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.bookingReqStatus = 'Approved'
        """

        db[0].execute(query_approved_requests)
        approved_requests = []

        for request in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": request[0],
                "instructorID": request[1],
                "instructorName": f"{request[8]} {request[9]}",  # Concatenate first name and last name
                "computerLabID": request[2],
                "bookingDate": request[3],
                "bookingStartTime": format_time_from_duration(request[4]),
                "bookingEndTime": format_time_from_duration(request[5]),
                "bookingPurpose": request[6],
                "bookingReqStatus": request[7]         
            }
            approved_requests.append(formatted_booking)

        return approved_requests
    
    except Exception as e:
        logger.exception("Error retrieving approved booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")
    
@BookingRequestRouter.get("/rejected-booking-requests", response_model=List[Dict])
async def get_rejected_booking_requests(db=Depends(get_db)):
    try:
        # Retrieve rejected booking requests
        query_rejected_requests = """
            SELECT br.bookingRequestID, br.instructorID, br.computerLabID, br.bookingDate,
                   br.bookingStartTime, br.bookingEndTime, br.bookingPurpose, br.bookingReqStatus,
                   i.instructorFirstName, i.instructorLastName
            FROM booking_request br
            JOIN instructor i ON br.instructorID = i.instructorID
            WHERE br.bookingReqStatus = 'Rejected'
        """

        db[0].execute(query_rejected_requests)
        rejected_requests = []

        for request in db[0].fetchall():
            formatted_booking = {
                "bookingRequestID": request[0],
                "instructorID": request[1],
                "computerLabID": request[2],
                "bookingDate": request[3],
                "bookingStartTime": format_time_from_duration(request[4]),
                "bookingEndTime": format_time_from_duration(request[5]),
                "bookingPurpose": request[6],
                "bookingReqStatus": request[7],
                "instructorName": f"{request[8]} {request[9]}"  # Concatenate first name and last name
            }
            rejected_requests.append(formatted_booking)

        return rejected_requests
    
    except Exception as e:
        logger.exception("Error retrieving rejected booking requests: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error occurred.")

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
        logger.error(f"Failed to delete booking request: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete booking request")