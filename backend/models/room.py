import enum
from sqlalchemy import Column, String, Integer, Enum, Boolean, DateTime
from datetime import datetime, timezone
from database import Base

class RoomMaintenanceStatus(str, enum.Enum):
    no = "Não"
    yes = "Sim"
    scheduled = "Agendada"

class Room(Base):
    __tablename__ = "rooms"

    name = Column(String(100), primary_key=True, index=True)
    capacity = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    computers = Column(Integer, nullable=False)
    
    maintenance_status = Column(
        Enum(RoomMaintenanceStatus), 
        default=RoomMaintenanceStatus.no,
        nullable=False
    )
    is_reserved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<Room(name={self.name}, capacity={self.capacity})>"