from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.equipment import Equipment, EquipmentReservation, EquipmentReservationStatus, EquipmentStatus
from schemas.equipment import EquipmentCreate, EquipmentReservationCreate, EquipmentReservationResponse, EquipmentResponse

router = APIRouter(prefix="/api/equipment", tags=["Equipamentos"])


ACTIVE_RESERVATION_STATUSES = [
    EquipmentReservationStatus.pending,
    EquipmentReservationStatus.in_use,
]


def _get_equipment(db: Session, equipment_name: str) -> Equipment:
    equipment = db.query(Equipment).filter(Equipment.name == equipment_name).first()
    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento nao encontrado",
        )
    return equipment


def _check_equipment_maintenance(equipment: Equipment) -> None:
    if equipment.status == EquipmentStatus.maintenance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The equipment '{equipment.name}' is under maintenance and cannot be reserved",
        )


def _check_user_conflict(db: Session, user_cpf: str, pickup_time, return_time) -> None:
    existing = (
        db.query(EquipmentReservation)
        .filter(
            EquipmentReservation.user_cpf == user_cpf,
            EquipmentReservation.status.in_(ACTIVE_RESERVATION_STATUSES),
            EquipmentReservation.pickup_time < return_time,
            EquipmentReservation.return_time > pickup_time,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a reservation at this time",
        )


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate, db: Session = Depends(get_db)) -> Equipment:
    exists = db.query(Equipment).filter(Equipment.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Equipamento ja cadastrado")

    equipment = Equipment(
        name=payload.name,
        total_quantity=payload.total_quantity,
        status=payload.status,
        description=payload.description,
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.get("/", response_model=List[EquipmentResponse])
def list_equipment(db: Session = Depends(get_db)) -> list[Equipment]:
    return db.query(Equipment).order_by(Equipment.name).all()


@router.post(
    "/reservations/",
    response_model=EquipmentReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar reserva de equipamento",
)
def create_equipment_reservation(
    payload: EquipmentReservationCreate,
    user_cpf: str = Query(..., description="CPF do usuario"),
    user_name: str = Query(..., description="Nome do usuario"),
    db: Session = Depends(get_db),
) -> EquipmentReservation:
    equipment = _get_equipment(db, payload.equipment_type)
    _check_equipment_maintenance(equipment)

    if payload.quantity > equipment.total_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {equipment.total_quantity} units of '{equipment.name}' are registered",
        )

    _check_user_conflict(db, user_cpf, payload.pickup_time, payload.return_time)

    reservation = EquipmentReservation(
        user_cpf=user_cpf,
        user_name=user_name,
        equipment_type=equipment.name,
        quantity=payload.quantity,
        pickup_time=payload.pickup_time,
        return_time=payload.return_time,
        status=EquipmentReservationStatus.pending,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("/reservations/", response_model=List[EquipmentReservationResponse])
def list_user_equipment_reservations(
    user_cpf: str = Query(..., description="CPF do usuario"),
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> list[EquipmentReservation]:
    query = db.query(EquipmentReservation).filter(EquipmentReservation.user_cpf == user_cpf)
    if active_only:
        query = query.filter(EquipmentReservation.status.in_(ACTIVE_RESERVATION_STATUSES))
    return query.order_by(EquipmentReservation.pickup_time.desc()).all()


@router.patch(
    "/reservations/{reservation_id}/cancel",
    response_model=EquipmentReservationResponse,
    summary="Cancelar reserva pendente de equipamento",
)
def cancel_equipment_reservation(
    reservation_id: int,
    user_cpf: str = Query(..., description="CPF do usuario"),
    db: Session = Depends(get_db),
) -> EquipmentReservation:
    reservation = db.query(EquipmentReservation).filter(EquipmentReservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")
    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    if reservation.status != EquipmentReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending reservations can be canceled")

    reservation.status = EquipmentReservationStatus.canceled
    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch(
    "/reservations/{reservation_id}/pickup",
    response_model=EquipmentReservationResponse,
    summary="Confirmar retirada de equipamento",
)
def confirm_equipment_pickup(
    reservation_id: int,
    user_cpf: str = Query(..., description="CPF do usuario"),
    db: Session = Depends(get_db),
) -> EquipmentReservation:
    reservation = db.query(EquipmentReservation).filter(EquipmentReservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")
    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    if reservation.status != EquipmentReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending reservations can be picked up")

    reservation.status = EquipmentReservationStatus.in_use
    db.commit()
    db.refresh(reservation)
    return reservation
