# backend/models/room.py
import enum
from sqlalchemy import Column, String, Integer, Enum, Boolean, DateTime
from datetime import datetime
from database import Base


class RoomMaintenanceStatus(str, enum.Enum):
    no = "Não"
    yes = "Sim"
    scheduled = "Agendada"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    computers = Column(Integer, nullable=False)
    maintenance_status = Column(
        Enum(RoomMaintenanceStatus), 
        default=RoomMaintenanceStatus.no,
        nullable=False
    )
    is_reserved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Room(id={self.id}, name={self.name}, capacity={self.capacity})>"
