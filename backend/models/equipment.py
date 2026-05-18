import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from database import Base


class EquipmentStatus(str, enum.Enum):
    available = "available"
    maintenance = "maintenance"


class EquipmentReservationStatus(str, enum.Enum):
    pending = "Pending"
    in_use = "In Use"
    canceled = "Canceled"


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    status = Column(
        Enum(EquipmentStatus, name="equipment_status"),
        default=EquipmentStatus.available,
        nullable=False,
    )
    total_quantity = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)


class EquipmentReservation(Base):
    __tablename__ = "equipment_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_cpf = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    pickup_time = Column(DateTime, nullable=False)
    return_time = Column(DateTime, nullable=False)
    status = Column(
        Enum(EquipmentReservationStatus, name="equipment_reservation_status"),
        default=EquipmentReservationStatus.pending,
        nullable=False,
    )
