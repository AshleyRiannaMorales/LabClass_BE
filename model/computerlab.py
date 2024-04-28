# model/computerlab.py
from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db

ComputerLabRouter = APIRouter(tags=["Computer Labs"])

# CRUD operations for computer labs

@ComputerLabRouter.get("/computer-labs/", response_model=list)
async def read_computer_labs(
    db=Depends(get_db)
):
    query = "SELECT * FROM computer_lab"
    db[0].execute(query)
    computer_labs = [{
        "computerLabID": lab[0],
        "computerLabCapacity": lab[1]
    } for lab in db[0].fetchall()]
    return computer_labs

@ComputerLabRouter.get("/computer-labs/{computer_lab_id}", response_model=dict)
async def read_computer_lab(
    computer_lab_id: int, 
    db=Depends(get_db)
):
    query = "SELECT * FROM computer_lab WHERE computerLabID = %s"
    db[0].execute(query, (computer_lab_id,))
    computer_lab = db[0].fetchone()
    if computer_lab:
        return {
            "computerLabID": computer_lab[0],
            "computerLabCapacity": computer_lab[1]
        }
    raise HTTPException(status_code=404, detail="Computer lab not found")

@ComputerLabRouter.post("/computer-labs/", response_model=dict)
async def create_computer_lab(
    computer_lab_id: int = Form(...),
    computer_lab_capacity: int = Form(...),
    db=Depends(get_db)
):
    query = "INSERT INTO computer_lab (computerLabID, computerLabCapacity) VALUES (%s, %s)"
    db[0].execute(query, (computer_lab_id, computer_lab_capacity))
    db[1].commit()

    return {"computerLabID": computer_lab_id}

@ComputerLabRouter.put("/computer-labs/{computer_lab_id}", response_model=dict)
async def update_computer_lab(
    computer_lab_id: int,
    computer_lab_capacity: int = Form(...),
    db=Depends(get_db)
):
    query = "UPDATE computer_lab SET computerLabCapacity = %s WHERE computerLabID = %s"
    db[0].execute(query, (computer_lab_capacity, computer_lab_id))
    db[1].commit()

    return {"message": "Computer lab updated successfully"}

@ComputerLabRouter.delete("/computer-labs/{computer_lab_id}", response_model=dict)
async def delete_computer_lab(
    computer_lab_id: int,
    db=Depends(get_db)
):
    query = "DELETE FROM computer_lab WHERE computerLabID = %s"
    db[0].execute(query, (computer_lab_id,))
    db[1].commit()

    return {"message": "Computer lab deleted successfully"}
