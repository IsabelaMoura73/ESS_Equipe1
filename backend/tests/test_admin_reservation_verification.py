"""
Testes BDD — Feature: Verificação de Reservas pelo Administrador
Aluno: Erick Melo | Persona BDD: Erick Teste

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

@given("Erick Teste esta autenticado como administrador")
def erick_autenticado(context):
    context["admin_cpf"] = "00000000000"
    context["admin_name"] = "Erick Teste"


@given(parsers.parse(
    'existe a reserva "{rid:d}" associada ao papel "{role}" '
    'para a sala "{room}" das "{start}" as "{end}"'
))
def insere_por_papel(rid, role, room, start, end):
    _insert(rid, f"cpf-{rid}", f"Usuario {rid}", role, room, start, end, ReservationStatus.pending)


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

@when("Erick consulta a listagem de reservas")
def lista_reservas(client, context):
    context["response"] = client.get("/api/admin/reservations")


@when(parsers.parse('Erick solicita a confirmacao da reserva "{rid:d}"'))
def solicita_confirmacao(client, context, rid):
    context["response"] = client.patch(f"/api/admin/reservations/{rid}/confirm")
    context["reservation_id"] = rid


@when(parsers.parse('Erick solicita a negacao da reserva "{rid:d}" sem informar justificativa'))
def solicita_negacao(client, context, rid):
    # Sem body → nenhum campo de justificativa enviado/exigido.
    context["response"] = client.patch(f"/api/admin/reservations/{rid}/deny")
    context["reservation_id"] = rid


@when(parsers.parse('Erick consulta o detalhe da reserva "{rid:d}"'))
def consulta_detalhe(client, context, rid):
    context["response"] = client.get(f"/api/admin/reservations/{rid}")
    context["reservation_id"] = rid


# ── Steps: THEN ───────────────────────────────────────────────────────────────

@then(parsers.parse('a reserva "{rid_first:d}" aparece antes da reserva "{rid_second:d}"'))
def ordem_listagem(context, rid_first, rid_second):
    r = context["response"]
    assert r.status_code == 200, r.text
    ids = [item["id"] for item in r.json()]
    assert rid_first in ids and rid_second in ids
    assert ids.index(rid_first) < ids.index(rid_second), \
        f"Esperava {rid_first} antes de {rid_second}, ordem retornada: {ids}"


@then(parsers.parse('o status de ambas permanece "{expected}"'))
def status_inalterado(context, expected):
    r = context["response"]
    for res in r.json():
        assert res["status"] == expected


@then(parsers.parse('o status da reserva "{rid:d}" passa a ser "{expected}"'))
def status_apos_acao(rid, expected):
    db = SessionTest()
    res = db.query(Reservation).filter(Reservation.id == rid).first()
    db.close()
    assert res is not None
    assert res.status.value == expected, \
        f"Esperava status '{expected}', mas a reserva esta '{res.status.value}'"


@then(parsers.parse('o status da reserva "{rid:d}" permanece "{expected}"'))
def status_permanece(rid, expected):
    status_apos_acao(rid, expected)


@then(parsers.parse('o servico retorna a mensagem "{msg}"'))
def mensagem_servico(context, msg):
    r = context["response"]
    assert r.status_code == 200, r.text
    body = r.json()
    assert _normalize(msg) in _normalize(body.get("message", "")), \
        f"Esperava '{msg}' em '{body}'"


@then(parsers.parse('o servico rejeita a operacao com a mensagem "{msg}"'))
def operacao_rejeitada(context, msg):
    r = context["response"]
    assert r.status_code in (400, 403, 404, 409, 422), \
        f"Esperava erro 4xx, recebeu {r.status_code}: {r.text}"
    detail = r.json().get("detail", "")
    assert _normalize(msg) in _normalize(detail), \
        f"Esperava '{msg}' em '{detail}'"


@then(parsers.parse('o servico informa as acoes permitidas como "{actions_csv}"'))
def acoes_permitidas(context, actions_csv):
    r = context["response"]
    assert r.status_code == 200, r.text
    expected = [a.strip() for a in actions_csv.split(",") if a.strip()]
    assert r.json().get("allowed_actions") == expected, \
        f"Esperava allowed_actions={expected}, recebi {r.json().get('allowed_actions')}"


@then(parsers.parse('o servico nao expoe operacao para alterar os dados da reserva "{rid:d}"'))
def sem_endpoint_de_edicao(client, rid):
    # Verifica que nao ha rota de admin para edicao/exclusao dos dados.
    # Qualquer endpoint mutativo (PUT, PATCH dos campos, DELETE) deve retornar 404/405.
    for method, path in [
        ("PUT", f"/api/admin/reservations/{rid}"),
        ("PATCH", f"/api/admin/reservations/{rid}"),
        ("DELETE", f"/api/admin/reservations/{rid}"),
    ]:
        resp = client.request(method, path, json={"room": "Outra Sala"})
        assert resp.status_code in (404, 405), \
            f"{method} {path} deveria nao existir, mas retornou {resp.status_code}"
