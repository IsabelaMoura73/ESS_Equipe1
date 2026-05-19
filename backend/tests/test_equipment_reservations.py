from datetime import datetime, timezone
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from database import Base, get_db
from models.equipment import ComputerReservation, ComputerReservationStatus
from models.room import Room, RoomMaintenanceStatus
from routes.equipment import (
    cancel_computer_reservation,
    create_computer_reservation,
    list_computer_reservations,
    update_computer_reservation,
)
from schemas.equipment import ComputerReservationCreate, ComputerReservationUpdate

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTest = sessionmaker(bind=engine_test)

Base.metadata.create_all(bind=engine_test)


def override_db():
    db = SessionTest()
    try:
        yield db
    finally:
        db.close()


scenarios("../../features/lab-equipment-reservation.feature")


@pytest.fixture(autouse=True)
def clean_database():
    db = SessionTest()
    db.query(ComputerReservation).delete()
    db.query(Room).delete()
    db.commit()
    db.close()
    yield
    db = SessionTest()
    db.query(ComputerReservation).delete()
    db.query(Room).delete()
    db.commit()
    db.close()


@pytest.fixture
def context():
    return {}


def _parse_dt(value: str) -> datetime:
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de data invalido: {value}")


def _insert_room(name: str, computers: int, maintenance_status: RoomMaintenanceStatus):
    db = SessionTest()
    db.add(
        Room(
            name=name,
            capacity=30,
            description="Sala de teste",
            computers=computers,
            maintenance_status=maintenance_status,
            is_reserved=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.close()


def _insert_reservation(
    context,
    user_name: str,
    user_cpf: str,
    room: str,
    quantity: int,
    start_time: str,
    end_time: str,
    status: ComputerReservationStatus = ComputerReservationStatus.pending,
):
    db = SessionTest()
    reservation = ComputerReservation(
        user_cpf=user_cpf,
        user_name=user_name,
        room=room,
        computer_quantity=quantity,
        start_time=_parse_dt(start_time),
        end_time=_parse_dt(end_time),
        status=status,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    context["reservation_id"] = reservation.id
    db.close()


def _request_body(context):
    return {
        "room": context["body"]["room"],
        "computer_quantity": int(context["body"]["computer_quantity"]),
        "start_time": _parse_dt(context["body"]["start_time"]).isoformat(),
        "end_time": _parse_dt(context["body"]["end_time"]).isoformat(),
    }


def _success_response(status_code: int, body=None):
    return SimpleNamespace(status_code=status_code, text=str(body), json=lambda: body)


def _error_response(exc: HTTPException):
    body = {"detail": exc.detail}
    return SimpleNamespace(status_code=exc.status_code, text=str(body), json=lambda: body)


def _response_body(reservation: ComputerReservation):
    return {
        "id": reservation.id,
        "user_cpf": reservation.user_cpf,
        "user_name": reservation.user_name,
        "room": reservation.room,
        "computer_quantity": reservation.computer_quantity,
        "start_time": reservation.start_time.isoformat(),
        "end_time": reservation.end_time.isoformat(),
        "status": reservation.status.value,
    }


@given(parsers.parse('the room "{room}" has {computers:d} computers and is not under maintenance'))
def room_not_under_maintenance(room, computers):
    _insert_room(room, computers, RoomMaintenanceStatus.no)


@given(parsers.parse('the room "{room}" has {computers:d} computers and is under maintenance'))
def room_under_maintenance(room, computers):
    _insert_room(room, computers, RoomMaintenanceStatus.yes)


@given(parsers.parse('student "{student}" with CPF "{cpf}" has no reservation from "{start}" to "{end}"'))
def student_has_no_reservation(context, student, cpf, start, end):
    context["user_name"] = student
    context["user_cpf"] = cpf


@given(parsers.parse('student "{student}" with CPF "{cpf}" has a reservation for "{quantity}" computers in room "{room}" from "{start}" to "{end}"'))
def student_has_reservation(context, student, cpf, quantity, room, start, end):
    _insert_reservation(context, student, cpf, room, int(quantity), start, end)


@given(parsers.parse('student "{student}" with CPF "{cpf}" has a pending reservation for "{quantity}" computers in room "{room}" from "{start}" to "{end}"'))
def student_has_pending_reservation(context, student, cpf, quantity, room, start, end):
    _insert_reservation(context, student, cpf, room, int(quantity), start, end, ComputerReservationStatus.pending)


@given(parsers.parse('student "{student}" with CPF "{cpf}" has a confirmed reservation for "{quantity}" computers in room "{room}" from "{start}" to "{end}"'))
def student_has_confirmed_reservation(context, student, cpf, quantity, room, start, end):
    _insert_reservation(context, student, cpf, room, int(quantity), start, end, ComputerReservationStatus.confirmed)


@given(parsers.parse('the request body has room "{room}", computer quantity "{quantity}", start time "{start}", and end time "{end}"'))
def request_body(context, room, quantity, start, end):
    context["body"] = {
        "room": room,
        "computer_quantity": quantity,
        "start_time": start,
        "end_time": end,
    }


@given(parsers.parse('the update body has room "{room}", computer quantity "{quantity}", start time "{start}", and end time "{end}"'))
def update_body(context, room, quantity, start, end):
    request_body(context, room, quantity, start, end)


@when(parsers.parse('a "POST" request is sent to "/api/equipment/reservations/" for student "{student}" with CPF "{cpf}"'))
def post_reservation(context, student, cpf):
    context["user_name"] = student
    context["user_cpf"] = cpf
    db = SessionTest()
    try:
        payload = ComputerReservationCreate(**_request_body(context))
        reservation = create_computer_reservation(payload, user_cpf=cpf, user_name=student, db=db)
        context["reservation_id"] = reservation.id
        context["response"] = _success_response(201, _response_body(reservation))
    except HTTPException as exc:
        context["response"] = _error_response(exc)
    finally:
        db.close()


@when(parsers.parse('a "GET" request is sent to "/api/equipment/reservations/" for CPF "{cpf}"'))
def get_reservations(context, cpf):
    context["user_cpf"] = cpf
    db = SessionTest()
    reservations = list_computer_reservations(user_cpf=cpf, db=db)
    context["response"] = _success_response(200, [_response_body(reservation) for reservation in reservations])
    db.close()


@when(parsers.parse('a "PUT" request is sent to "/api/equipment/reservations/{reservation_id}" for CPF "{cpf}"'))
def put_reservation(context, reservation_id, cpf):
    db = SessionTest()
    try:
        payload = ComputerReservationUpdate(**_request_body(context))
        reservation = update_computer_reservation(context["reservation_id"], payload, user_cpf=cpf, db=db)
        context["response"] = _success_response(200, _response_body(reservation))
    except HTTPException as exc:
        context["response"] = _error_response(exc)
    finally:
        db.close()


@when(parsers.parse('a "DELETE" request is sent to "/api/equipment/reservations/{reservation_id}" for CPF "{cpf}"'))
def delete_reservation(context, reservation_id, cpf):
    db = SessionTest()
    try:
        cancel_computer_reservation(context["reservation_id"], user_cpf=cpf, db=db)
        context["response"] = _success_response(204)
    except HTTPException as exc:
        context["response"] = _error_response(exc)
    finally:
        db.close()


@then(parsers.parse('the response status should be "{status_code:d}"'))
def response_status(context, status_code):
    assert context["response"].status_code == status_code, context["response"].text


@then(parsers.parse('the response message should be "{message}"'))
def response_message(context, message):
    assert context["response"].json()["detail"] == message


@then(parsers.parse('the reservation should be stored with status "{status}"'))
def reservation_stored_with_status(context, status):
    body = context["response"].json()
    assert body["status"] == status


@then(parsers.parse('the stored reservation should have room "{room}", computer quantity "{quantity}", start time "{start}", and end time "{end}"'))
def stored_reservation_data(context, room, quantity, start, end):
    body = context["response"].json()
    assert body["room"] == room
    assert body["computer_quantity"] == int(quantity)
    assert body["start_time"].startswith(_parse_dt(start).isoformat())
    assert body["end_time"].startswith(_parse_dt(end).isoformat())


@then(parsers.parse('no reservation should be stored for student CPF "{cpf}"'))
def no_reservation_stored(cpf):
    db = SessionTest()
    count = db.query(ComputerReservation).filter(ComputerReservation.user_cpf == cpf).count()
    db.close()
    assert count == 0


@then(parsers.parse('the reservation list should contain room "{room}", status "{status}", and computer quantity "{quantity}"'))
def list_contains_reservation(context, room, status, quantity):
    body = context["response"].json()
    assert len(body) == 1
    assert body[0]["room"] == room
    assert body[0]["status"] == status
    assert body[0]["computer_quantity"] == int(quantity)


@then("the reservation should no longer be stored")
def reservation_no_longer_stored(context):
    db = SessionTest()
    reservation = db.query(ComputerReservation).filter(ComputerReservation.id == context["reservation_id"]).first()
    db.close()
    assert reservation is None
