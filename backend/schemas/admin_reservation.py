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
    Detalhe usado pelo administrador. Inclui flags indicando se as ações
    `Confirmar`/`Negar` estão habilitadas (apenas para reservas pendentes)
    e a lista de campos que devem ser tratados como somente-leitura na UI.
    """

    id: int
    user_cpf: str
    user_name: str
    user_type: Optional[str] = None
    room: str
    start_time: datetime
    end_time: datetime
    status: ReservationStatus
    can_confirm: bool
    can_deny: bool
    read_only_fields: List[str]

    model_config = {"from_attributes": True}


class AdminReservationActionResponse(BaseModel):
    """Resposta padrão das ações Confirmar/Negar."""

    message: str
    reservation: ReservationResponse
