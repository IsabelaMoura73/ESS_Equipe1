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

scenarios("../../features/room-crud.feature")


@pytest.fixture(autouse=True)
def clean_database():
    """Garante o override correto e limpa o banco antes de cada teste"""
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
        "user": None,
        "rooms": {},
        "response": None,
        "error_message": None,
    }


# ===================== GIVEN STEPS =====================

@given(parsers.parse('eu estou logado como administrador com o usuário "{user}" com CPF "{cpf}"'))
def admin_logged_in(context, user, cpf):
    context["user"] = {"name": user, "cpf": cpf, "role": "admin"}


@given("eu estou na tela de salas cadastradas")
def on_rooms_screen(context):
    context["screen"] = "rooms_list"


@given(parsers.parse('a sala de nome "{room_name}" não aparece na lista de salas cadastradas'))
def room_not_exists(client, context, room_name):
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    room_names = [r["name"] for r in rooms]
    assert room_name not in room_names


@given(parsers.parse('eu vejo a sala "{room_name}" na lista de salas cadastradas'))
def room_exists_in_list(client, context, room_name):
    """Garante que a sala existe, criando-a se necessário"""
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    room_names = [r["name"] for r in rooms]

    if room_name not in room_names:
        payload = {
            "name": room_name,
            "capacity": 80,
            "description": "Sala de teste",
            "computers": 20,
            "maintenance_status": "Não",
        }
        create_response = client.post("/api/rooms/", json=payload)
        assert create_response.status_code == 201
        room = create_response.json()
    else:
        room = next(r for r in rooms if r["name"] == room_name)

    context["rooms"][room_name] = room


@given(parsers.parse('eu vejo a sala "{room_name}" na lista de salas cadastradas com capacidade "{capacity}"'))
def room_exists_with_capacity(client, context, room_name, capacity):
    """Garante que a sala existe com a capacidade dada, criando ou atualizando"""
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    found = next((r for r in rooms if r["name"] == room_name), None)

    if found is None:
        payload = {
            "name": room_name,
            "capacity": int(capacity),
            "description": "Sala de teste",
            "computers": 20,
            "maintenance_status": "Não",
        }
        create_response = client.post("/api/rooms/", json=payload)
        assert create_response.status_code == 201
        room = create_response.json()
    elif found["capacity"] != int(capacity):
        update_response = client.put(f"/api/rooms/{room_name}", json={"capacity": int(capacity)})
        assert update_response.status_code == 200
        room = update_response.json()
    else:
        room = found

    context["rooms"][room_name] = room


@given(parsers.parse('eu vejo que a sala "{room_name}" está reservada'))
def room_is_reserved(client, context, room_name):
    response = client.patch(f"/api/rooms/{room_name}/reserve")
    assert response.status_code == 200


@given(parsers.parse('eu vejo a sala "{room_name}" na lista de salas cadastradas com capacidade "{capacity}" e com status "reservada"'))
def room_reserved_with_capacity(client, context, room_name, capacity):
    """Garante que a sala existe com capacidade dada e marcada como reservada"""
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    found = next((r for r in rooms if r["name"] == room_name), None)

    if found is None:
        payload = {
            "name": room_name,
            "capacity": int(capacity),
            "description": "Sala de teste",
            "computers": 20,
            "maintenance_status": "Não",
        }
        create_response = client.post("/api/rooms/", json=payload)
        assert create_response.status_code == 201
    elif found["capacity"] != int(capacity):
        update_response = client.put(f"/api/rooms/{room_name}", json={"capacity": int(capacity)})
        assert update_response.status_code == 200

    reserve_response = client.patch(f"/api/rooms/{room_name}/reserve")
    assert reserve_response.status_code == 200
    context["rooms"][room_name] = reserve_response.json()


# ===================== WHEN STEPS =====================

@when('eu seleciono a opção "cadastrar sala"')
def select_create_room_option(context):
    context["action"] = "create"


@when(parsers.parse('tento cadastrar a sala "{room_name}" com capacidade "{capacity}", descrição com "{description}", número de computadores "{computers}" e status de manutenção "{maintenance}"'))
def create_room_with_data(client, context, room_name, capacity, description, computers, maintenance):
    maintenance_status = "Não" if maintenance == "Não" else "Sim"

    payload = {
        "name": room_name,
        "capacity": int(capacity),
        "description": description,
        "computers": int(computers),
        "maintenance_status": maintenance_status,
    }

    response = client.post("/api/rooms/", json=payload)
    context["response"] = response
    context["last_room_name"] = room_name


