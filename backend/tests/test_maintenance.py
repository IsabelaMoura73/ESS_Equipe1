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
import models.user
from models.maintenance import MaintenanceRequest, MaintenanceStatus
from models.room import Room, RoomMaintenanceStatus
from models.user import User, UserRole
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
    db.add(User(
        nome="Breno Miranda",
        cpf="11111111111",
        senha="senha123",
        tipo=UserRole.DOCENTE,
        status=True,
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

@given(parsers.parse('o sistema não possui solicitação pendente do professor "{teacher}" para a sala "{room}"'))
def no_pending_request(teacher, room):
    pass

@given(parsers.parse('já existe uma solicitação com status "pending" do professor "{teacher}" para a sala "{room}"'))
def existing_pending_request(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
        json={"room": room, "description": "Solicitação existente"}
    )
    context["existing_request"] = res.json()

@given(parsers.parse('o sistema não possui nenhuma sala com nome "{room}"'))
def no_room(room):
    pass

@given(parsers.parse('a sala "{room}" está em manutenção no sistema'))
def room_in_maintenance(context, room):
    db = SessionTest()
    db.query(Room).filter(Room.name == room).update(
        {"maintenance_status": RoomMaintenanceStatus.yes}
    )
    db.commit()
    db.close()

@given(parsers.parse('o sistema possui uma solicitação com status "pending" do professor "{teacher}" para a sala "{room}"'))
def pending_request_known_id(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
        json={"room": room, "description": "Solicitação para excluir"}
    )
    context["request"] = res.json()

@given(parsers.parse('o sistema possui uma solicitação com status "confirmed" do professor "{teacher}" para a sala "{room}"'))
def confirmed_request_known_id(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
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

@given(parsers.parse('o sistema possui uma solicitação com status "pending" do professor "{teacher}" para a sala "{room}" com descrição "{description}"'))
def pending_request_with_description(client, context, teacher, room, description):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
        json={"room": room, "description": description}
    )
    context["request"] = res.json()

@given(parsers.parse('o sistema possui uma solicitação com status "confirmed" do professor "{teacher}" para a sala "{room}" com descrição "{description}"'))
def confirmed_request_with_description(client, context, teacher, room, description):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
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

@when(parsers.parse('o sistema recebe uma solicitação do professor "{teacher}" para a sala "{room}" com descrição "{description}"'))
def post_request(client, context, teacher, room, description):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
        json={"room": room, "description": description}
    )
    context["response"] = res

@when(parsers.parse('o sistema recebe uma solicitação do professor "{teacher}" para a sala "{room}" sem descrição'))
def post_request_empty_description(client, context, teacher, room):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
        json={"room": room, "description": ""}
    )
    context["response"] = res

@when(parsers.parse('o sistema recebe uma solicitação do professor "{teacher}" para a sala "{room}" com descrição de {length:d} caracteres'))
def post_request_long_description(client, context, teacher, room, length):
    res = client.post(
        "/api/maintenance/",
        params={"teacher_cpf": "11111111111"},
        json={"room": room, "description": "a" * length}
    )
    context["response"] = res

@when('o sistema recebe uma requisição de exclusão dessa solicitação pelo seu ID')
def delete_request(client, context):
    request_id = context["request"]["id"]
    res = client.delete(
        f"/api/maintenance/{request_id}",
        params={"teacher_cpf": "11111111111"}
    )
    context["response"] = res

@when(parsers.parse('o sistema recebe uma requisição de edição dessa solicitação pelo seu ID com descrição "{new_description}"'))
def put_request(client, context, new_description):
    request_id = context["request"]["id"]
    res = client.put(
        f"/api/maintenance/{request_id}",
        params={"teacher_cpf": "11111111111"},
        json={"description": new_description}
    )
    context["response"] = res

@then(parsers.parse('o sistema registra a solicitação com status "{status}"'))
def check_status(context, status):
    assert context["response"].status_code == 201
    assert context["response"].json()["status"] == status

@then('o sistema retorna confirmação de sucesso')
def check_success(context):
    assert context["response"].status_code == 201

@then('o sistema não registra a solicitação')
def check_not_created(context):
    assert context["response"].status_code in [400, 404, 422]

@then(parsers.parse('o sistema retorna o erro "{message}"'))
def check_error_message(context, message):
    body = context["response"].json()
    detail = body.get("detail", "")
    if isinstance(detail, list):
        messages = [err.get("msg", "") for err in detail]
        assert any(message in msg for msg in messages)
    else:
        assert message in detail

@then('o sistema remove a solicitação com sucesso')
def check_deletion_success(context):
    assert context["response"].status_code == 204

@then(parsers.parse('o sistema não retorna mais essa solicitação para o professor "{teacher}"'))
def check_request_removed(client, context, teacher):
    listing = client.get(
        "/api/maintenance/my-requests",
        params={"teacher_cpf": "11111111111"}
    )
    ids = [s["id"] for s in listing.json()]
    assert context["request"]["id"] not in ids

@then('o sistema não remove a solicitação')
def check_not_deleted(context):
    assert context["response"].status_code == 400

@then(parsers.parse('o sistema atualiza a descrição para "{description}"'))
def check_updated_description(context, description):
    assert context["response"].json()["description"] == description

@then('o sistema retorna confirmação de edição')
def check_edit_success(context):
    assert context["response"].status_code == 200

@then('o sistema não atualiza a solicitação')
def check_not_updated(context):
    assert context["response"].status_code == 400


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
