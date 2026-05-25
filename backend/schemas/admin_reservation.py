from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from models.reservation import ReservationStatus
from schemas.reservation import ReservationResponse


class AdminReservationListItem(BaseModel):
    """Item da listagem do admin — inclui `user_type` para indicar prioridade."""

    id: int
    user_cpf: str
    user_name: str
    user_type: Optional[str] = None
    room: str
    start_time: datetime
    end_time: datetime
    status: ReservationStatus

    model_config = {"from_attributes": True}


class AdminReservationDetail(BaseModel):
    """
    Detalhe de reserva sob a perspectiva do administrador.

    `allowed_actions` informa quais operações o serviço aceita para esta reserva
    no estado atual. Reservas decididas (`confirmed`/`denied`/`completed`)
    retornam lista vazia — o serviço não permite mais alterar o status.
    """

    id: int
    user_cpf: str
    user_name: str
    user_type: Optional[str] = None
    room: str
    start_time: datetime
    end_time: datetime
    status: ReservationStatus
    allowed_actions: List[str]

    model_config = {"from_attributes": True}


class AdminReservationActionResponse(BaseModel):
    """Resposta padrão das ações Confirmar/Negar."""

    message: str
    reservation: ReservationResponse
