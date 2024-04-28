from fastapi import Depends, HTTPException, APIRouter, Form
from .db import get_db
import bcrypt

AdminRouter = APIRouter(tags=["Admin"])

# CRUD operations for admin

@AdminRouter.get("/admin/", response_model=list)
async def read_admins(
    db=Depends(get_db)
):
    query = "SELECT adminID FROM admin"
    db[0].execute(query)
    admins = [{"adminID": admin[0]} for admin in db[0].fetchall()]
    return admins

@AdminRouter.post("/login/admin", response_model=dict)
async def admin_login(
    admin_id: int = Form(...), 
    admin_pass: str = Form(...), 
    db=Depends(get_db)
):
    query = "SELECT adminID FROM admin WHERE adminID = %s AND adminPass = %s"
    db[0].execute(query, (admin_id, admin_pass))
    admin = db[0].fetchone()
    if admin:
        return {"adminID": admin[0], "message": "Log In Successful"}
    else:
        # Check if admin ID exists
        query_check_id = "SELECT adminID FROM admin WHERE adminID = %s"
        db[0].execute(query_check_id, (admin_id,))
        existing_id = db[0].fetchone()
        if not existing_id:
            raise HTTPException(status_code=404, detail="Admin account does not exist with the provided ID")
        else:
            raise HTTPException(status_code=401, detail="Incorrect password provided")

@AdminRouter.put("/admin/{admin_id}", response_model=dict)
async def update_admin(
    admin_id: int,
    admin_pass: str = Form(...),
    db=Depends(get_db)
):
    # Update admin information in the database 
    query = "UPDATE admin SET adminPass = %s WHERE adminID = %s"
    db[0].execute(query, (admin_pass, admin_id))

    # Check if the update was successful
    if db[0].rowcount > 0:
        db[1].commit()
        return {"message": "Admin updated successfully"}
    
    # If no rows were affected, admin not found
    raise HTTPException(status_code=404, detail="Admin not found")

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