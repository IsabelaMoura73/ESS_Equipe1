from __future__ import annotations
from fastapi import APIRouter, Depends, Query, status
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
    user_cpf: str = Query(..., description="CPF do usuário"),
    user_nome: str = Query(..., description="Nome do usuário"),
    user_senha: str = Query(..., description="Senha do usuário"),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    return create_reservation(db, user_cpf, user_nome, user_senha, payload)


@router.put(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Editar reserva",
)
def update_reservation_endpoint(
    reservation_id: int,
    payload: ReservationUpdate,
    user_cpf: str = Query(..., description="CPF do usuário"),
    user_nome: str = Query(..., description="Nome do usuário"),
    user_senha: str = Query(..., description="Senha do usuário"),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    return update_reservation(db, reservation_id, user_cpf, user_nome, user_senha, payload)


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Cancelar reserva",
)
def cancel_reservation_endpoint(
    reservation_id: int,
    user_cpf: str = Query(..., description="CPF do usuário"),
    user_nome: str = Query(..., description="Nome do usuário"),
    user_senha: str = Query(..., description="Senha do usuário"),
    db: Session = Depends(get_db),
) -> None:
    cancel_reservation(db, reservation_id, user_cpf, user_nome, user_senha)
