from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestUpdate, MaintenanceRequestResponse
from services.maintenance import (
    create_maintenance_request,
    list_maintenance_requests,
    update_maintenance_request,
    delete_maintenance_request,
)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

@router.post("/", response_model=MaintenanceRequestResponse, status_code=201)
def create_request(data: MaintenanceRequestCreate, teacher_cpf: str, db: Session = Depends(get_db)):
    return create_maintenance_request(db, teacher_cpf, data)

@router.get("/my-requests", response_model=List[MaintenanceRequestResponse])
def list_my_requests(teacher_cpf: str, status: str = None, db: Session = Depends(get_db)):
    return list_maintenance_requests(db, teacher_cpf, status)

@router.put("/{request_id}", response_model=MaintenanceRequestResponse)
def update_request(request_id: int, data: MaintenanceRequestUpdate, teacher_cpf: str, db: Session = Depends(get_db)):
    return update_maintenance_request(db, request_id, teacher_cpf, data)

@router.delete("/{request_id}", status_code=204)
def delete_request(request_id: int, teacher_cpf: str, db: Session = Depends(get_db)):
    delete_maintenance_request(db, request_id, teacher_cpf)