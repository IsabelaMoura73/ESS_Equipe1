from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from dependencies import get_current_user, require_admin
import models, schemas

router = APIRouter()


# ── Sala ──────────────────────────────────────────────────────────────────────

@router.get("/sala", response_model=List[schemas.RoomReservationOut])
def list_room_reservations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tipo == "admin":
        return db.query(models.RoomReservation).order_by(
            models.RoomReservation.status
        ).all()
    return db.query(models.RoomReservation).filter(
        models.RoomReservation.usuario_id == current_user.id
    ).all()


@router.post("/sala", response_model=schemas.RoomReservationOut, status_code=201)
def create_room_reservation(
    data: schemas.RoomReservationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(models.Room).filter(models.Room.id == data.sala_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.em_manutencao:
        raise HTTPException(status_code=400, detail="Sala em manutenção")

    conflict = db.query(models.RoomReservation).filter(
        models.RoomReservation.usuario_id == current_user.id,
        models.RoomReservation.status.in_(("pendente", "confirmada")),
        models.RoomReservation.horario_inicio < data.horario_fim,
        models.RoomReservation.horario_fim > data.horario_inicio,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Você já possui uma reserva neste horário.")

    res = models.RoomReservation(
        usuario_id=current_user.id,
        sala_id=data.sala_id,
        horario_inicio=data.horario_inicio,
        horario_fim=data.horario_fim,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


@router.delete("/sala/{res_id}")
def cancel_room_reservation(
    res_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = db.query(models.RoomReservation).filter(models.RoomReservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    if res.usuario_id != current_user.id and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    if res.status != "pendente":
        raise HTTPException(status_code=400, detail="Só é possível cancelar reservas pendentes.")
    res.status = "cancelada"
    db.commit()
    return {"message": "Reserva cancelada"}


@router.patch("/sala/{res_id}/status")
def set_room_reservation_status(
    res_id: int,
    status: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if status not in ("confirmada", "negada"):
        raise HTTPException(status_code=400, detail="Status inválido")
    res = db.query(models.RoomReservation).filter(models.RoomReservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    if res.status != "pendente":
        raise HTTPException(status_code=400, detail="Reserva não está pendente")
    res.status = status
    db.commit()
    return {"message": f"Reserva {status}"}


# ── Lab ───────────────────────────────────────────────────────────────────────

@router.get("/lab", response_model=List[schemas.LabReservationOut])
def list_lab_reservations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tipo == "admin":
        return db.query(models.LabReservation).all()
    return db.query(models.LabReservation).filter(
        models.LabReservation.usuario_id == current_user.id
    ).all()


@router.post("/lab", response_model=schemas.LabReservationOut, status_code=201)
def create_lab_reservation(
    data: schemas.LabReservationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(models.Room).filter(models.Room.id == data.sala_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if room.em_manutencao:
        raise HTTPException(status_code=400, detail="Sala em manutenção")
    if data.qtd_computadores > room.qtd_computadores:
        raise HTTPException(status_code=400, detail="Quantidade de computadores excede o disponível")

    conflict = db.query(models.LabReservation).filter(
        models.LabReservation.usuario_id == current_user.id,
        models.LabReservation.status.in_(("pendente", "confirmada")),
        models.LabReservation.horario_inicio < data.horario_fim,
        models.LabReservation.horario_fim > data.horario_inicio,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Você já possui uma reserva neste horário.")

    res = models.LabReservation(
        usuario_id=current_user.id,
        sala_id=data.sala_id,
        qtd_computadores=data.qtd_computadores,
        horario_inicio=data.horario_inicio,
        horario_fim=data.horario_fim,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


@router.delete("/lab/{res_id}")
def cancel_lab_reservation(
    res_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = db.query(models.LabReservation).filter(models.LabReservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    if res.usuario_id != current_user.id and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    if res.status != "pendente":
        raise HTTPException(status_code=400, detail="Só é possível cancelar reservas pendentes.")
    res.status = "cancelada"
    db.commit()
    return {"message": "Reserva cancelada"}


@router.patch("/lab/{res_id}/status")
def set_lab_reservation_status(
    res_id: int,
    status: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if status not in ("confirmada", "negada"):
        raise HTTPException(status_code=400, detail="Status inválido")
    res = db.query(models.LabReservation).filter(models.LabReservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    if res.status != "pendente":
        raise HTTPException(status_code=400, detail="Reserva não está pendente")
    res.status = status
    db.commit()
    return {"message": f"Reserva {status}"}
