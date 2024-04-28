# model/semschedule.py
from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import bcrypt

SemScheduleRouter = APIRouter(tags=["Semester Schedules"])

# CRUD operations for semester schedules

@SemScheduleRouter.get("/semester-schedules/", response_model=list)
async def read_semester_schedules(
    db=Depends(get_db)
):
    query = "SELECT * FROM sem_schedule"
    db[0].execute(query)
    semester_schedules = [{
        "semSchedID": schedule[0],
        "adminID": schedule[1],
        "computerLabID": schedule[2],
        "schedDay": schedule[3],
        "schedStartTime": schedule[4],
        "schedEndTime": schedule[5],
        "schedSemester": schedule[6],
        "schedYear": schedule[7]
    } for schedule in db[0].fetchall()]
    return semester_schedules

@SemScheduleRouter.get("/semester-schedules/{sem_schedule_id}", response_model=dict)
async def read_semester_schedule(
    sem_schedule_id: int, 
    db=Depends(get_db)
):
    query = "SELECT * FROM sem_schedule WHERE semSchedID = %s"
    db[0].execute(query, (sem_schedule_id,))
    semester_schedule = db[0].fetchone()
    if semester_schedule:
        return {
            "semSchedID": semester_schedule[0],
            "adminID": semester_schedule[1],
            "computerLabID": semester_schedule[2],
            "schedDay": semester_schedule[3],
            "schedStartTime": semester_schedule[4],
            "schedEndTime": semester_schedule[5],
            "schedSemester": semester_schedule[6],
            "schedYear": semester_schedule[7]
        }
    raise HTTPException(status_code=404, detail="Semester schedule not found")

@SemScheduleRouter.post("/semester-schedules/", response_model=dict)
async def create_semester_schedule(
    admin_id: int = Form(...),
    computer_lab_id: int = Form(...),
    sched_day: str = Form(...),
    sched_start_time: str = Form(...),
    sched_end_time: str = Form(...),
    sched_semester: str = Form(...),
    sched_year: int = Form(...),
    db=Depends(get_db)
):
    query = "INSERT INTO sem_schedule (adminID, computerLabID, schedDay, schedStartTime, schedEndTime, schedSemester, schedYear) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    db[0].execute(query, (admin_id, computer_lab_id, sched_day, sched_start_time, sched_end_time, sched_semester, sched_year))
    db[1].commit()

    # Retrieve the last inserted ID using LAST_INSERT_ID()
    db[0].execute("SELECT LAST_INSERT_ID()")
    new_sem_schedule_id = db[0].fetchone()[0]

    return {"semSchedID": new_sem_schedule_id}

@SemScheduleRouter.put("/semester-schedules/{sem_schedule_id}", response_model=dict)
async def update_semester_schedule(
    sem_schedule_id: int,
    admin_id: int = Form(...),
    computer_lab_id: int = Form(...),
    sched_day: str = Form(...),
    sched_start_time: str = Form(...),
    sched_end_time: str = Form(...),
    sched_semester: str = Form(...),
    sched_year: int = Form(...),
    db=Depends(get_db)
):
    query = "UPDATE sem_schedule SET adminID = %s, computerLabID = %s, schedDay = %s, schedStartTime = %s, schedEndTime = %s, schedSemester = %s, schedYear = %s WHERE semSchedID = %s"
    db[0].execute(query, (admin_id, computer_lab_id, sched_day, sched_start_time, sched_end_time, sched_semester, sched_year, sem_schedule_id))
    db[1].commit()

    return {"message": "Semester schedule updated successfully"}

@SemScheduleRouter.delete("/semester-schedules/{sem_schedule_id}", response_model=dict)
async def delete_semester_schedule(
    sem_schedule_id: int,
    db=Depends(get_db)
):
    query = "DELETE FROM sem_schedule WHERE semSchedID = %s"
    db[0].execute(query, (sem_schedule_id,))
    db[1].commit()

    return {"message": "Semester schedule deleted successfully"}