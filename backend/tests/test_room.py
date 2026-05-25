# backend/tests/test_room.py
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
import models.room
from main import app

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

scenarios("../../features/room-service.feature")


@pytest.fixture(autouse=True)
def clean_database():
    app.dependency_overrides[get_db] = override_db
    with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def context():
    return {
        "payload": {},
        "response": None,
        "missing_field": None,
        "original_room": None,
    }


# ===================== GIVEN STEPS =====================

@given(parsers.re(r'nenhuma sala com nome "(?P<room_name>[^"]+)" existe no banco'))
def no_room_exists(client, context, room_name):
    client.delete(f"/api/rooms/{room_name}")


# parsers.re with [^"]+ prevents greedy cross-quote matching between overlapping patterns
@given(parsers.re(r'o corpo da requisição tem nome "(?P<room_name>[^"]+)", capacidade "(?P<capacity>[^"]+)", descrição "(?P<description>[^"]+)", computadores "(?P<computers>[^"]+)" e status de manutenção "(?P<maintenance>[^"]+)"'))
def set_full_body(context, room_name, capacity, description, computers, maintenance):
    context["payload"] = {
        "name": room_name,
        "capacity": int(capacity),
        "description": description,
        "computers": int(computers),
        "maintenance_status": maintenance,
    }


@given(parsers.re(r'o corpo da requisição faltando o campo "(?P<field>[^"]+)"'))
def body_missing_field(context, field):
    context["missing_field"] = field


@given(parsers.re(r'o corpo da requisição tem nome "(?P<room_name>[^"]+)", descrição "(?P<description>[^"]+)", computadores "(?P<computers>[^"]+)"$'))
def set_body_without_capacity(context, room_name, description, computers):
    payload = {
        "name": room_name,
        "description": description,
        "computers": int(computers),
    }
    if context.get("missing_field"):
        payload.pop(context["missing_field"], None)
    context["payload"] = payload


@given(parsers.re(r'o corpo da requisição tem nome "(?P<room_name>[^"]+)", capacidade "(?P<capacity>[^"]+)", computadores "(?P<computers>[^"]+)"$'))
def set_body_no_description(context, room_name, capacity, computers):
    context["payload"] = {
        "name": room_name,
        "capacity": int(capacity),
        "computers": int(computers),
    }


@given('o corpo da requisição tem nome "D005", capacidade "80", descrição com mais de 500 caracteres')
def set_body_long_description(context):
    context["payload"] = {
        "name": "D005",
        "capacity": 80,
        "description": "x" * 501,
        "computers": 20,
    }


@given(parsers.re(r'uma sala "(?P<room_name>[^"]+)" com capacidade "(?P<capacity>[^"]+)" e computadores "(?P<computers>[^"]+)" já existe no banco'))
def create_room_in_db(client, context, room_name, capacity, computers):
    payload = {
        "name": room_name,
        "capacity": int(capacity),
        "description": "Sala de teste",
        "computers": int(computers),
        "maintenance_status": "Não",
    }
    response = client.post("/api/rooms/", json=payload)
    assert response.status_code == 201
    context["original_room"] = response.json()


@given(parsers.re(r'uma sala "(?P<room_name>[^"]+)" com is_reserved "(?P<is_reserved>[^"]+)" existe'))
def create_room_with_reservation(client, context, room_name, is_reserved):
    payload = {
        "name": room_name,
        "capacity": 80,
        "description": "Sala de teste",
        "computers": 20,
        "maintenance_status": "Não",
    }
    response = client.post("/api/rooms/", json=payload)
    assert response.status_code == 201

    if is_reserved.lower() == "true":
        reserve_response = client.patch(f"/api/rooms/{room_name}/reserve")
        assert reserve_response.status_code == 200


# ===================== WHEN STEPS =====================

@when('uma requisição "POST" é enviada para "/api/rooms/" com os dados da sala')
def post_room_with_data(client, context):
    context["response"] = client.post("/api/rooms/", json=context["payload"])


@when('uma requisição "POST" é enviada para "/api/rooms/"')
def post_room(client, context):
    context["response"] = client.post("/api/rooms/", json=context["payload"])


@when(parsers.re(r'uma requisição "DELETE" é enviada para "/api/rooms/(?P<room_name>[^"]+)"'))
def delete_room_request(client, context, room_name):
    context["response"] = client.delete(f"/api/rooms/{room_name}")


# ===================== THEN STEPS =====================

@then(parsers.re(r'o status da resposta deve ser "(?P<status_code>[^"]+)"'))
def check_status_code(context, status_code):
    assert context["response"].status_code == int(status_code)


@then(parsers.re(r'a sala deve ser armazenada com name "(?P<room_name>[^"]+)" como primary key'))
def check_room_name_pk(context, room_name):
    data = context["response"].json()
    assert data["name"] == room_name


@then(parsers.re(r'a sala deve ter "(?P<field>[^"]+)" preenchido automaticamente'))
def check_field_auto_filled(context, field):
    data = context["response"].json()
    assert field in data
    assert data[field] is not None


@then(parsers.re(r'a mensagem de resposta deve conter "(?P<message>[^"]+)"'))
def check_response_contains(context, message):
    body = str(context["response"].json())
    assert message in body


@then(parsers.re(r"a mensagem de resposta deve ser \"(?P<message>[^\"]+)\""))
def check_response_exact(context, message):
    data = context["response"].json()
    assert data.get("detail") == message


@then(parsers.re(r'a sala original mantém capacidade "(?P<capacity>[^"]+)" e computadores "(?P<computers>[^"]+)"'))
def check_original_room_unchanged(client, context, capacity, computers):
    room_name = context["original_room"]["name"]
    response = client.get(f"/api/rooms/{room_name}")
    assert response.status_code == 200
    data = response.json()
    assert data["capacity"] == int(capacity)
    assert data["computers"] == int(computers)


@then('a resposta não contém corpo')
def check_no_body(context):
    assert len(context["response"].content) == 0


@then(parsers.re(r'a sala "(?P<room_name>[^"]+)" não existe mais no banco'))
def check_room_deleted(client, context, room_name):
    response = client.get(f"/api/rooms/{room_name}")
    assert response.status_code == 404


@then(parsers.re(r'a sala "(?P<room_name>[^"]+)" ainda existe no banco'))
def check_room_still_exists(client, context, room_name):
    response = client.get(f"/api/rooms/{room_name}")
    assert response.status_code == 200
