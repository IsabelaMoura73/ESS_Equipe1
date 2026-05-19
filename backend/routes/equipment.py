from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.equipment import ComputerReservation, ComputerReservationStatus
from models.room import Room, RoomMaintenanceStatus
from schemas.equipment import ComputerReservationCreate, ComputerReservationResponse, ComputerReservationUpdate

router = APIRouter(prefix="/api/equipment/reservations", tags=["Reservas de Computadores"])

ACTIVE_STATUSES = [
    ComputerReservationStatus.pending,
    ComputerReservationStatus.confirmed,
]


def _get_room(db: Session, room_name: str) -> Room:
    room = db.query(Room).filter(Room.name == room_name).first()
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def _check_room_maintenance(room: Room) -> None:
    if room.maintenance_status != RoomMaintenanceStatus.no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is under maintenance. Computer reservation not allowed",
        )


def _check_student_time_conflict(
    db: Session,
    user_cpf: str,
    start_time,
    end_time,
    exclude_id: int | None = None,
) -> None:
    query = db.query(ComputerReservation).filter(
        ComputerReservation.user_cpf == user_cpf,
        ComputerReservation.status.in_(ACTIVE_STATUSES),
        ComputerReservation.start_time < end_time,
        ComputerReservation.end_time > start_time,
    )
    if exclude_id is not None:
        query = query.filter(ComputerReservation.id != exclude_id)

    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a reservation at this time",
        )


def _check_room_computer_capacity(
    db: Session,
    room: Room,
    start_time,
    end_time,
    requested_quantity: int,
    exclude_id: int | None = None,
) -> None:
    query = db.query(ComputerReservation).filter(
        ComputerReservation.room == room.name,
        ComputerReservation.status.in_(ACTIVE_STATUSES),
        ComputerReservation.start_time < end_time,
        ComputerReservation.end_time > start_time,
    )
    if exclude_id is not None:
        query = query.filter(ComputerReservation.id != exclude_id)

    reserved_quantity = sum(reservation.computer_quantity for reservation in query.all())
    available_quantity = room.computers - reserved_quantity
    if requested_quantity > available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available_quantity} computers are available in room '{room.name}' for this time",
        )


@router.post("/", response_model=ComputerReservationResponse, status_code=status.HTTP_201_CREATED)
def create_computer_reservation(
    payload: ComputerReservationCreate,
    user_cpf: str = Query(..., description="CPF do usuario"),
    user_name: str = Query(..., description="Nome do usuario"),
    db: Session = Depends(get_db),
) -> ComputerReservation:
    room = _get_room(db, payload.room)
    _check_room_maintenance(room)
    _check_student_time_conflict(db, user_cpf, payload.start_time, payload.end_time)
    _check_room_computer_capacity(db, room, payload.start_time, payload.end_time, payload.computer_quantity)

    reservation = ComputerReservation(
        user_cpf=user_cpf,
        user_name=user_name,
        room=room.name,
        computer_quantity=payload.computer_quantity,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=ComputerReservationStatus.pending,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("/", response_model=List[ComputerReservationResponse])
def list_computer_reservations(
    user_cpf: str = Query(..., description="CPF do usuario"),
    db: Session = Depends(get_db),
) -> list[ComputerReservation]:
    return (
        db.query(ComputerReservation)
        .filter(ComputerReservation.user_cpf == user_cpf)
        .order_by(ComputerReservation.start_time.desc())
        .all()
    )


@router.put("/{reservation_id}", response_model=ComputerReservationResponse)
def update_computer_reservation(
    reservation_id: int,
    payload: ComputerReservationUpdate,
    user_cpf: str = Query(..., description="CPF do usuario"),
    db: Session = Depends(get_db),
) -> ComputerReservation:
    reservation = db.query(ComputerReservation).filter(ComputerReservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if reservation.status != ComputerReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending reservations can be edited")

    new_room_name = payload.room if payload.room is not None else reservation.room
    new_quantity = payload.computer_quantity if payload.computer_quantity is not None else reservation.computer_quantity
    new_start = payload.start_time if payload.start_time is not None else reservation.start_time
    new_end = payload.end_time if payload.end_time is not None else reservation.end_time

    if new_end <= new_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")

    room = _get_room(db, new_room_name)
    _check_room_maintenance(room)
    _check_student_time_conflict(db, user_cpf, new_start, new_end, exclude_id=reservation_id)
    _check_room_computer_capacity(db, room, new_start, new_end, new_quantity, exclude_id=reservation_id)

    reservation.room = room.name
    reservation.computer_quantity = new_quantity
    reservation.start_time = new_start
    reservation.end_time = new_end

    db.commit()
    db.refresh(reservation)
    return reservation


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def cancel_computer_reservation(
    reservation_id: int,
    user_cpf: str = Query(..., description="CPF do usuario"),
    db: Session = Depends(get_db),
) -> None:
    reservation = db.query(ComputerReservation).filter(ComputerReservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if reservation.user_cpf != user_cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if reservation.status != ComputerReservationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending reservations can be canceled")

    db.delete(reservation)
    db.commit()
    return None
