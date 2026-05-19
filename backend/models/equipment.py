import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String

from database import Base


class ComputerReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    denied = "denied"
    completed = "completed"


class ComputerReservation(Base):
    __tablename__ = "equipment_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_cpf = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    room = Column(String, nullable=False)
    computer_quantity = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(
        Enum(ComputerReservationStatus, name="computer_reservation_status"),
        default=ComputerReservationStatus.pending,
        nullable=False,
    )
