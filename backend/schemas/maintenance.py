from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date
from models.maintenance import MaintenanceStatus


# ── função utilitária compartilhada (Extract Method) ─────────────────────────

def validate_description_value(v: Optional[str]) -> str:
    """
    Extract Method: lógica de validação idêntica que existia duplicada em
    MaintenanceRequestCreate e MaintenanceRequestUpdate foi centralizada aqui.
    """
    if v is None or not str(v).strip():
        raise ValueError("O campo Descrição é obrigatório")
    if len(v) > 500:
        raise ValueError("Descrição muito longa")
    return v


# ── schemas ───────────────────────────────────────────────────────────────────

class MaintenanceRequestCreate(BaseModel):
    room: str
    description: Optional[str] = None

    @field_validator("description", mode="after")
    @classmethod
    def validate_description(cls, v):
        return validate_description_value(v)   # delega ao helper extraído


class MaintenanceRequestUpdate(BaseModel):
    description: Optional[str] = None

    @field_validator("description", mode="after")
    @classmethod
    def validate_description(cls, v):
        return validate_description_value(v)   # delega ao helper extraído


class MaintenanceRequestResponse(BaseModel):
    id: int
    teacher_cpf: str
    teacher_name: str
    room: str
    description: str
    status: MaintenanceStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    model_config = {"from_attributes": True}