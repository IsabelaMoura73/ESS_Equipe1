"""
Testes BDD — Feature 5: Listagem de salas reservadas (usuario)
Aluna: Ana Sofia | Persona BDD: Ana Lima

Rodar:
    cd backend && pytest tests/test_list_reservation.py -v
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

# ── Banco em memoria (isolado, nao toca o salla.db real) ──────────────────────
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

# Carrega os cenarios do arquivo .feature
scenarios("features/list_reserved_rooms.feature")

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def create_tables():
    """Cria as tabelas no banco em memoria uma unica vez por sessao de teste."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(autouse=True)
def clean_database():
    """Limpa e repopula o banco antes de cada teste — garante isolamento."""
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

    # Cria salas de teste (necessario para validacao de sala existente)
    for nome in ["D005", "E101"]:
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
    """Garante que o override do banco esta ativo antes de cada teste."""
    app.dependency_overrides[get_db] = override_get_db
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def context():
    return {}


# ── Utilitarios ───────────────────────────────────────────────────────────────

def _parse_dt(dt_str: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de data invalido: {dt_str}")


def _normalize(text: str) -> str:
    """Remove acentos para comparacao entre feature file e resposta da API."""
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()


def _insert_reservation(user_cpf, user_name, room, start, end, status):
    """Insere uma reserva diretamente no banco de teste."""
    db = SessionTest()
    r = Reservation(
        user_cpf=user_cpf,
        user_name=user_name,
        room=room,
        start_time=_parse_dt(start),
        end_time=_parse_dt(end),
        status=status,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    rid = r.id
    db.close()
    return rid


STATUS_MAP = {
    "pending":   ReservationStatus.pending,
    "confirmed": ReservationStatus.confirmed,
    "denied":    ReservationStatus.denied,
    "completed": ReservationStatus.completed,
}

# ── Steps: GIVEN ──────────────────────────────────────────────────────────────

@given(parsers.parse('Ana Lima esta autenticada no sistema com CPF "{cpf}"'))
def ana_autenticada(context, cpf):
    context["user_cpf"] = cpf
    context["user_name"] = "Ana Lima"


@given(parsers.parse('Ana possui uma reserva com status "{st}" da sala "{room}" das "{start}" as "{end}"'))
def ana_possui_reserva(context, st, room, start, end):
    rid = _insert_reservation(
        context.get("user_cpf", "11122233344"),
        context.get("user_name", "Ana Lima"),
        room, start, end, STATUS_MAP[st],
    )
    context["reservation_id"] = rid


@given(parsers.parse('Ana possui reservas com status "{s1}" e "{s2}"'))
def ana_possui_multiplas(context, s1, s2):
    cpf = context.get("user_cpf", "11122233344")
    name = context.get("user_name", "Ana Lima")
    for i, st in enumerate([s1, s2]):
        _insert_reservation(
            cpf, name, f"SALA{i+1}",
            f"2026-08-0{i+1}T08:00:00", f"2026-08-0{i+1}T10:00:00",
            STATUS_MAP[st],
        )


@given(parsers.parse('existe uma reserva de outro usuario com CPF "{other_cpf}" da sala "{room}" das "{start}" as "{end}"'))
def outro_usuario_reserva(context, other_cpf, room, start, end):
    rid = _insert_reservation(
        other_cpf, "Outro Usuario", room, start, end, ReservationStatus.pending
    )
    context["other_reservation_id"] = rid


# ── Steps: WHEN ───────────────────────────────────────────────────────────────

@when("Ana acessa a listagem de suas reservas")
def ana_lista(client, context):
    r = client.get(
        "/api/reservations/my-reservations",
        params={"user_cpf": context.get("user_cpf", "11122233344")},
    )
    context["response"] = r


@when(parsers.parse('Ana filtra suas reservas por status "{st}"'))
def ana_filtra(client, context, st):
    r = client.get(
        "/api/reservations/my-reservations",
        params={"user_cpf": context.get("user_cpf", "11122233344"), "status": st},
    )
    context["response"] = r


@when("Ana acessa os detalhes da sua reserva")
def ana_detalha(client, context):
    r = client.get(
        f"/api/reservations/{context['reservation_id']}",
        params={"user_cpf": context.get("user_cpf", "11122233344")},
    )
    context["response"] = r


@when("Ana tenta acessar os detalhes da reserva do outro usuario")
def ana_tenta_acessar_outra(client, context):
    r = client.get(
        f"/api/reservations/{context['other_reservation_id']}",
        params={"user_cpf": context.get("user_cpf", "11122233344")},
    )
    context["response"] = r


@when("uma usuario nao autenticada tenta listar reservas sem informar o CPF")
def sem_cpf_lista(client, context):
    r = client.get("/api/reservations/my-reservations")
    context["response"] = r


# ── Steps: THEN ───────────────────────────────────────────────────────────────

@then("a listagem retorna todas as reservas de Ana independente do status")
def listagem_completa(context):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert len(r.json()) >= 2


@then(parsers.parse('a listagem retorna apenas reservas com status "{expected_status}"'))
def listagem_filtrada(context, expected_status):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    reservas = r.json()
    assert len(reservas) > 0, "A listagem nao deveria estar vazia"
    assert all(res["status"] == expected_status for res in reservas), \
        f"Esperava apenas '{expected_status}', mas recebi: {[res['status'] for res in reservas]}"


@then("a listagem esta ordenada da mais recente para a mais antiga")
def listagem_ordenada(context):
    r = context["response"]
    assert r.status_code == 200
    reservas = r.json()
    assert len(reservas) >= 2, "Precisamos de ao menos 2 reservas para verificar ordenacao"
    datas = [res["start_time"] for res in reservas]
    assert datas == sorted(datas, reverse=True), \
        f"Listagem nao esta ordenada do mais recente ao mais antigo: {datas}"


@then(parsers.parse('os detalhes exibem sala "{room}" e status "{st}"'))
def detalhes_corretos(context, room, st):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    body = r.json()
    assert body["room"] == room, f"Sala esperada: {room}, recebida: {body['room']}"
    assert body["status"] == st, f"Status esperado: {st}, recebido: {body['status']}"
    assert "start_time" in body and "end_time" in body


@then(parsers.parse('Ana recebe o erro "{msg}"'))
def ana_recebe_erro(context, msg):
    r = context["response"]
    assert r.status_code in (400, 403, 404, 422), \
        f"Esperava erro 4xx, recebeu {r.status_code}"
    detail = r.json().get("detail", "")
    assert _normalize(msg) in _normalize(detail), \
        f"Esperava '{msg}' na mensagem, mas recebi: '{detail}'"


@then("a listagem retorna uma lista vazia")
def listagem_vazia(context):
    r = context["response"]
    assert r.status_code == 200
    assert r.json() == [], f"Esperava lista vazia, recebeu: {r.json()}"


@then("o sistema retorna erro de validacao com codigo 422")
def retorna_422(context):
    assert context["response"].status_code == 422