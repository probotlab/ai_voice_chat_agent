import datetime as dt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse 
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
import uvicorn

# Import from your database.py file
from database import init_db, Appointment, get_db

# Initialize the database tables
init_db()

# --- PYDANTIC MODELS (Data Contracts) ---
class AppointmentRequest(BaseModel):
    patient_name: str
    reason: str | None = None
    start_time: dt.datetime

class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    reason: str | None
    start_time: dt.datetime
    cancelled: bool 
    created_at: dt.datetime

class CancelAppointmentRequest(BaseModel):
    patient_name: str
    date: dt.date

class CancelAppointmentResponse(BaseModel):
    canceled_count: int

# --- FASTAPI APP ---
app = FastAPI()

# 1. Schedule Appointment
@app.post("/schedule_appointment/", response_model=AppointmentResponse)
def schedule_appointment(request: AppointmentRequest, db: Session = Depends(get_db)):
    new_appointment = Appointment(
        patient_name=request.patient_name,
        reason=request.reason,
        start_time=request.start_time
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    
    return AppointmentResponse(
        id=new_appointment.id,
        patient_name=new_appointment.patient_name,
        reason=new_appointment.reason,
        start_time=new_appointment.start_time,
        cancelled=new_appointment.cancelled,
        created_at=new_appointment.created_at
    )

# 2. Cancel Appointment
@app.post("/cancel_appointment/", response_model=CancelAppointmentResponse)
def cancel_appointment(request: CancelAppointmentRequest, db: Session = Depends(get_db)):
    start_dt = dt.datetime.combine(request.date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)
    
    result = db.execute(
        select(Appointment)
        .where(Appointment.patient_name == request.patient_name)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time < end_dt)
        .where(Appointment.cancelled == False)
    )

    appointments = result.scalars().all()
    
    if not appointments:
        raise HTTPException(status_code=404, detail="No matching appointment found.")

    for appointment in appointments:
        appointment.cancelled = True  # Fixed: Actually update the database

    db.commit()
    
    return CancelAppointmentResponse(canceled_count=len(appointments))

# 3. List Appointments (FIXED for 422 Error)
@app.get("/list_appointments/")
def list_appointments(date: dt.date | None = None, db: Session = Depends(get_db)):
    query = select(Appointment).where(Appointment.cancelled == False)
    
    # If the frontend passes a specific date, filter by it
    if date:
        start_dt = dt.datetime.combine(date, dt.time.min)
        end_dt = start_dt + dt.timedelta(days=1)
        query = query.where(Appointment.start_time >= start_dt)
        query = query.where(Appointment.start_time < end_dt)
        
    query = query.order_by(Appointment.start_time.asc())
    
    result = db.execute(query)
    appointments = result.scalars().all()
    
    booked_appointments = []
    for appointment in appointments:
        appointment_obj = AppointmentResponse(
            id=appointment.id,
            patient_name=appointment.patient_name,
            reason=appointment.reason,
            start_time=appointment.start_time,
            cancelled=appointment.cancelled,
            created_at=appointment.created_at
        )
        booked_appointments.append(appointment_obj) # Fixed: Correct list append
        
    return booked_appointments

# 4. Serve the Voice Agent HTML Page
@app.get("/agent")
def serve_voice_agent():
    # This tells FastAPI to send your agent.html file to the browser
    return FileResponse("agent.html")
    
if __name__ == "__main__":
    # Render sets a 'PORT' env var automatically. If it's not there, use 10000.
    port = int(os.environ.get("PORT", 10000))
    
    # Use 0.0.0.0 to make it accessible to Render's network
    uvicorn.run("backend:app", host="0.0.0.0", port=port, reload=False)
