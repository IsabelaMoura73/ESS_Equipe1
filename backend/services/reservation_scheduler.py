from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from database import SessionLocal
from models.reservation import Reservation, ReservationStatus

_BRT = timezone(timedelta(hours=-3))


def _expire_reservations() -> None:
    now = datetime.now(_BRT).replace(tzinfo=None)
    db = SessionLocal()
    try:
        # pending cuja start_time já passou → denied
        db.query(Reservation).filter(
            Reservation.status == ReservationStatus.pending,
            Reservation.start_time <= now,
        ).update({"status": ReservationStatus.denied}, synchronize_session=False)

        # confirmed cuja end_time já passou → completed
        db.query(Reservation).filter(
            Reservation.status == ReservationStatus.confirmed,
            Reservation.end_time <= now,
        ).update({"status": ReservationStatus.completed}, synchronize_session=False)

        db.commit()
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(_expire_reservations, "interval", minutes=1)
    scheduler.start()
    return scheduler