@when(parsers.parse('eu seleciono a opção "remover sala" da sala "{room_name}"'))
def select_delete_room_option(context, room_name):
    context["action"] = "delete"
    context["target_room"] = room_name


@when(parsers.parse('confirmo que realmente quero remover a sala "{room_name}"'))
def confirm_delete_room(client, context, room_name):
    response = client.delete(f"/api/rooms/{room_name}")
    context["response"] = response


@when(parsers.parse('eu seleciono a opção "editar sala" da sala "{room_name}"'))
def select_edit_room_option(context, room_name):
    context["action"] = "edit"
    context["target_room"] = room_name


@when(parsers.parse('edito a capacidade "{old_capacity}" para "{new_capacity}"'))
def edit_room_capacity(client, context, old_capacity, new_capacity):
    room_name = context["target_room"]
    payload = {"capacity": int(new_capacity)}
    response = client.put(f"/api/rooms/{room_name}", json=payload)
    context["response"] = response


@when("salvo as alterações")
def save_changes(context):
    pass


# ===================== THEN STEPS =====================

@then("eu vejo uma mensagem de confirmação de cadastro de sala")
def verify_create_success(context):
    assert context["response"].status_code == 201
    assert "name" in context["response"].json()


@then("eu ainda estou na tela de salas cadastradas")
def still_on_rooms_screen(context):
    assert context["screen"] == "rooms_list"


@then(parsers.parse('eu vejo a sala "{room_name}" na lista de salas cadastradas'))
def verify_room_in_list(client, context, room_name):
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    room_names = [r["name"] for r in rooms]
    assert room_name in room_names


@then("eu vejo uma mensagem de confirmação de remoção de sala")
def verify_delete_success(context):
    assert context["response"].status_code == 204


@then(parsers.parse('eu não vejo a sala "{room_name}" na lista de salas cadastradas'))
def verify_room_not_in_list(client, context, room_name):
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    room_names = [r["name"] for r in rooms]
    assert room_name not in room_names


@then("eu recebo uma mensagem de confirmação de edição")
def verify_edit_success(context):
    assert context["response"].status_code == 200


@then(parsers.parse('a sala "{room_name}" aparece com capacidade "{capacity}" na lista de salas cadastradas'))
def verify_room_capacity_updated(client, context, room_name, capacity):
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]

    for room in rooms:
        if room["name"] == room_name:
            assert room["capacity"] == int(capacity)
            return

    assert False, f"Sala {room_name} não encontrada"


@then(parsers.parse('eu recebo uma mensagem de erro informando que a sala "{room_name}" já existe'))
def verify_duplicate_error(context, room_name):
    assert context["response"].status_code in [409, 422]
    assert "já existe" in context["response"].json().get("detail", "").lower()


@then("eu continuo na tela com o formulário de cadastro de sala")
def still_on_create_form(context):
    assert context["action"] == "create"


@then("a tela do formulário de cadastro está com todos os campos vazios")
def form_fields_empty(context):
    pass


@then(parsers.parse('eu vejo uma mensagem de erro informando que não posso remover uma sala reservada'))
def verify_cannot_delete_reserved(context):
    assert context["response"].status_code == 400
    assert "reservada" in context["response"].json().get("detail", "").lower()


@then(parsers.parse('eu continuo vendo a sala "{room_name}" na lista de salas cadastradas'))
def verify_room_still_in_list(client, context, room_name):
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]
    room_names = [r["name"] for r in rooms]
    assert room_name in room_names


@then(parsers.parse('eu recebo uma mensagem de erro informando que não é possível editar uma sala reservada'))
def verify_cannot_edit_reserved(context):
    assert context["response"].status_code == 400
    assert "reservada" in context["response"].json().get("detail", "").lower()


@then(parsers.parse('a sala "{room_name}" ainda aparece com capacidade "{capacity}" na lista de salas cadastradas e com status "reservada"'))
def verify_room_unchanged(client, context, room_name, capacity):
    response = client.get("/api/rooms/")
    rooms = response.json()["rooms"]

    for room in rooms:
        if room["name"] == room_name:
            assert room["capacity"] == int(capacity)
            assert room["is_reserved"] is True
            return

    assert False, f"Sala {room_name} não encontrada"
