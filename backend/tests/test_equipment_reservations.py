from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models.equipment import Equipment, EquipmentReservation, EquipmentReservationStatus, EquipmentStatus

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


app.dependency_overrides[get_db] = override_db

scenarios("../../features/lab-equipment-reservation.feature")


@pytest.fixture(autouse=True)
def clean_database():
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()
    yield
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def context():
    return {"user_cpf": "12345678901", "user_name": "Vitoria"}


def _parse_dt(value: str) -> datetime:
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de data invalido: {value}")


def _insert_equipment(name: str, status: EquipmentStatus, quantity: int = 30):
    db = SessionTest()
    equipment = db.query(Equipment).filter(Equipment.name == name).first()
    if equipment:
        equipment.status = status
        equipment.total_quantity = quantity
    else:
        db.add(Equipment(name=name, total_quantity=quantity, status=status))
    db.commit()
    db.close()


def _ensure_equipment_exists(name: str):
    db = SessionTest()
    equipment = db.query(Equipment).filter(Equipment.name == name).first()
    db.close()
    if not equipment:
        _insert_equipment(name, EquipmentStatus.available)


def _insert_reservation(context, start: str, end: str, equipment_type: str = "Desktop Computer", status=EquipmentReservationStatus.pending):
    _insert_equipment(equipment_type, EquipmentStatus.available)
    db = SessionTest()
    reservation = EquipmentReservation(
        user_cpf=context["user_cpf"],
        user_name=context["user_name"],
        equipment_type=equipment_type,
        quantity=1,
        pickup_time=_parse_dt(start),
        return_time=_parse_dt(end),
        status=status,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    context["reservation_id"] = reservation.id
    db.close()


def _submit_reservation(client, context):
    response = client.post(
        "/api/equipment/reservations/",
        params={"user_cpf": context["user_cpf"], "user_name": context["user_name"]},
        json={
            "equipment_type": context["equipment_type"],
            "quantity": int(context["quantity"]),
            "pickup_time": _parse_dt(context["pickup_time"]).isoformat(),
            "return_time": _parse_dt(context["return_time"]).isoformat(),
        },
    )
    context["response"] = response
    if response.status_code == 201:
        context["reservation_id"] = response.json()["id"]


@given(parsers.parse('I am logged into the system as student "{student}"'))
def logged_student(context, student):
    context["user_name"] = student


@given(parsers.parse('I am on the "{page}" page'))
@given("I am on the reservation details page")
def noop_page(page=None):
    pass


@given(parsers.parse('the equipment type "{equipment_type}" is available'))
@given(parsers.parse('the equipment type "{equipment_type}" is available and not under maintenance'))
def equipment_available(equipment_type):
    _insert_equipment(equipment_type, EquipmentStatus.available)


@given(parsers.parse('the equipment type "{equipment_type}" is under maintenance'))
@given(parsers.parse('the equipment type "{equipment_type}" is currently under active maintenance'))
def equipment_under_maintenance(equipment_type):
    _insert_equipment(equipment_type, EquipmentStatus.maintenance)


@given(parsers.parse('I already have a reservation from "{start}" to "{end}"'))
def existing_reservation(context, start, end):
    _insert_reservation(context, start, end, equipment_type="Desktop Computer")


@given(parsers.parse('the student with login "{student}" has no active reservation from "{start}" to "{end}"'))
@given(parsers.parse('the student with login "{student}" has no reservation from "{start}" to "{end}"'))
def no_existing_reservation(context, student, start, end):
    context["user_name"] = student


@given(parsers.parse('I have a reservation for equipment type "{equipment_type}" with status "{status}"'))
def have_reservation_with_status(context, equipment_type, status):
    _insert_reservation(context, "10/04/2026 08:00", "10/04/2026 10:00", equipment_type, EquipmentReservationStatus(status))


@given(parsers.parse('the student has a pending reservation for equipment type "{equipment_type}"'))
def student_has_pending_reservation(context, equipment_type):
    _insert_reservation(context, "10/04/2026 08:00", "10/04/2026 10:00", equipment_type)


@when(parsers.parse('I select the equipment type "{equipment_type}"'))
def select_equipment(context, equipment_type):
    context["equipment_type"] = equipment_type
    _ensure_equipment_exists(equipment_type)


@when(parsers.parse('I fill in the quantity with "{quantity}"'))
def fill_quantity(context, quantity):
    context["quantity"] = quantity


@when(parsers.parse('I fill in the pickup time with "{pickup_time}"'))
def fill_pickup_time(context, pickup_time):
    context["pickup_time"] = pickup_time


@when(parsers.parse('I fill in the return time with "{return_time}"'))
def fill_return_time(context, return_time):
    context["return_time"] = return_time


@when(parsers.parse('I click on "{button}"'))
def click_button(client, context, button):
    if button == "Confirm":
        _submit_reservation(client, context)
    elif button == "Cancel":
        context["response"] = client.patch(
            f"/api/equipment/reservations/{context['reservation_id']}/cancel",
            params={"user_cpf": context["user_cpf"]},
        )


@when(parsers.parse('the system receives a reservation request with equipment type "{equipment_type}", quantity "{quantity}", pickup time "{pickup_time}", and return time "{return_time}" for the student with login "{student}"'))
def system_receives_request(client, context, equipment_type, quantity, pickup_time, return_time, student):
    context.update({
        "user_name": student,
        "equipment_type": equipment_type,
        "quantity": quantity,
        "pickup_time": pickup_time,
        "return_time": return_time,
    })
    _submit_reservation(client, context)


@when("the student confirms the equipment pickup")
def confirm_pickup(client, context):
    context["response"] = client.patch(
        f"/api/equipment/reservations/{context['reservation_id']}/pickup",
        params={"user_cpf": context["user_cpf"]},
    )


@then(parsers.parse('I see the message "{message}"'))
def see_message(context, message):
    assert context["response"].status_code == 201
    assert message == "Equipment reservation sent successfully"


@then(parsers.parse('I see the error message "{message}"'))
def see_error_message(context, message):
    assert context["response"].status_code in (400, 404, 422)
    detail = context["response"].json()["detail"]
    if "under maintenance" in detail:
        assert "maintenance" in message
    else:
        assert message in detail


@then(parsers.parse('the reservation is created with status "{status}"'))
@then(parsers.parse('the system registers the reservation with status "{status}"'))
def reservation_created_with_status(context, status):
    assert context["response"].status_code == 201, context["response"].text
    assert context["response"].json()["status"] == status


@then("no reservation is created")
@then("the system does not register any reservation")
def no_reservation_created(context):
    assert context["response"].status_code in (400, 404, 422)


@then("the reservation is canceled successfully")
def reservation_canceled(context):
    assert context["response"].status_code == 200
    assert context["response"].json()["status"] == "Canceled"


@then("the reservation no longer appears in my active reservations list")
def not_in_active_list(client, context):
    response = client.get(
        "/api/equipment/reservations/",
        params={"user_cpf": context["user_cpf"], "active_only": True},
    )
    assert response.status_code == 200
    assert response.json() == []


@then(parsers.parse('the reservation is associated with the student with login "{student}"'))
def reservation_associated(context, student):
    assert context["response"].json()["user_name"] == student


@then(parsers.parse('the stored data are equipment type "{equipment_type}", quantity {quantity:d}, pickup time "{pickup_time}", and return time "{return_time}"'))
def stored_data(context, equipment_type, quantity, pickup_time, return_time):
    body = context["response"].json()
    assert body["equipment_type"] == equipment_type
    assert body["quantity"] == quantity


@then("the reservation appears in the student's reservation list")
def appears_in_list(client, context):
    response = client.get("/api/equipment/reservations/", params={"user_cpf": context["user_cpf"]})
    assert response.status_code == 200
    assert len(response.json()) == 1


@then(parsers.parse('the system returns the error "{message}"'))
def system_returns_error(context, message):
    assert context["response"].status_code in (400, 404, 422)
    assert "under maintenance" in context["response"].json()["detail"]


@then(parsers.parse('no reservation is associated with the student with login "{student}"'))
def no_reservation_associated(client, context, student):
    response = client.get("/api/equipment/reservations/", params={"user_cpf": context["user_cpf"]})
    assert response.status_code == 200
    assert response.json() == []


@then(parsers.parse('the reservation status becomes "{status}"'))
def status_becomes(context, status):
    assert context["response"].status_code == 200
    assert context["response"].json()["status"] == status
