from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.maintenance import MaintenanceRequest, MaintenanceStatus
from schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestUpdate, MaintenanceRequestResponse

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

@router.post("/", response_model=MaintenanceRequestResponse, status_code=201)
def create_request(data: MaintenanceRequestCreate, teacher_name: str, db: Session = Depends(get_db)):
    existing = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.room == data.room,
        MaintenanceRequest.teacher_name == teacher_name,
        MaintenanceRequest.status == MaintenanceStatus.pending
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Já existe uma solicitação pendente para esta sala")

    new_request = MaintenanceRequest(
        teacher_name=teacher_name,
        room=data.room,
        description=data.description,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/my-requests", response_model=List[MaintenanceRequestResponse])
def list_my_requests(teacher_name: str, db: Session = Depends(get_db)):
    return db.query(MaintenanceRequest).filter(
        MaintenanceRequest.teacher_name == teacher_name
    ).all()

@router.put("/{request_id}", response_model=MaintenanceRequestResponse)
def update_request(request_id: int, data: MaintenanceRequestUpdate, db: Session = Depends(get_db)):
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != MaintenanceStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending requests can be edited")
    request.description = data.description
    db.commit()
    db.refresh(request)
    return request

@router.delete("/{request_id}", status_code=204)
def delete_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != MaintenanceStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending requests can be deleted")
    db.delete(request)
    db.commit()
    return None