"""
Testes BDD — Feature: Verificacao de Reservas (Administrador)

Rodar:
    cd backend && pytest tests/test_admin_reservation_verification.py -v
"""

import unicodedata
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
import models.reservation
from models.reservation import Reservation, ReservationStatus
import models.room
from models.room import Room, RoomMaintenanceStatus
from main import app

# ── Banco em memoria ──────────────────────────────────────────────────────────
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

scenarios("features/admin_reservation_verification.feature")

# ── Fixtures ──────────────────────────────────────────────────────────────────

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

    for nome in ["Lab 1", "Lab 2", "Auditorio", "Grad 3", "Grad 4"]:
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


# ── Utilitarios ───────────────────────────────────────────────────────────────

STATUS_MAP = {
    "pending": ReservationStatus.pending,
    "confirmed": ReservationStatus.confirmed,
    "denied": ReservationStatus.denied,
    "completed": ReservationStatus.completed,
}

ROLE_MAP = {
    "Aluno": "discente",
    "Professor": "docente",
    "discente": "discente",
    "docente": "docente",
}


def _parse_dt(dt_str: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato invalido: {dt_str}")


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()


def _insert(reservation_id, user_cpf, user_name, user_type, room, start, end, st):
    db = SessionTest()
    r = Reservation(
        id=reservation_id,
        user_cpf=user_cpf,
        user_name=user_name,
        user_type=user_type,
        room=room,
        start_time=_parse_dt(start),
        end_time=_parse_dt(end),
        status=st,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    rid = r.id
    db.close()
    return rid


# ── Steps: GIVEN ──────────────────────────────────────────────────────────────

@given("o administrador autenticado acessa a pagina de Visualizacao de Reservas")
def admin_autenticado(context):
    context["admin"] = True


@given(parsers.parse(
    'o sistema possui a reserva "{rid:d}" associada ao papel "{role}" '
    'para a sala "{room}" das "{start}" as "{end}"'
))
def insere_por_papel(rid, role, room, start, end):
    _insert(rid, f"cpf-{rid}", f"Usuario {rid}", ROLE_MAP[role], room, start, end, ReservationStatus.pending)


@given(parsers.parse('existe a reserva "{rid:d}" para a sala "{room}" com status "{st}"'))
def insere_reserva_status(rid, room, st):
    _insert(
        rid, f"cpf-{rid}", f"Usuario {rid}", "discente",
        room, "2026-07-10T08:00:00", "2026-07-10T10:00:00",
        STATUS_MAP[st],
    )


@given(parsers.parse(
    'existe a reserva "{rid:d}" criada por "{nome}" para a sala "{room}" com status "{st}"'
))
def insere_reserva_de_outrem(rid, nome, room, st):
    user_type = "docente" if "professor" in nome.lower() else "discente"
    _insert(
        rid, f"cpf-{rid}", nome, user_type, room,
        "2026-07-11T08:00:00", "2026-07-11T10:00:00",
        STATUS_MAP[st],
    )


# ── Steps: WHEN ───────────────────────────────────────────────────────────────

@when("o sistema carrega a listagem de reservas cadastradas")
def carrega_listagem(client, context):
    context["response"] = client.get("/api/admin/reservations")


@when(parsers.parse('o administrador clica no botao Confirmar para a reserva "{rid:d}"'))
def clica_confirmar(client, context, rid):
    context["response"] = client.patch(f"/api/admin/reservations/{rid}/confirm")
    context["reservation_id"] = rid


@when(parsers.parse('o administrador clica no botao Negar para a reserva "{rid:d}"'))
def clica_negar(client, context, rid):
    context["response"] = client.patch(f"/api/admin/reservations/{rid}/deny")
    context["reservation_id"] = rid


@when(parsers.parse('o administrador visualiza os detalhes da reserva "{rid:d}"'))
def visualiza_detalhes(client, context, rid):
    context["response"] = client.get(f"/api/admin/reservations/{rid}")
    context["reservation_id"] = rid


@when(parsers.parse('o administrador acessa os detalhes da reserva "{rid:d}"'))
def acessa_detalhes(client, context, rid):
    visualiza_detalhes(client, context, rid)


# ── Steps: THEN ───────────────────────────────────────────────────────────────

@then("a reserva do professor e exibida antes da reserva do aluno na lista")
def professor_antes_aluno(context):
    r = context["response"]
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) >= 2
    teacher_idx = next(i for i, x in enumerate(data) if x["user_type"] == "docente")
    student_idx = next(i for i, x in enumerate(data) if x["user_type"] == "discente")
    assert teacher_idx < student_idx, f"Professor deve vir antes do aluno: {data}"


@then(parsers.parse('o status de ambas permanece "{expected}"'))
def status_inalterado(context, expected):
    r = context["response"]
    for res in r.json():
        assert res["status"] == expected


@then(parsers.parse('o sistema atualiza o status da reserva "{rid:d}" para "{expected}" no banco de dados'))
def status_atualizado_no_banco(rid, expected):
    db = SessionTest()
    res = db.query(Reservation).filter(Reservation.id == rid).first()
    db.close()
    assert res is not None, f"Reserva {rid} nao encontrada"
    assert res.status.value == expected, f"Esperava {expected}, obteve {res.status.value}"


@then(parsers.parse('o sistema retorna a mensagem de sucesso "{msg}"'))
def mensagem_sucesso(context, msg):
    r = context["response"]
    assert r.status_code == 200, r.text
    body = r.json()
    assert _normalize(msg) in _normalize(body.get("message", "")), \
        f"Esperava '{msg}' em '{body}'"


@then("o sistema exibe os botoes Confirmar e Negar com o estado desabilitado")
def botoes_desabilitados(context):
    r = context["response"]
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["can_confirm"] is False
    assert body["can_deny"] is False


@then(parsers.parse('o sistema nao permite alterar o status da reserva "{rid:d}"'))
def nao_permite_alterar(client, context, rid):
    # Tenta confirmar uma reserva ja decidida → deve retornar erro
    resp = client.patch(f"/api/admin/reservations/{rid}/confirm")
    assert resp.status_code == 400, f"Esperava 400, recebeu {resp.status_code}: {resp.text}"
    detail = resp.json().get("detail", "")
    assert _normalize("ja decidida") in _normalize(detail) or _normalize("decidida") in _normalize(detail)


@then("o campo nome da sala consta como somente leitura")
def sala_somente_leitura(context):
    r = context["response"]
    assert r.status_code == 200, r.text
    body = r.json()
    assert "room" in body["read_only_fields"], \
        f"'room' deveria estar em read_only_fields: {body['read_only_fields']}"


@then("o administrador possui apenas as acoes Confirmar e Negar habilitadas")
def apenas_confirmar_negar(context):
    r = context["response"]
    body = r.json()
    # Reserva pendente: ambas acoes habilitadas, demais campos somente leitura
    assert body["can_confirm"] is True
    assert body["can_deny"] is True
    for campo in ("room", "start_time", "end_time"):
        assert campo in body["read_only_fields"]
