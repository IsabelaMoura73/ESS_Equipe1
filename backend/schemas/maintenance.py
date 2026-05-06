from pydantic import BaseModel
from typing import Optional
from datetime import date
from models.maintenance import MaintenanceStatus

class MaintenanceRequestCreate(BaseModel):
    room: str
    description: str

class MaintenanceRequestUpdate(BaseModel):
    description: str

class MaintenanceRequestResponse(BaseModel):
    id: int
    teacher_name: str
    room: str
    description: str
    status: MaintenanceStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    model_config = {"from_attributes": True}