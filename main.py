# incident-service/main.py (UPDATED for DB)
from fastapi import FastAPI, HTTPException, status, Depends
from models import Incident, IncidentBase, IncidentUpdate, Status, Severity
from typing import List
from datetime import datetime
import httpx 
import asyncio
from fastapi.middleware.cors import CORSMiddleware 
from sqlalchemy.orm import Session
from database import SessionLocal, IncidentDB # Removed init_db here
import os 
from dotenv import load_dotenv

load_dotenv() # Load env vars for local testing

# Initialize the FastAPI application
app = FastAPI(title="Incident Core Service (Postgres)")

# --- CORS Configuration ---
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://k8s-incident-incident-a59589fc56-1030006196.us-east-1.elb.amazonaws.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Notification Configuration ---
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8001/notify")


# Dependency: Get Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Pydantic to DB Model Helper ---
def pydantic_to_db(incident: IncidentBase) -> IncidentDB:
    now = datetime.now()
    return IncidentDB(
        title=incident.title,
        description=incident.description,
        severity=incident.severity.value,
        status=Status.OPEN.value,
        created_at=now,
        updated_at=now
    )


# --- ASYNC Notification Function (No change to logic) ---
# ... (send_notification function body remains the same as previous step, but we define it here)
async def send_notification(incident: Incident):
    if incident.severity not in [Severity.CRITICAL, Severity.HIGH]:
        return
    
    payload = {
        "message": f"New {incident.severity.value} Incident: {incident.title}",
        "severity": incident.severity.value, 
        "source_service": "incident-service",
        "incident_id": incident.id,
    }
    # ... (httpx call logic remains the same)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                NOTIFICATION_SERVICE_URL,
                json=payload,
                timeout=5.0 
            )
            response.raise_for_status() 
            print(f"Successfully triggered notification for Incident ID: {incident.id}")
    except Exception as e:
        print(f"ERROR during notification: {e}")
    


# POST /incidents: CREATE (UPDATED with DB logic)
@app.post("/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(incident_data: IncidentBase, db: Session = Depends(get_db)):
    db_incident = pydantic_to_db(incident_data)
    
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    new_incident = Incident.model_validate(db_incident)
    
    asyncio.create_task(send_notification(new_incident)) 
    
    return new_incident


# GET /incidents: READ (All) (UPDATED with DB logic)
@app.get("/incidents", response_model=List[Incident])
async def list_incidents(db: Session = Depends(get_db)):
    incidents = db.query(IncidentDB).all()
    return [Incident.model_validate(inc) for inc in incidents]


# GET /incidents/{id}: READ (Single) (UPDATED with DB logic)
@app.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    db_incident = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return Incident.model_validate(db_incident)


# PUT /incidents/{id}: UPDATE (UPDATED with DB logic)
@app.put("/incidents/{incident_id}", response_model=Incident)
async def update_incident(incident_id: int, update_data: IncidentUpdate, db: Session = Depends(get_db)):
    db_incident = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    update_data_dict = update_data.model_dump(exclude_unset=True)
    
    # Update fields
    for key, value in update_data_dict.items():
        setattr(db_incident, key, value.value if isinstance(value, Enum) else value)
    
    db_incident.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_incident)
    
    return Incident.model_validate(db_incident)


# DELETE /incidents/{id}: DELETE (UPDATED with DB logic)
@app.delete("/incidents/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    db_incident = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    
    if db_incident:
        db.delete(db_incident)
        db.commit()
    return

# Basic Health Check
@app.get("/health")
async def health_check():
    return {"status": "ok"}
