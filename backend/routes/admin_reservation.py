"""
Feature: Verificação de Reservas (Administrador)

Endpoints:
  GET   /api/admin/reservations              → lista todas com prioridade para docentes
  GET   /api/admin/reservations/{id}         → detalhes (inclui flags can_confirm/can_deny)
  PATCH /api/admin/reservations/{id}/confirm → confirma reserva pendente
  PATCH /api/admin/reservations/{id}/deny    → nega reserva pendente
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case
from sqlalchemy.orm import Session

from database import get_db
from models.reservation import Reservation, ReservationStatus
from schemas.reservation import ReservationResponse
from schemas.admin_reservation import (
    AdminReservationDetail,
    AdminReservationListItem,
    AdminReservationActionResponse,
)

router = APIRouter(prefix="/api/admin/reservations", tags=["Administração de Reservas"])


# Sinônimos aceitos para identificação do papel "professor/docente"
TEACHER_TYPES = {"teacher", "docente", "professor"}


def _is_teacher(user_type: str | None) -> bool:
    if not user_type:
        return False
    return user_type.strip().lower() in TEACHER_TYPES


@router.get(
    "",
    response_model=List[AdminReservationListItem],
    summary="Listar todas as reservas (admin)",
    description=(
        "Lista todas as reservas do sistema. Reservas associadas a docentes/professores"
        " são exibidas antes das de discentes/alunos. Empate é resolvido por start_time."
    ),
)
def list_all_reservations(db: Session = Depends(get_db)) -> List[Reservation]:
    teacher_priority = case(
        (Reservation.user_type.in_(list(TEACHER_TYPES)), 0),
        else_=1,
    )
    reservations = (
        db.query(Reservation)
        .order_by(teacher_priority.asc(), Reservation.start_time.asc())
        .all()
    )
    return reservations


@router.get(
    "/{reservation_id}",
    response_model=AdminReservationDetail,
    summary="Detalhar reserva (admin)",
    description=(
        "Detalhes da reserva incluindo flags `can_confirm` e `can_deny`. Ambas são"
        " `false` quando a reserva já foi confirmada ou negada (somente leitura)."
    ),
)
def get_reservation_detail(reservation_id: int, db: Session = Depends(get_db)) -> AdminReservationDetail:
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva não encontrada",
        )

    can_act = reservation.status == ReservationStatus.pending
    return AdminReservationDetail(
        id=reservation.id,
        user_cpf=reservation.user_cpf,
        user_name=reservation.user_name,
        user_type=reservation.user_type,
        room=reservation.room,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status=reservation.status,
        can_confirm=can_act,
        can_deny=can_act,
        read_only_fields=["room", "start_time", "end_time", "user_cpf", "user_name"],
    )


def _decide(db: Session, reservation_id: int, new_status: ReservationStatus, success_msg: str):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva não encontrada",
        )
    if reservation.status != ReservationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reserva já decidida não pode ser alterada",
        )

    reservation.status = new_status
    db.commit()
    db.refresh(reservation)

    return AdminReservationActionResponse(
        message=success_msg,
        reservation=ReservationResponse.model_validate(reservation),
    )


@router.patch(
    "/{reservation_id}/confirm",
    response_model=AdminReservationActionResponse,
    summary="Confirmar reserva",
)
def confirm_reservation(reservation_id: int, db: Session = Depends(get_db)):
    return _decide(
        db, reservation_id, ReservationStatus.confirmed,
        "Reserva confirmada com sucesso",
    )


@router.patch(
    "/{reservation_id}/deny",
    response_model=AdminReservationActionResponse,
    summary="Negar reserva",
)
def deny_reservation(reservation_id: int, db: Session = Depends(get_db)):
    return _decide(
        db, reservation_id, ReservationStatus.denied,
        "Reserva negada com sucesso",
    )
