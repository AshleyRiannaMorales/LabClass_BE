import mysql.connector
from fastapi import Depends, HTTPException, Header

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "labclass",
    "port": 3306,
}

def get_db():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    try:
        yield cursor, db
    finally:
        cursor.close()
        db.close()

def get_current_admin_id(token: str = Header(...)):
    """
    Extracts the admin ID from the token in the request header.
    This function depends on your specific authentication implementation.
    """
    # Your authentication logic to decode the token and extract admin ID goes here
    # Example:
    # admin_id = decode_token(token)
    # if not admin_id:
    #     raise HTTPException(status_code=401, detail="Invalid or missing authentication token")
    # return admin_id
