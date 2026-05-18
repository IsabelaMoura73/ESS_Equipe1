from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from models.equipment import EquipmentReservationStatus, EquipmentStatus


class EquipmentCreate(BaseModel):
    name: str
    total_quantity: int = 0
    status: EquipmentStatus = EquipmentStatus.available
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("O nome do equipamento e obrigatorio")
        return value.strip()

    @model_validator(mode="after")
    def validate_quantity(self) -> EquipmentCreate:
        if self.total_quantity < 0:
            raise ValueError("A quantidade total nao pode ser negativa")
        return self


class EquipmentResponse(BaseModel):
    id: int
    name: str
    total_quantity: int
    status: EquipmentStatus
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class EquipmentReservationCreate(BaseModel):
    equipment_type: str
    quantity: int
    pickup_time: datetime
    return_time: datetime

    @field_validator("equipment_type")
    @classmethod
    def validate_equipment_type(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("O tipo de equipamento e obrigatorio")
        return value.strip()

    @model_validator(mode="after")
    def validate_reservation(self) -> EquipmentReservationCreate:
        if self.quantity <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        if self.return_time <= self.pickup_time:
            raise ValueError("O horario de devolucao deve ser posterior ao horario de retirada")
        return self


class EquipmentReservationResponse(BaseModel):
    id: int
    user_cpf: str
    user_name: str
    equipment_type: str
    quantity: int
    pickup_time: datetime
    return_time: datetime
    status: EquipmentReservationStatus

    model_config = {"from_attributes": True}
