"""
Testes BDD — Feature 5: Listagem de salas reservadas (usuario)
Ana Sofia 

p rodar:
    cd backend && python -m pytest tests/test_list_reservation.py -v
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
scenarios("features/list_reserved_rooms.feature")


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
    for nome in ["D005", "E101", "SALA1", "SALA2"]:
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
def ctx():
    """Contexto isolado por teste — compartilhado entre todos os steps do mesmo cenario."""
    return {
        "user_cpf": None,
        "reservation_ids": [],
        "other_reservation_id": None,
        "response": None,
    }


# ── Utilitarios ───────────────────────────────────────────────────────────────

def _parse_dt(dt_str):
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato invalido: {dt_str}")


def _normalize(text):
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()


def _insert_reservation(user_cpf, user_name, room, start, end, status):
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

@given(parsers.parse('o sistema possui reservas do CPF "{cpf}" com status "{s1}" e "{s2}"'))
def sistema_possui_multiplas(ctx, cpf, s1, s2):
    ctx["user_cpf"] = cpf
    for i, st in enumerate([s1, s2]):
        rid = _insert_reservation(
            cpf, "Usuario Teste", f"SALA{i+1}",
            f"2026-08-0{i+1}T08:00:00", f"2026-08-0{i+1}T10:00:00",
            STATUS_MAP[st],
        )
        ctx["reservation_ids"].append(rid)


@given(parsers.parse('o sistema possui uma reserva do CPF "{cpf}" com status "{st}" da sala "{room}" das "{start}" as "{end}"'))
def sistema_possui_uma(ctx, cpf, st, room, start, end):
    if ctx["user_cpf"] is None:
        ctx["user_cpf"] = cpf
    rid = _insert_reservation(cpf, "Usuario Teste", room, start, end, STATUS_MAP[st])
    ctx["reservation_ids"].append(rid)


# Padrao distinto para evitar ambiguidade com parsers.parse 
@given(parsers.parse('o sistema possui uma reserva de outro usuario com CPF "{cpf}" da sala "{room}" das "{start}" as "{end}"'))
def sistema_possui_reserva_outro(ctx, cpf, room, start, end):
    rid = _insert_reservation(cpf, "Outro Usuario", room, start, end, ReservationStatus.pending)
    ctx["other_reservation_id"] = rid


@given(parsers.parse('o sistema nao possui reservas para o CPF "{cpf}"'))
def sistema_sem_reservas(ctx, cpf):
    ctx["user_cpf"] = cpf


# ── Steps: WHEN ───────────────────────────────────────────────────────────────

@when(parsers.parse('o servico de listagem e consultado para o CPF "{cpf}" sem filtro de status'))
def servico_lista_sem_filtro(ctx, client, cpf):
    ctx["user_cpf"] = cpf
    ctx["response"] = client.get(
        "/api/reservations/my-reservations",
        params={"user_cpf": cpf},
    )


@when(parsers.parse('o servico de listagem e consultado para o CPF "{cpf}" com filtro de status "{st}"'))
def servico_lista_com_filtro(ctx, client, cpf, st):
    ctx["user_cpf"] = cpf
    ctx["response"] = client.get(
        "/api/reservations/my-reservations",
        params={"user_cpf": cpf, "status": st},
    )


@when(parsers.parse('o servico de detalhe e consultado para o CPF "{cpf}" e o id da reserva'))
def servico_detalha(ctx, client, cpf):
    ids = ctx["reservation_ids"]
    assert len(ids) > 0, f"Nenhum reservation_id foi definido no Given. ctx: {ctx}"
    ctx["response"] = client.get(
        f"/api/reservations/{ids[0]}",
        params={"user_cpf": cpf},
    )


@when(parsers.parse('o servico de detalhe e consultado para o CPF "{cpf}" e o id da reserva do outro usuario'))
def servico_detalha_outro(ctx, client, cpf):
    rid = ctx["other_reservation_id"]
    assert rid is not None, "other_reservation_id nao foi definido no Given"
    ctx["response"] = client.get(
        f"/api/reservations/{rid}",
        params={"user_cpf": cpf},
    )


@when("o servico de listagem e consultado sem informar o CPF do usuario")
def servico_sem_cpf(ctx, client):
    ctx["response"] = client.get("/api/reservations/my-reservations")


# ── Steps: THEN ───────────────────────────────────────────────────────────────

@then(parsers.parse('o sistema retorna todas as reservas associadas ao CPF "{cpf}"'))
def retorna_todas(ctx, cpf):
    r = ctx["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert len(r.json()) >= 2, f"Esperava ao menos 2 reservas, recebeu: {r.json()}"


@then(parsers.parse('o sistema retorna somente reservas com status "{st}" para o CPF "{cpf}"'))
def retorna_filtradas(ctx, st, cpf):
    r = ctx["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    reservas = r.json()
    assert len(reservas) > 0, f"Nenhuma reserva retornada. ctx: {ctx}"
    assert all(res["status"] == st for res in reservas), \
        f"Status inesperado: {[res['status'] for res in reservas]}"


@then("o sistema retorna as reservas ordenadas da mais recente para a mais antiga")
def retorna_ordenadas(ctx):
    r = ctx["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    reservas = r.json()
    assert len(reservas) >= 2, f"Esperava ao menos 2 reservas, recebeu: {reservas}"
    datas = [res["start_time"] for res in reservas]
    assert datas == sorted(datas, reverse=True), f"Ordem incorreta: {datas}"


@then(parsers.parse('o sistema retorna os dados da reserva com sala "{room}" e status "{st}"'))
def retorna_detalhes(ctx, room, st):
    r = ctx["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    body = r.json()
    assert body["room"] == room, f"Sala: esperava {room}, recebeu {body['room']}"
    assert body["status"] == st, f"Status: esperava {st}, recebeu {body['status']}"


@then(parsers.parse('o sistema rejeita o acesso com erro "{msg}"'))
def rejeita_acesso(ctx, msg):
    r = ctx["response"]
    assert r.status_code in (403, 404), f"Esperava 403 ou 404, recebeu {r.status_code}"
    detail = r.json().get("detail", "")
    assert _normalize(msg) in _normalize(detail), \
        f"Esperava '{msg}' na mensagem, recebeu: '{detail}'"


@then("o sistema retorna uma colecao vazia de reservas")
def retorna_vazio(ctx):
    r = ctx["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert r.json() == [], f"Esperava lista vazia, recebeu: {r.json()}"


@then("o sistema rejeita a requisicao por ausencia de parametro obrigatorio")
def rejeita_sem_cpf(ctx):
    assert ctx["response"].status_code == 422