from __future__ import annotations
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from services.reservation import (
    cancel_reservation,
    create_reservation,
    update_reservation,
)

router = APIRouter(prefix="/api/reservations", tags=["Reservas de Sala"])


@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar reserva de sala",
)
def create_reservation_endpoint(
    payload: ReservationCreate,
    x_user_cpf: str = Header(..., alias="X-User-Cpf"),
    x_user_nome: str = Header(..., alias="X-User-Nome"),
    x_user_senha: str = Header(..., alias="X-User-Senha"),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    return create_reservation(db, x_user_cpf, x_user_nome, x_user_senha, payload)


@router.put(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Editar reserva",
)
def update_reservation_endpoint(
    reservation_id: int,
    payload: ReservationUpdate,
    x_user_cpf: str = Header(..., alias="X-User-Cpf"),
    x_user_nome: str = Header(..., alias="X-User-Nome"),
    x_user_senha: str = Header(..., alias="X-User-Senha"),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    return update_reservation(db, reservation_id, x_user_cpf, x_user_nome, x_user_senha, payload)


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Cancelar reserva",
)
def cancel_reservation_endpoint(
    reservation_id: int,
    x_user_cpf: str = Header(..., alias="X-User-Cpf"),
    x_user_nome: str = Header(..., alias="X-User-Nome"),
    x_user_senha: str = Header(..., alias="X-User-Senha"),
    db: Session = Depends(get_db),
) -> None:
    cancel_reservation(db, reservation_id, x_user_cpf, x_user_nome, x_user_senha)
