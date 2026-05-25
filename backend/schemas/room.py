# backend/schemas/room.py
from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import datetime
from models.room import RoomMaintenanceStatus


class RoomCreate(BaseModel):
    """Schema para criação de sala"""
    name: str = Field(..., min_length=1, max_length=100, description="Nome da sala")
    capacity: int = Field(..., gt=0, description="Capacidade da sala")
    description: Optional[str] = Field(None, max_length=500, description="Descrição da sala")
    computers: int = Field(..., ge=0, description="Número de computadores")
    maintenance_status: RoomMaintenanceStatus = Field(
        default=RoomMaintenanceStatus.no,
        description="Status de manutenção"
    )

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Nome da sala é obrigatório")
        if len(v) > 100:
            raise ValueError("Nome da sala não pode exceder 100 caracteres")
        return v.strip()

    @field_validator("capacity", mode="after")
    @classmethod
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("Capacidade deve ser maior que zero")
        if v > 500:
            raise ValueError("Capacidade não pode exceder 500 pessoas")
        return v

    @field_validator("computers", mode="after")
    @classmethod
    def validate_computers(cls, v):
        if v < 0:
            raise ValueError("Número de computadores não pode ser negativo")
        if v > 200:
            raise ValueError("Número de computadores não pode exceder 200")
        return v

    @field_validator("description", mode="after")
    @classmethod
    def validate_description(cls, v):
        if v and len(v) > 500:
            raise ValueError("Descrição não pode exceder 500 caracteres")
        return v


class RoomUpdate(BaseModel):
    """Schema para atualização de sala"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=500)
    computers: Optional[int] = Field(None, ge=0)
    maintenance_status: Optional[RoomMaintenanceStatus] = None
    is_reserved: Optional[bool] = None

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Nome da sala não pode estar vazio")
            if len(v) > 100:
                raise ValueError("Nome da sala não pode exceder 100 caracteres")
            return v.strip()
        return v

    @field_validator("capacity", mode="after")
    @classmethod
    def validate_capacity(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Capacidade deve ser maior que zero")
        return v

    @field_validator("computers", mode="after")
    @classmethod
    def validate_computers(cls, v):
        if v is not None and v < 0:
            raise ValueError("Número de computadores não pode ser negativo")
        return v

    @field_validator("description", mode="after")
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("Descrição não pode exceder 500 caracteres")
        return v


class RoomResponse(BaseModel):
    """Schema para resposta de sala"""
    name: str
    capacity: int
    description: Optional[str]
    computers: int
    maintenance_status: RoomMaintenanceStatus
    is_reserved: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoomListResponse(BaseModel):
    """Schema para listagem de salas"""
    total: int
    rooms: list[RoomResponse]
