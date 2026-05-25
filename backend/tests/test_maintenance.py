import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models.maintenance
import models.room
from models.maintenance import MaintenanceRequest, MaintenanceStatus
from models.room import Room, RoomMaintenanceStatus
from schemas.maintenance import MaintenanceRequestCreate

scenarios("features/maintenance.feature")

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTest = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)

def override_get_db():
    db = SessionTest()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True, scope="session")
def create_tables():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.fixture(autouse=True)
def clean_database():
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.add(Room(
        name="Grad 2",
        capacity=30,
        description="Sala de testes",
        computers=10,
        maintenance_status=RoomMaintenanceStatus.no,
        is_reserved=False,
    ))
    db.commit()
    db.close()
    yield
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

@pytest.fixture(autouse=True)
def ensure_db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def context():
    return {}

# ── Givens ───────────────────────────────────────────────────────────────────

@given(parsers.parse('o MaintenanceService não tem uma solicitação pendente do professor "{teacher}" para a sala "{room}"'))
def no_pending_request(teacher, room):
    pass  # banco já limpo pelo clean_database

@given(parsers.parse('já existe uma solicitação com status "pending" do professor "{teacher}" para a sala "{room}"'))
def existing_pending_request(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": "Solicitação existente"}
    )
    context["existing_request"] = res.json()

@given(parsers.parse('o MaintenanceService não tem nenhuma sala com nome "{room}"'))
def no_room(room):
    pass  # sala não cadastrada no banco de testes

@given(parsers.parse('a sala "{room}" está com maintenance_status "yes"'))
def room_in_maintenance(context, room):
    db = SessionTest()
    db.query(Room).filter(Room.name == room).update(
        {"maintenance_status": RoomMaintenanceStatus.yes}
    )
    db.commit()
    db.close()

@given(parsers.parse('existe uma solicitação com status "pending" do professor "{teacher}" para a sala "{room}" com ID conhecido'))
def pending_request_known_id(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": "Solicitação para excluir"}
    )
    context["request"] = res.json()

@given(parsers.parse('existe uma solicitação com status "confirmed" do professor "{teacher}" para a sala "{room}" com ID conhecido'))
def confirmed_request_known_id(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": "Solicitação confirmada"}
    )
    request = res.json()
    db = SessionTest()
    db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request["id"]).update(
        {"status": MaintenanceStatus.confirmed}
    )
    db.commit()
    db.close()
    context["request"] = request

@given(parsers.parse('existe uma solicitação com status "pending" do professor "{teacher}" para a sala "{room}" com description "{description}" e ID conhecido'))
def pending_request_with_description(client, context, teacher, room, description):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": description}
    )
    context["request"] = res.json()

@given(parsers.parse('existe uma solicitação com status "confirmed" do professor "{teacher}" para a sala "{room}" com description "{description}" e ID conhecido'))
def confirmed_request_with_description(client, context, teacher, room, description):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": description}
    )
    request = res.json()
    db = SessionTest()
    db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request["id"]).update(
        {"status": MaintenanceStatus.confirmed}
    )
    db.commit()
    db.close()
    context["request"] = request

# ── Whens ─────────────────────────────────────────────────────────────────────

@when(parsers.parse('uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "{teacher}", room "{room}" e description "{description}"'))
def post_request(client, context, teacher, room, description):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": description}
    )
    context["response"] = res
    
@when(parsers.parse('uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "{teacher}", room "{room}" e description ""'))
def post_request_empty_description(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": ""}
    )
    context["response"] = res

@when(parsers.parse('uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "{teacher}", room "{room}" e description com "{length}" caracteres'))
def post_request_long_description(client, context, teacher, room, length):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_name": teacher},
        json={"room": room, "description": "a" * int(length)}
    )
    context["response"] = res

@when(parsers.parse('uma requisição "DELETE" for enviada para "/api/maintenance/{id}"'))
def delete_request(client, context):
    request_id = context["request"]["id"]
    res = client.delete(f"/api/maintenance/{request_id}")
    context["response"] = res

@when(parsers.parse('uma requisição "PUT" for enviada para "/api/maintenance/{id}" com description "{new_description}"'))
def put_request(client, context, new_description):
    request_id = context["request"]["id"]
    res = client.put(
        f"/api/maintenance/{request_id}",
        json={"description": new_description}
    )
    context["response"] = res

# ── Thens ─────────────────────────────────────────────────────────────────────

@then(parsers.parse('o status da resposta deve ser "{status_code}"'))
def check_status_code(context, status_code):
    assert context["response"].status_code == int(status_code)

@then(parsers.parse('o JSON da resposta deve conter status "{status}", room "{room}" e teacher_name "{teacher}"'))
def check_response_json(context, status, room, teacher):
    body = context["response"].json()
    assert body["status"] == status
    assert body["room"] == room
    assert body["teacher_name"] == teacher

@then(parsers.parse('o JSON da resposta deve conter a mensagem de erro "{message}"'))
def check_error_message(context, message):
    body = context["response"].json()
    detail = body.get("detail", "")
    if isinstance(detail, list):
        messages = [err.get("msg", "") for err in detail]
        assert any(message in msg for msg in messages)
    else:
        assert message in detail

@then(parsers.parse('o JSON da resposta deve conter description "{description}"'))
def check_description(context, description):
    assert context["response"].json()["description"] == description

@then(parsers.parse('o MaintenanceService não retorna mais essa solicitação para o professor "{teacher}"'))
def check_request_removed(client, context, teacher):
    listing = client.get(
        "/api/maintenance/my-requests",
        params={"teacher_name": teacher}
    )
    ids = [s["id"] for s in listing.json()]
    assert context["request"]["id"] not in ids

# ── Testes Unitários ──────────────────────────────────────────────────────────

def test_unitario_schema_rejeita_descricao_vazia():
    with pytest.raises(Exception):
        MaintenanceRequestCreate(room="Grad 2", description="")

def test_unitario_schema_rejeita_descricao_nula():
    with pytest.raises(Exception):
        MaintenanceRequestCreate(room="Grad 2", description=None)

def test_unitario_schema_rejeita_descricao_acima_de_500_caracteres():
    with pytest.raises(Exception):
        MaintenanceRequestCreate(room="Grad 2", description="a" * 501)

def test_unitario_schema_aceita_descricao_valida():
    obj = MaintenanceRequestCreate(room="Grad 2", description="Ar-condicionado com defeito")
    assert obj.room == "Grad 2"
    assert obj.description == "Ar-condicionado com defeito"

def test_unitario_schema_rejeita_descricao_so_espacos():
    with pytest.raises(Exception):
        MaintenanceRequestCreate(room="Grad 2", description="     ")