# incident-service/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Use Python Enums for strict choices
class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Status(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

# Model for Incident creation (data required from the request body)
class IncidentBase(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=10)
    severity: Severity = Severity.MEDIUM
    
# Model for the data we return (includes generated fields)
class Incident(IncidentBase):
    id: int
    status: Status = Status.OPEN
    created_at: datetime
    updated_at: datetime
    
# Model for updating an incident (all fields are optional)
class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[Status] = None

# Allow Pydantic v2 models to be mutated (required for our in-memory updates)
Incident.model_config = {'frozen': False}
