from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from model.instructors import InstructorsRouter
from model.admin import AdminRouter
from model.bookingrequest import BookingRequestRouter
from model.semschedule import SemScheduleRouter
from model.computerlab import ComputerLabRouter
from model.verificationrequest import VerificationRequests

app = FastAPI(
    title="LabClass API",
    description="LabClass is a user-friendly web application designed to simplify the scheduling of computer laboratory classrooms at UIC Fr. Selga Campus. It facilitates seamless coordination between instructors and laboratory staff, allowing efficient scheduling, real-time availability checks, and notifications. Instructors can easily manage their class schedules, while the laboratory staff oversees bookings and maintains transparent communication.",
    version="1.0.0"
)

# Set up CORS
origins = [
    "http://localhost:",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include CRUD routes from modules
app.include_router(InstructorsRouter, prefix="/api", tags=["Instructors"])
app.include_router(AdminRouter, prefix="/api", tags=["Admin"])
app.include_router(VerificationRequests, prefix="/api", tags=["Verification Requests"])
app.include_router(BookingRequestRouter, prefix="/api", tags=["Booking Requests"])
app.include_router(SemScheduleRouter, prefix="/api", tags=["Semester Schedule"])
app.include_router(ComputerLabRouter, prefix="/api", tags=["Computer Labs"])

# Include API documentation route
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="LabClass API Docs")

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    return app.openapi()