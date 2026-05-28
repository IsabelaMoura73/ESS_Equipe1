"""
Testes BDD — Feature: Confirmação e Negação de Solicitações de Manutenção

Rodar:
    cd backend && pytest tests/test_maintenance_check.py -v
"""

from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
import models.maintenance
import models.reservation
import models.room  # noqa: F401
from models.maintenance import MaintenanceRequest, MaintenanceStatus
from models.maintenance_check import (
    MaintenanceCheckStatus,
    ReservationConflictType,
    MAINTENANCE_CHECK_MESSAGES,
)
from models.reservation import Reservation, ReservationStatus
from models.room import Room, RoomMaintenanceStatus
from main import app
from routes.maintenance_check import router as maintenance_check_router

scenarios("features/maintenance_check.feature")

# Registra o router de admin sem precisar alterar main.py durante o desenvolvimento
existing_prefixes = [r.path for r in app.routes]
if not any("/api/maintenance/admin" in p for p in existing_prefixes):
    app.include_router(maintenance_check_router)

# ── Banco em memória ──────────────────────────────────────────────────────────
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

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def create_tables():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

TEACHER_CPF = "111.111.111-11"
# Hash fixo apenas para satisfazer o campo NOT NULL em testes (não é usado para login)
_FAKE_HASH = "$2b$12$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

