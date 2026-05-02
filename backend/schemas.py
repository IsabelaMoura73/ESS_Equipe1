from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    nome: str
    cpf: str
    senha: str = Field(max_length=128)
    tipo: str  # discente | docente | admin
    matricula: Optional[str] = None
    curso: Optional[str] = None
    siape: Optional[str] = None


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    senha: str  # senha atual — obrigatória para confirmar identidade
    nova_senha: Optional[str] = Field(default=None, max_length=128)


class UserOut(BaseModel):
    id: int
    nome: str
    cpf: str
    tipo: str
    matricula: Optional[str]
    curso: Optional[str]
    siape: Optional[str]
    ativo: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    cpf: str
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── Room ──────────────────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    nome: str
    capacidade: int
    descricao: Optional[str] = None
    qtd_computadores: int = 0


class RoomUpdate(BaseModel):
    nome: Optional[str] = None
    capacidade: Optional[int] = None
    descricao: Optional[str] = None
    qtd_computadores: Optional[int] = None
    em_manutencao: Optional[bool] = None


class RoomOut(BaseModel):
    id: int
    nome: str
    capacidade: int
    descricao: Optional[str]
    qtd_computadores: int
    em_manutencao: bool

    model_config = {"from_attributes": True}


# ── Reservations ──────────────────────────────────────────────────────────────

class RoomReservationCreate(BaseModel):
    sala_id: int
    horario_inicio: datetime
    horario_fim: datetime


class LabReservationCreate(BaseModel):
    sala_id: int
    qtd_computadores: int
    horario_inicio: datetime
    horario_fim: datetime


class RoomReservationOut(BaseModel):
    id: int
    usuario_id: int
    sala_id: int
    horario_inicio: datetime
    horario_fim: datetime
    status: str

    model_config = {"from_attributes": True}


class LabReservationOut(BaseModel):
    id: int
    usuario_id: int
    sala_id: int
    qtd_computadores: int
    horario_inicio: datetime
    horario_fim: datetime
    status: str

    model_config = {"from_attributes": True}


# ── Maintenance ───────────────────────────────────────────────────────────────

class MaintenanceCreate(BaseModel):
    sala_id: int
    descricao: str
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None


class MaintenanceOut(BaseModel):
    id: int
    usuario_id: int
    sala_id: int
    descricao: str
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    status: str

    model_config = {"from_attributes": True}
