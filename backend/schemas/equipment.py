from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from models.equipment import ComputerReservationStatus


class ComputerReservationCreate(BaseModel):
    room: str
    computer_quantity: int
    start_time: datetime
    end_time: datetime

    @field_validator("room")
    @classmethod
    def validate_room(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("O nome da sala e obrigatorio")
        return value.strip()

    @model_validator(mode="after")
    def validate_reservation(self) -> ComputerReservationCreate:
        if self.computer_quantity <= 0:
            raise ValueError("A quantidade de computadores deve ser maior que zero")
        if self.end_time <= self.start_time:
            raise ValueError("O horario de fim deve ser posterior ao horario de inicio")
        return self


class ComputerReservationUpdate(BaseModel):
    room: Optional[str] = None
    computer_quantity: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("room")
    @classmethod
    def validate_room(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("O nome da sala nao pode ser vazio")
        return value.strip() if value else value

    @model_validator(mode="after")
    def validate_reservation(self) -> ComputerReservationUpdate:
        if self.computer_quantity is not None and self.computer_quantity <= 0:
            raise ValueError("A quantidade de computadores deve ser maior que zero")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("O horario de fim deve ser posterior ao horario de inicio")
        return self


class ComputerReservationResponse(BaseModel):
    id: int
    user_cpf: str
    user_name: str
    room: str
    computer_quantity: int
    start_time: datetime
    end_time: datetime
    status: ComputerReservationStatus

    model_config = {"from_attributes": True}
