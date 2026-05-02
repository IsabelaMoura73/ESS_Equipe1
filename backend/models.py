from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cpf = Column(String(14), unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # discente | docente | admin
    matricula = Column(String, nullable=True)
    curso = Column(String, nullable=True)
    siape = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)

    reservas_sala = relationship("RoomReservation", back_populates="usuario")
    reservas_lab = relationship("LabReservation", back_populates="usuario")
    manutencoes = relationship("MaintenanceRequest", back_populates="usuario")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    capacidade = Column(Integer, nullable=False)
    descricao = Column(String, nullable=True)
    qtd_computadores = Column(Integer, default=0)
    em_manutencao = Column(Boolean, default=False)

    reservas_sala = relationship("RoomReservation", back_populates="sala")
    reservas_lab = relationship("LabReservation", back_populates="sala")
    manutencoes = relationship("MaintenanceRequest", back_populates="sala")


class RoomReservation(Base):
    __tablename__ = "room_reservations"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sala_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    horario_inicio = Column(DateTime, nullable=False)
    horario_fim = Column(DateTime, nullable=False)
    status = Column(String, default="pendente")  # pendente | confirmada | negada | concluida | cancelada

    usuario = relationship("User", back_populates="reservas_sala")
    sala = relationship("Room", back_populates="reservas_sala")


class LabReservation(Base):
    __tablename__ = "lab_reservations"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sala_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    qtd_computadores = Column(Integer, nullable=False)
    horario_inicio = Column(DateTime, nullable=False)
    horario_fim = Column(DateTime, nullable=False)
    status = Column(String, default="pendente")

    usuario = relationship("User", back_populates="reservas_lab")
    sala = relationship("Room", back_populates="reservas_lab")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sala_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    descricao = Column(String, nullable=False)
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    status = Column(String, default="pendente")  # pendente | aprovada | negada

    usuario = relationship("User", back_populates="manutencoes")
    sala = relationship("Room", back_populates="manutencoes")
