# backend/services/reservation.py
from __future__ import annotations
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.reservation import Reservation, ReservationStatus
from schemas.reservation import ReservationCreate, ReservationUpdate

try:
    from models.room import Room, RoomMaintenanceStatus  # type: ignore
    _ROOM_MODEL_AVAILABLE = True
except ImportError:
    _ROOM_MODEL_AVAILABLE = False


def _check_room_exists_and_not_in_maintenance(db: Session, room_name: str) -> None:
    if not _ROOM_MODEL_AVAILABLE:
        return
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


def create_reservation(
    db: Session, user_cpf: str, user_name: str, data: ReservationCreate
) -> Reservation:
    _check_room_exists_and_not_in_maintenance(db, data.room)
    _check_confirmed_conflict(db, data.room, data.start_time, data.end_time)
    _check_user_conflict(db, user_cpf, data.start_time, data.end_time)
    reservation = Reservation(
        user_cpf=user_cpf,
        user_name=user_name,
        room=data.room,
        start_time=data.start_time,
        end_time=data.end_time,
        status=ReservationStatus.pending,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def update_reservation(
    db: Session, reservation_id: int, user_cpf: str, data: ReservationUpdate
) -> Reservation:
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")
    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você não é o dono desta reserva")
    if reservation.status != ReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível editar/excluir reservas pendentes")
    new_room  = data.room       if data.room       is not None else reservation.room
    new_start = data.start_time if data.start_time is not None else reservation.start_time
    new_end   = data.end_time   if data.end_time   is not None else reservation.end_time
    _check_room_exists_and_not_in_maintenance(db, new_room)
    _check_confirmed_conflict(db, new_room, new_start, new_end, exclude_id=reservation_id)
    _check_user_conflict(db, user_cpf, new_start, new_end, exclude_id=reservation_id)
    reservation.room       = new_room
    reservation.start_time = new_start
    reservation.end_time   = new_end
    db.commit()
    db.refresh(reservation)
    return reservation


def cancel_reservation(db: Session, reservation_id: int, user_cpf: str) -> None:
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")
    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: você não é o dono desta reserva")
    if reservation.status != ReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Só é possível editar/excluir reservas pendentes")
    reservation.status = ReservationStatus.denied
    db.commit()
