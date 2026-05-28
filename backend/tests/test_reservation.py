"""
Testes BDD — Feature 7: Efetuar reserva e manutencao de reservas (usuario)
Aluno: Artur Vinicius Pereira Fernandes

Rodar:
    cd backend && pytest tests/test_reservation.py -v
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
import models.room
import models.user
from models.reservation import Reservation, ReservationStatus
from models.room import Room, RoomMaintenanceStatus
from models.user import User, UserRole
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

scenarios("features/reservation_management.feature")

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
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()


_TIPO_MAP = {
    "discente": UserRole.DISCENTE,
    "docente": UserRole.DOCENTE,
    "admin": UserRole.ADMIN,
}

_MAINTENANCE_MAP = {
    "Sim": RoomMaintenanceStatus.yes,
    "Não": RoomMaintenanceStatus.no,
    "Agendada": RoomMaintenanceStatus.scheduled,
}

STATUS_MAP = {
    "pending": ReservationStatus.pending,
    "confirmed": ReservationStatus.confirmed,
    "denied": ReservationStatus.denied,
    "completed": ReservationStatus.completed,
}


def _insert_user(cpf: str, tipo: str, ativo: bool = True) -> None:
    db = SessionTest()
    if db.query(User).filter(User.cpf == cpf).first() is None:
        db.add(User(
            nome=f"Usuario {cpf}",
            cpf=cpf,
            status=ativo,
            senha="senha_hash",
            tipo=_TIPO_MAP[tipo],
        ))
        db.commit()
    db.close()


def _insert_reservation(user_cpf, room, start, end, status):
    db = SessionTest()
    r = Reservation(
        user_cpf=user_cpf,
        user_name=f"Usuario {user_cpf}",
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


# ── Steps: GIVEN ──────────────────────────────────────────────────────────────

@given(parsers.parse('o sistema tem um usuario com CPF "{cpf}" e tipo "{tipo}"'))
def sistema_tem_usuario(cpf, tipo):
    _insert_user(cpf, tipo)


@given(parsers.parse('o sistema tem um usuario com CPF "{cpf}"'))
def sistema_tem_usuario_sem_tipo(cpf):
    _insert_user(cpf, "discente")


@given(parsers.parse('o sistema nao possui um usuario com CPF "{cpf}"'))
def sistema_nao_possui_usuario(**_):
    pass


@given(parsers.parse('a conta do usuario com CPF "{cpf}" esta desativada'))
def conta_desativada(cpf):
    db = SessionTest()
    user = db.query(User).filter(User.cpf == cpf).first()
    user.status = False
    db.commit()
    db.close()


@given(parsers.parse('o sistema nao tem nenhuma reserva confirmada da sala "{room}" das "{start}" as "{end}"'))
def sistema_sem_reserva_confirmada(room, start, end):
    pass


@given(parsers.parse('o sistema possui uma reserva confirmada da sala "{room}" das "{start}" as "{end}"'))
def sistema_possui_reserva_confirmada(room, start, end):
    _insert_reservation("00000000000", room, start, end, ReservationStatus.confirmed)


@given(parsers.parse('o sistema possui uma reserva pendente da sala "{room}" das "{start}" as "{end}" para o CPF "{cpf}"'))
def sistema_possui_reserva_pendente(context, room, start, end, cpf):
    rid = _insert_reservation(cpf, room, start, end, ReservationStatus.pending)
    context["reservation_id"] = rid


@given(parsers.parse('o sistema possui uma reserva pendente de ID {rid:d} da sala "{room}" das "{start}" as "{end}" para o CPF "{cpf}"'))
def sistema_possui_reserva_pendente_id(context, rid, room, start, end, cpf):
    real_id = _insert_reservation(cpf, room, start, end, ReservationStatus.pending)
    context["reservation_id"] = real_id
    context["feature_id"] = rid


@given(parsers.parse('o sistema possui uma reserva de ID {rid:d} com status "{st}" da sala "{room}" das "{start}" as "{end}" para o CPF "{cpf}"'))
def sistema_possui_reserva_id_status(context, rid, st, room, start, end, cpf):
    real_id = _insert_reservation(cpf, room, start, end, STATUS_MAP[st])
    context["reservation_id"] = real_id
    context["feature_id"] = rid


@given(parsers.parse('o sistema possui uma reserva com status "{st}" da sala "{room}" das "{start}" as "{end}" para o CPF "{cpf}"'))
def sistema_possui_reserva_status(context, st, room, start, end, cpf):
    rid = _insert_reservation(cpf, room, start, end, STATUS_MAP[st])
    context["reservation_id"] = rid


@given(parsers.parse('o sistema tem a sala "{room}" com status de manutencao "{manutencao}"'))
def sistema_sala_manutencao(room, manutencao):
    db = SessionTest()
    sala = db.query(Room).filter(Room.name == room).first()
    sala.maintenance_status = _MAINTENANCE_MAP[manutencao]
    db.commit()
    db.close()


# ── Steps: WHEN ──────────────────────────────────────────────────────────────

@when(parsers.parse('o usuario com CPF "{cpf}" tenta reservar a sala "{room}" das "{start}" as "{end}"'))
def usuario_tenta_reservar(client, context, cpf, room, start, end):
    r = client.post(
        "/api/reservations/",
        params={"user_cpf": cpf},
        json={"room": room, "start_time": start, "end_time": end},
    )
    context["response"] = r
    if r.status_code == 201:
        context["reservation_id"] = r.json()["id"]


@when(parsers.parse('o usuario com CPF "{cpf}" tenta editar a reserva de ID {_rid:d} alterando horario de fim para "{new_end}"'))
def usuario_tenta_editar_fim(client, context, cpf, new_end, **_):
    r = client.put(
        f"/api/reservations/{context['reservation_id']}",
        params={"user_cpf": cpf},
        json={"end_time": new_end},
    )
    context["response"] = r


@when(parsers.parse('o usuario com CPF "{cpf}" tenta editar a reserva de ID {_rid:d} alterando sala para "{new_room}"'))
def usuario_tenta_editar_sala(client, context, cpf, new_room, **_):
    r = client.put(
        f"/api/reservations/{context['reservation_id']}",
        params={"user_cpf": cpf},
        json={"room": new_room},
    )
    context["response"] = r


@when(parsers.parse('o usuario com CPF "{cpf}" tenta editar a reserva de ID {_rid:d} alterando sala para "{new_room}" e horario de fim para "{new_end}"'))
def usuario_tenta_editar_sala_e_fim(client, context, cpf, new_room, new_end, **_):
    r = client.put(
        f"/api/reservations/{context['reservation_id']}",
        params={"user_cpf": cpf},
        json={"room": new_room, "end_time": new_end},
    )
    context["response"] = r


@when(parsers.parse('o usuario com CPF "{cpf}" tenta cancelar a reserva de ID {_rid:d}'))
def usuario_tenta_cancelar_id(client, context, cpf, **_):
    r = client.delete(
        f"/api/reservations/{context['reservation_id']}",
        params={"user_cpf": cpf},
    )
    context["response"] = r


# ── Steps: THEN ──────────────────────────────────────────────────────────────

@then(parsers.parse('o sistema armazena a reserva com status "{expected_status}"'))
def sistema_armazena_reserva(context, expected_status):
    r = context["response"]
    assert r.status_code == 201, f"Esperava 201, recebeu {r.status_code}: {r.text}"
    assert r.json()["status"] == expected_status


@then(parsers.parse('o sistema armazena a reserva com status "{expected_status}" e tipo "{expected_tipo}"'))
def sistema_armazena_reserva_tipo(context, expected_status, expected_tipo):
    r = context["response"]
    assert r.status_code == 201, f"Esperava 201, recebeu {r.status_code}: {r.text}"
    assert r.json()["status"] == expected_status
    assert r.json()["user_type"] == expected_tipo


@then(parsers.parse('o sistema armazena a reserva com status "{expected_status}" e CPF "{expected_cpf}"'))
def sistema_armazena_reserva_cpf(context, expected_status, expected_cpf):
    r = context["response"]
    assert r.status_code == 201, f"Esperava 201, recebeu {r.status_code}: {r.text}"
    assert r.json()["status"] == expected_status
    assert r.json()["user_cpf"] == expected_cpf


@then(parsers.parse('o status do usuario na reserva e "{expected_tipo}"'))
def status_usuario_na_reserva(context, expected_tipo):
    assert context["response"].json()["user_type"] == expected_tipo


@then(parsers.parse('o servidor retorna um erro informando que a sala ja esta reservada neste periodo'))
def erro_sala_reservada(context):
    r = context["response"]
    assert r.status_code == 400
    assert "conflito" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o servidor retorna um erro informando que o usuario ja possui uma reserva neste horario'))
def erro_usuario_conflito(context):
    r = context["response"]
    assert r.status_code == 400
    assert "ja possui uma reserva" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o servidor retorna um erro informando que o usuario nao foi encontrado'))
def erro_usuario_nao_encontrado(context):
    r = context["response"]
    assert r.status_code == 404
    assert "nao encontrado" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o sistema nao possui nenhuma reserva com CPF "{cpf}"'))
def sistema_sem_reserva_cpf(cpf):
    db = SessionTest()
    count = db.query(Reservation).filter(Reservation.user_cpf == cpf).count()
    db.close()
    assert count == 0


@then(parsers.parse('o servidor retorna um erro informando que a conta esta desativada'))
def erro_conta_desativada(context):
    r = context["response"]
    assert r.status_code == 403
    assert "desativada" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o servidor retorna um erro informando que a sala nao foi encontrada'))
def erro_sala_nao_encontrada(context):
    r = context["response"]
    assert r.status_code == 404
    assert "sala nao encontrada" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o servidor retorna um erro informando que a sala esta em manutencao'))
def erro_sala_manutencao(context):
    r = context["response"]
    assert r.status_code == 400
    assert "manutencao" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o servidor retorna um erro informando que o usuario nao e dono da reserva'))
def erro_nao_dono(context):
    r = context["response"]
    assert r.status_code == 403
    assert "nao" in _normalize(r.json().get("detail", "")) and "dono" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o servidor retorna um erro informando que so e possivel editar reservas pendentes'))
def erro_so_pendentes(context):
    r = context["response"]
    assert r.status_code == 400
    assert "pendentes" in _normalize(r.json().get("detail", ""))


@then(parsers.parse('o sistema atualiza a sala da reserva para "{expected_room}"'))
def sistema_atualiza_sala(context, expected_room):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert r.json()["room"] == expected_room


@then(parsers.parse('o sistema atualiza a sala da reserva de ID {_rid:d} para "{expected_room}"'))
def sistema_atualiza_sala_id(context, expected_room, **_):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert r.json()["room"] == expected_room


@then(parsers.parse('o sistema atualiza o horario de fim da reserva para "{expected_end}"'))
def sistema_atualiza_fim(context, expected_end):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert expected_end[:16] in r.json()["end_time"]


@then(parsers.parse('o status da reserva permanece "{expected}"'))
def status_permanece(context, expected):
    assert context["response"].json()["status"] == expected


@then(parsers.parse('o sistema marca a reserva com status "{expected}"'))
def sistema_marca_status(context, expected):
    db = SessionTest()
    r = db.query(Reservation).filter(Reservation.id == context["reservation_id"]).first()
    db.close()
    assert r is not None
    assert r.status.value == expected
