from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from models.reservation import Reservation, ReservationStatus
from models.room import Room, RoomMaintenanceStatus
from schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate

router = APIRouter(prefix="/api/reservations", tags=["Reservas de Sala"])


def _check_room_maintenance(db: Session, room_name: str) -> None:
    room = db.query(Room).filter(Room.name == room_name).first()
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala não encontrada",
        )
    if room.maintenance_status == RoomMaintenanceStatus.yes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sala em manutenção",
        )


def _check_confirmed_conflict(
    db: Session, room_name: str, start: datetime, end: datetime, exclude_id: int | None = None
) -> None:
    query = (
        db.query(Reservation)
        .filter(
            Reservation.room == room_name,
            Reservation.status == ReservationStatus.confirmed,
            Reservation.start_time < end,
            Reservation.end_time > start,
        )
    )
    if exclude_id is not None:
        query = query.filter(Reservation.id != exclude_id)

    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conflito de horário: a sala já está reservada neste período",
        )


def _check_user_conflict(
    db: Session, user_cpf: str, start: datetime, end: datetime, exclude_id: int | None = None
) -> None:
    query = (
        db.query(Reservation)
        .filter(
            Reservation.user_cpf == user_cpf,
            Reservation.status.in_([ReservationStatus.pending, ReservationStatus.confirmed]),
            Reservation.start_time < end,
            Reservation.end_time > start,
        )
    )
    if exclude_id is not None:
        query = query.filter(Reservation.id != exclude_id)

    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você já possui uma reserva neste horário",
        )


@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar reserva de sala",
)
def create_reservation(
    payload: ReservationCreate,
    user_cpf: str = Query(..., description="CPF do usuário"),
    user_name: str = Query(..., description="Nome do usuário"),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    _check_room_maintenance(db, payload.room)
    _check_confirmed_conflict(db, payload.room, payload.start_time, payload.end_time)
    _check_user_conflict(db, user_cpf, payload.start_time, payload.end_time)

    reservation = Reservation(
        user_cpf=user_cpf,
        user_name=user_name,
        room=payload.room,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=ReservationStatus.pending,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation  # type: ignore[return-value]


@router.put(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Editar reserva",
)
def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    user_cpf: str = Query(..., description="CPF do usuário"),
    db: Session = Depends(get_db),
) -> Reservation:
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")

    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você não é o dono desta reserva")

    if reservation.status != ReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível editar/excluir reservas pendentes")

    new_room = payload.room if payload.room is not None else reservation.room
    new_start = payload.start_time if payload.start_time is not None else reservation.start_time
    new_end = payload.end_time if payload.end_time is not None else reservation.end_time

    _check_room_maintenance(db, new_room)
    _check_confirmed_conflict(db, new_room, new_start, new_end, exclude_id=reservation_id)
    _check_user_conflict(db, user_cpf, new_start, new_end, exclude_id=reservation_id)

    reservation.room = new_room
    reservation.start_time = new_start
    reservation.end_time = new_end

    db.commit()
    db.refresh(reservation)
    return reservation


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Cancelar reserva",
)
def cancel_reservation(
    reservation_id: int,
    user_cpf: str = Query(..., description="CPF do usuário"),
    db: Session = Depends(get_db),
) -> None:
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")

    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você não é o dono desta reserva")

    if reservation.status != ReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível editar/excluir reservas pendentes")

    reservation.status = ReservationStatus.denied
    db.commit()