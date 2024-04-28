# model/semschedule.py
from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
from datetime import timedelta

SemScheduleRouter = APIRouter(tags=["Semester Schedules"])


# CRUD operations for semester schedules

@SemScheduleRouter.get("/semester-schedules/", response_model=list[dict])
async def read_semester_schedules(db=Depends(get_db)):
    query = "SELECT * FROM sem_schedule"
    db[0].execute(query)
    semester_schedules = []

    for schedule in db[0].fetchall():
        formatted_schedule = {
            "semSchedID": schedule[0],
            "computerLabID": schedule[1],
            "schedDay": schedule[2],
            "schedSemester": schedule[5],
            "schedYear": schedule[6],
            "subject": schedule[7],
            "instructorID": schedule[8]
        }
        # Handle schedStartTime and schedEndTime formatting
        if isinstance(schedule[3], timedelta):
            formatted_schedule["schedStartTime"] = str(schedule[3])  # Convert timedelta to string
        else:
            formatted_schedule["schedStartTime"] = schedule[3].strftime("%H:%M")
        if isinstance(schedule[4], timedelta):
            formatted_schedule["schedEndTime"] = str(schedule[4])  # Convert timedelta to string
        else:
            formatted_schedule["schedEndTime"] = schedule[4].strftime("%H:%M")
        semester_schedules.append(formatted_schedule)
    return semester_schedules

@SemScheduleRouter.get("/semester-schedules/first-semester", response_model=list)
async def read_first_semester_schedules(db=Depends(get_db)):
    query = "SELECT * FROM first_sem_sched"
    db[0].execute(query)
    first_semester_schedules = []

    for schedule in db[0].fetchall():
        formatted_schedule = {
            "computerLabID": schedule[0],
            "instructorName": schedule[1],
            "subject": schedule[2],
            "schedSemester": schedule[3],
            "student_year": schedule[4],
            "student_course": schedule[5],
            "student_section": schedule[6],
            "schedDay": schedule[7]
        }
        # Handle schedStartTime and schedEndTime formatting
        if isinstance(schedule[8], timedelta):
            formatted_schedule["schedStartTime"] = str(schedule[8])  # Convert timedelta to string
        else:
            formatted_schedule["schedStartTime"] = schedule[8].strftime("%H:%M")
        if isinstance(schedule[9], timedelta):
            formatted_schedule["schedEndTime"] = str(schedule[9])  # Convert timedelta to string
        else:
            formatted_schedule["schedEndTime"] = schedule[9].strftime("%H:%M")
        first_semester_schedules.append(formatted_schedule)
    return first_semester_schedules

@SemScheduleRouter.get("/semester-schedules/second-semester", response_model=list)
async def read_second_semester_schedules(db=Depends(get_db)):
    query = "SELECT * FROM second_sem_sched"
    db[0].execute(query)
    second_semester_schedules = []

    for schedule in db[0].fetchall():
        formatted_schedule = {
            "computerLabID": schedule[0],
            "instructorName": schedule[1],
            "subject": schedule[2],
            "schedSemester": schedule[3],
            "student_year": schedule[4],
            "student_course": schedule[5],
            "student_section": schedule[6],
            "schedDay": schedule[7]
        }
        # Handle schedStartTime and schedEndTime formatting
        if isinstance(schedule[8], timedelta):
            formatted_schedule["schedStartTime"] = str(schedule[8])  # Convert timedelta to string
        else:
            formatted_schedule["schedStartTime"] = schedule[8].strftime("%H:%M")

        if isinstance(schedule[9], timedelta):
            formatted_schedule["schedEndTime"] = str(schedule[9])  # Convert timedelta to string
        else:
            formatted_schedule["schedEndTime"] = schedule[9].strftime("%H:%M")
        second_semester_schedules.append(formatted_schedule)
    return second_semester_schedules

@SemScheduleRouter.post("/semester-schedules/", response_model=dict)
async def create_semester_schedule(
    computer_lab_id: int = Form(...),
    sched_day: str = Form(...),
    sched_start_time: str = Form(...),
    sched_end_time: str = Form(...),
    sched_semester: str = Form(...),
    sched_year: int = Form(...),
    subject: str = Form(...),
    instructor_id: int = Form(...),
    student_year: str = Form(...),
    student_section: str = Form(...),
    student_course: str = Form(...),
    db=Depends(get_db)
):
    try:
        # Insert the new semester schedule into the database
        query = """
            INSERT INTO sem_schedule 
            (computerLabID, schedDay, schedStartTime, schedEndTime, schedSemester, schedYear, subject, instructorID, student_year, student_section, student_course) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        db[0].execute(
            query,
            (   computer_lab_id, sched_day, sched_start_time, sched_end_time,sched_semester, sched_year, subject, instructor_id, student_year, student_section, student_course,),
        )
        db[1].commit()

        return {"message": "Semester schedule created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create semester schedule")


@SemScheduleRouter.delete("/semester-schedules/")
async def delete_semester_schedule(
    semSchedID: int,
    db=Depends(get_db)
):
    try:
        # Delete the semester schedule from the database
        query = "DELETE FROM sem_schedule WHERE semSchedID = %s"
        db[0].execute(query, (semSchedID,))
        db[1].commit()

        return {"message": "Semester schedule deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete semester schedule")