@pytest.fixture(autouse=True)
def clean_database():
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    # Cria usuário docente de teste necessário para a FK teacher_cpf
    from models.user import User, UserRole
    db.add(User(
        nome="Professor Teste",
        cpf=TEACHER_CPF,
        status=True,
        senha=_FAKE_HASH,
        tipo=UserRole.DOCENTE,
    ))
    db.commit()
    # Cria todas as salas utilizadas nos testes
    for nome in ["Sala D002", "Sala D003", "Sala D004", "Sala D005", "Grad 2"]:
        db.add(Room(
            name=nome,
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

# ── Helpers ───────────────────────────────────────────────────────────────────

def _insert_maintenance(room: str, status: MaintenanceStatus = MaintenanceStatus.pending) -> int:
    db = SessionTest()
    req = MaintenanceRequest(
        teacher_cpf=TEACHER_CPF,
        teacher_name="Professor Teste",
        room=room,
        description="Descrição de teste",
        status=status,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    rid = req.id
    db.close()
    return rid

def _insert_reservation(room: str, status: ReservationStatus, days_from_now: int = 5) -> int:
    db = SessionTest()
    start = datetime.now() + timedelta(days=days_from_now)
    end   = start + timedelta(hours=2)
    r = Reservation(
        user_cpf="000.000.000-00",
        user_name="Usuário Teste",
        room=room,
        start_time=start,
        end_time=end,
        status=status,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    rid = r.id
    db.close()
    return rid

def _parse_date_br(date_str: str) -> str:
    day, month, year = date_str.split("/")
    return f"{year}-{month}-{day}"

def _get_maintenance_status(request_id: int) -> MaintenanceCheckStatus:
    db = SessionTest()
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    status = req.status if req else None
    db.close()
    return status

def _get_reservation_status(reservation_id: int) -> ReservationStatus:
    db = SessionTest()
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    status = res.status if res else None
    db.close()
    return status

# ── GIVEN ─────────────────────────────────────────────────────────────────────

@given("eu estou logado como administrador")
def admin_logged_in(context):
    context["is_admin"] = True

@given(parsers.parse('a "{room}" não possui reservas com status "Confirmada" na data atual'))
def room_has_no_confirmed_reservations(context, room):
    context["room"] = room
    context["maintenance_id"] = _insert_maintenance(room)

@given(parsers.parse('existe uma solicitação de manutenção com status "Pendente" para a "{room}"'))
def existing_pending_maintenance(context, room):
    context["room"] = room
    context["maintenance_id"] = _insert_maintenance(room)

@given(parsers.parse('existe solicitação de manutenção com status "Pendente" para a "{room}"'))
def existing_pending_maintenance_short(context, room):
    context["room"] = room
    context["maintenance_id"] = _insert_maintenance(room)
    if room == "Sala D003":
        rid = _insert_reservation(room, ReservationStatus.confirmed, days_from_now=5)
        context["confirmed_reservation_id"] = rid

# ── WHEN ──────────────────────────────────────────────────────────────────────

@when("eu acesso a página de visualização de solicitações de manutenção")
def access_maintenance_list(client, context):
    context["response"] = client.get("/api/maintenance/admin/requests")

@when("eu consigo visualizar a solicitações")
def can_see_requests(context):
    assert context["response"].status_code == 200

@when("eu seleciono a opção de confirmar a solicitação")
def select_confirm_option(context):
    context["action"] = MaintenanceCheckStatus.confirmed

@when("eu seleciono a opção de negar a solicitação")
def select_deny_option(client, context):
    request_id = context["maintenance_id"]
    context["response"] = client.put(f"/api/maintenance/admin/{request_id}/deny")
    context["action"] = MaintenanceCheckStatus.denied

@when(parsers.parse('eu preencho o campo "Data de fim da manutenção" com "{end_date}"'))
def fill_end_date(context, end_date):
    context["end_date"] = _parse_date_br(end_date)

@when('eu clico em "Confirmar manutenção"')
def click_confirm(client, context):
    request_id = context["maintenance_id"]
    context["response"] = client.put(
        f"/api/maintenance/admin/{request_id}/confirm",
        json={"end_date": context["end_date"], "force": False},
    )

@when(parsers.parse('a "{room}" possui reservas com status "Pendente" dentro do período de manutenção'))
def room_has_pending_reservations_in_period(client, context, room):
    db = SessionTest()
    db.query(MaintenanceRequest).filter(MaintenanceRequest.id == context["maintenance_id"]).update(
        {"status": MaintenanceStatus.pending, "start_date": None, "end_date": None}
    )
    db.commit()
    db.close()

    rid = _insert_reservation(room, ReservationStatus.pending, days_from_now=5)
    context["pending_reservation_id"] = rid

    request_id = context["maintenance_id"]
    context["response"] = client.put(
        f"/api/maintenance/admin/{request_id}/confirm",
        json={"end_date": context["end_date"], "force": False},
    )

@when("eu confirmo a ação")
def confirm_action_with_force(client, context):
    request_id = context["maintenance_id"]
    context["response"] = client.put(
        f"/api/maintenance/admin/{request_id}/confirm",
        json={"end_date": context["end_date"], "force": True},
    )

# ── THEN ──────────────────────────────────────────────────────────────────────

@then('o status da solicitação é atualizado para "Confirmada"')
def status_updated_to_confirmed(context):
    assert context["response"].status_code == 200, (
        f"Esperado 200, obtido {context['response'].status_code}: {context['response'].json()}"
    )
    assert context["response"].json()["status"] == MaintenanceCheckStatus.confirmed

@then(parsers.parse('a "{room}" entra em manutenção com início na data atual e fim em "{end_date}"'))
def room_enters_maintenance(context, room, end_date):
    data = context["response"].json()
    assert data["start_date"] == str(date.today())
    assert data["end_date"]   == _parse_date_br(end_date)
    assert data["room"]       == room

@then('o status da solicitação é atualizado para "Negada"')
def status_updated_to_denied(context):
    assert context["response"].status_code == 200, (
        f"Esperado 200, obtido {context['response'].status_code}: {context['response'].json()}"
    )
    assert context["response"].json()["status"] == MaintenanceCheckStatus.denied

@then(parsers.parse('a "{room}" permanece disponível para reservas'))
def room_remains_available(context, room):
    data = context["response"].json()
    assert data["status"] == MaintenanceCheckStatus.denied
    assert data["room"]   == room

@then(parsers.parse('o sistema exibe a mensagem "{message}"'))
def system_shows_message(context, message):
    assert context["response"].status_code == 409, (
        f"Esperado 409, obtido {context['response'].status_code}: {context['response'].json()}"
    )
    detail   = context["response"].json().get("detail", {})
    expected = MAINTENANCE_CHECK_MESSAGES[ReservationConflictType.pending_conflict]
    if isinstance(detail, dict):
        assert expected in detail.get("message", "")
    else:
        assert message in detail

@then(parsers.parse('todas as reservas com status "Pendente" da "{room}" dentro do período de manutenção foram automaticamente alteradas para "Negada"'))
def pending_reservations_auto_denied(context, room):
    status = _get_reservation_status(context["pending_reservation_id"])
    assert status == ReservationStatus.denied, (
        f"Esperado 'denied', obtido '{status}'"
    )

@then("o sistema impede a confirmação da manutenção")
def system_blocks_confirmation(context):
    assert context["response"].status_code == 409, (
        f"Esperado 409, obtido {context['response'].status_code}: {context['response'].json()}"
    )

@then(parsers.parse('eu vejo a mensagem "{message}"'))
def i_see_message(context, message):
    detail   = context["response"].json().get("detail", "")
    expected = MAINTENANCE_CHECK_MESSAGES[ReservationConflictType.confirmed_conflict]
    if isinstance(detail, dict):
        assert expected in detail.get("message", "")
    else:
        assert message in detail

@then('o status da solicitação permanece "Pendente"')
def status_remains_pending(context):
    status = _get_maintenance_status(context["maintenance_id"])
    assert status == MaintenanceCheckStatus.pending, (
        f"Esperado 'pending', obtido '{status}'"
    )
