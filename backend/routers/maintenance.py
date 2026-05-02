from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from dependencies import get_current_user, require_admin, require_docente_or_admin
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.MaintenanceOut])
def list_maintenance(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tipo == "admin":
        return db.query(models.MaintenanceRequest).all()
    return db.query(models.MaintenanceRequest).filter(
        models.MaintenanceRequest.usuario_id == current_user.id
    ).all()


@router.post("/", response_model=schemas.MaintenanceOut, status_code=201)
def create_maintenance(
    data: schemas.MaintenanceCreate,
    current_user: models.User = Depends(require_docente_or_admin),
    db: Session = Depends(get_db),
):
    room = db.query(models.Room).filter(models.Room.id == data.sala_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    req = models.MaintenanceRequest(
        usuario_id=current_user.id,
        sala_id=data.sala_id,
        descricao=data.descricao,
        data_inicio=data.data_inicio,
        data_fim=data.data_fim,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.delete("/{req_id}")
def cancel_maintenance(
    req_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if req.usuario_id != current_user.id and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    if req.status != "pendente":
        raise HTTPException(status_code=400, detail="Só é possível cancelar solicitações pendentes.")
    db.delete(req)
    db.commit()
    return {"message": "Solicitação cancelada"}


@router.patch("/{req_id}/status")
def set_maintenance_status(
    req_id: int,
    status: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if status not in ("aprovada", "negada"):
        raise HTTPException(status_code=400, detail="Status inválido")
    req = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    req.status = status
    if status == "aprovada":
        req.sala.em_manutencao = True
        # Negar reservas pendentes da sala
        for res in req.sala.reservas_sala:
            if res.status == "pendente":
                res.status = "negada"
        for res in req.sala.reservas_lab:
            if res.status == "pendente":
                res.status = "negada"

    db.commit()
    return {"message": f"Solicitação {status}"}
