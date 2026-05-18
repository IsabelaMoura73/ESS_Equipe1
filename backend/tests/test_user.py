import unicodedata

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from database import SessionLocal
import models.user  # noqa: F401
import models.reservation  # noqa: F401
from models.user import User, UserRole
from models.reservation import Reservation, ReservationStatus
from main import app
from passlib.context import CryptContext

scenarios("features/user.feature")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_and_clean():
    db = SessionLocal()
    db.query(Reservation).delete()
    db.query(User).delete()
    db.commit()
    db.close()
    yield
    db = SessionLocal()
    db.query(Reservation).delete()
    db.query(User).delete()
    db.commit()
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def context():
    return {}


# Utilitarios 

def _normalize(text: str) -> str:
    """Remove acentos para comparacao entre feature file (ASCII) e API (UTF-8)."""
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()


def _insert_user(nome, cpf, tipo, senha, status=True, siape=None, matricula=None, curso=None):
    db = SessionLocal()
    user = User(
        nome=nome,
        cpf=cpf,
        tipo=UserRole(tipo),
        senha=pwd_context.hash(senha),
        status=status,
        siape=siape,
        matricula=matricula,
        curso=curso,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    uid = user.id
    db.close()
    return uid


def _get_user_by_cpf(cpf):
    db = SessionLocal()
    user = db.query(User).filter(User.cpf == cpf).first()
    db.close()
    return user


def _count_users_by_cpf(cpf):
    db = SessionLocal()
    count = db.query(User).filter(User.cpf == cpf).count()
    db.close()
    return count


def _insert_reservation_for_user(cpf, status_str):
    db = SessionLocal()
    r = Reservation(
        user_cpf=cpf,
        user_name="John Logan",
        room="SALA_TESTE",
        start_time=__import__("datetime").datetime(2026, 8, 1, 8, 0),
        end_time=__import__("datetime").datetime(2026, 8, 1, 10, 0),
        status=ReservationStatus(status_str),
    )
    db.add(r)
    db.commit()
    db.close()


#GIVEN 

@given(parsers.parse('o sistema nao tem um usuario com CPF "{cpf}"'))
def sistema_sem_usuario(cpf):
    db = SessionLocal()
    user = db.query(User).filter(User.cpf == cpf).first()
    db.close()
    assert user is None, f"Esperava ausencia de usuario com CPF {cpf}, mas ele existe"


@given(parsers.parse('o sistema tem um usuario "{nome}" com CPF "{cpf}"'))
def sistema_tem_usuario(nome, cpf):
    _insert_user(nome=nome, cpf=cpf, tipo="discente", senha="senha123",
                 matricula="20230001", curso="Computacao")


@given(parsers.parse('o sistema tem um usuario ativo "{nome}" com CPF "{cpf}" e senha "{senha}"'))
def sistema_tem_usuario_ativo(context, nome, cpf, senha):
    uid = _insert_user(nome=nome, cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=True)
    context["user_id"] = uid
    context["user_cpf"] = cpf
    context["user_nome"] = nome


@given(parsers.parse('o sistema tem um usuario desativado "{nome}" com CPF "{cpf}" e senha "{senha}"'))
def sistema_tem_usuario_desativado(context, nome, cpf, senha):
    uid = _insert_user(nome=nome, cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=False)
    context["user_id"] = uid
    context["user_cpf"] = cpf
    context["user_nome"] = nome


@given(parsers.parse('o sistema tem uma reserva com status "{status}" associada ao usuario com CPF "{cpf}"'))
def sistema_tem_reserva_para_usuario(cpf, status):
    _insert_reservation_for_user(cpf, status)


#WHEN 

@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'matricula "{matricula}", curso "{curso}" e senha "{senha}"'
))
def cadastrar_discente(client, context, nome, cpf, tipo, matricula, curso, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "matricula": matricula, "curso": curso, "senha": senha,
    })
    context["response"] = r


@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'siape "{siape}" e senha "{senha}"'
))
def cadastrar_docente(client, context, nome, cpf, tipo, siape, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "siape": siape, "senha": senha,
    })
    context["response"] = r


@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'sem siape e senha "{senha}"'
))
def cadastrar_docente_sem_siape(client, context, nome, cpf, tipo, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo, "senha": senha,
    })
    context["response"] = r


@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'curso "{curso}", sem matricula e senha "{senha}"'
))
def cadastrar_discente_sem_matricula(client, context, nome, cpf, tipo, curso, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "curso": curso, "senha": senha,
    })
    context["response"] = r


@when(parsers.parse('eu realizo o login com CPF "{cpf}" e senha "{senha}"'))
def realizar_login(client, context, cpf, senha):
    r = client.post("/users/login", json={"cpf": cpf, "senha": senha})
    context["response"] = r


@when(parsers.parse('eu atualizo o nome do usuario com CPF "{cpf}" para "{novo_nome}"'))
def atualizar_nome(client, context, cpf, novo_nome):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}", json={"nome": novo_nome})
    context["response"] = r


@when(parsers.parse('eu atualizo a senha do usuario com CPF "{cpf}" para "{nova_senha}"'))
@when(parsers.parse('eu tento atualizar a senha do usuario com CPF "{cpf}" para "{nova_senha}"'))
def atualizar_senha(client, context, cpf, nova_senha):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}", json={"senha": nova_senha})
    context["response"] = r
    if r.status_code == 200:
        context["nova_senha"] = nova_senha


@when(parsers.parse('eu solicito a desativacao da conta do usuario com CPF "{cpf}"'))
def desativar_conta(client, context, cpf):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}/deactivate")
    context["response"] = r


#THEN 

@then(parsers.parse('o sistema armazena o usuario "{nome}" com CPF "{cpf}" e tipo "{tipo}"'))
def sistema_armazena_usuario(nome, cpf, tipo):
    user = _get_user_by_cpf(cpf)
    assert user is not None, f"Usuario com CPF {cpf} nao encontrado no banco"
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"
    assert user.tipo.value == tipo, \
        f"Tipo esperado '{tipo}', encontrado '{user.tipo.value}'"


@then(parsers.parse('o status do usuario "{nome}" com CPF "{cpf}" e ativo'))
def status_usuario_ativo(nome, cpf):
    user = _get_user_by_cpf(cpf)
    assert user is not None, f"Usuario com CPF {cpf} nao encontrado"
    assert user.status is True, f"Esperava usuario ativo, mas status={user.status}"


@then(parsers.parse('o servidor retorna um erro informando que o CPF ja esta cadastrado'))
def erro_cpf_ja_cadastrado(context):
    r = context["response"]
    assert r.status_code == 400, f"Esperava 400, recebeu {r.status_code}: {r.text}"
    detail = _normalize(r.json().get("detail", ""))
    assert "cpf" in detail or "cadastrado" in detail, \
        f"Mensagem de erro inesperada: {r.json().get('detail')}"


@then(parsers.parse('o sistema ainda tem apenas um usuario com CPF "{cpf}"'))
def sistema_tem_apenas_um(cpf):
    assert _count_users_by_cpf(cpf) == 1, \
        f"Esperava exatamente 1 usuario com CPF {cpf}"


@then("o servidor retorna um erro de validacao")
def erro_validacao(context):
    r = context["response"]
    assert r.status_code == 422, \
        f"Esperava 422 (validacao), recebeu {r.status_code}: {r.text}"


@then(parsers.parse('o sistema nao tem um usuario com CPF "{cpf}"'))
def sistema_nao_tem_usuario(cpf):
    assert _count_users_by_cpf(cpf) == 0, \
        f"Esperava ausencia de usuario com CPF {cpf}, mas ele existe"


@then(parsers.parse('o servidor retorna os dados do usuario com CPF "{cpf}"'))
@then(parsers.parse('o servidor retorna os dados do usuario "{nome}" com CPF "{cpf}"'))
def retorna_dados_usuario(context, cpf, nome=None):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    assert r.json().get("cpf") == cpf
    if nome:
        assert _normalize(r.json().get("nome", "")) == _normalize(nome)


@then("o servidor retorna um erro informando CPF ou senha invalidos")
def erro_cpf_ou_senha_invalidos(context):
    r = context["response"]
    assert r.status_code == 401, f"Esperava 401, recebeu {r.status_code}: {r.text}"
    detail = _normalize(r.json().get("detail", ""))
    assert "cpf" in detail or "senha" in detail or "invalido" in detail, \
        f"Mensagem inesperada: {r.json().get('detail')}"


@then("o servidor retorna um erro informando que a conta esta desativada")
def erro_conta_desativada_login(context):
    r = context["response"]
    assert r.status_code == 403, f"Esperava 403, recebeu {r.status_code}: {r.text}"
    detail = _normalize(r.json().get("detail", ""))
    assert "desativada" in detail or "desativ" in detail, \
        f"Mensagem inesperada: {r.json().get('detail')}"



@then(parsers.parse(
    'o sistema ainda tem o usuario "{nome}" com CPF "{cpf}" com status desativado'
))
def usuario_ainda_desativado(nome, cpf):
    user = _get_user_by_cpf(cpf)
    assert user is not None
    assert user.status is False, f"Esperava usuario desativado, mas status={user.status}"


@then(parsers.parse('o servidor retorna os dados atualizados com nome "{novo_nome}"'))
def retorna_dados_com_novo_nome(context, novo_nome):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    body = r.json()
    assert _normalize(body.get("nome", "")) == _normalize(novo_nome), \
        f"Nome esperado '{novo_nome}', recebido '{body.get('nome')}'"


@then(parsers.parse('o sistema armazena o usuario com CPF "{cpf}" com nome "{nome}"'))
def sistema_armazena_nome(cpf, nome):
    user = _get_user_by_cpf(cpf)
    assert user is not None
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"


@then(parsers.parse('o sistema permite login com CPF "{cpf}" e nova senha "{nova_senha}"'))
def sistema_permite_login_nova_senha(client, cpf, nova_senha):
    r = client.post("/users/login", json={"cpf": cpf, "senha": nova_senha})
    assert r.status_code == 200, \
        f"Login com nova senha falhou: {r.status_code} — {r.text}"


@then(parsers.parse('o sistema ainda permite login com CPF "{cpf}" e senha original "{senha_original}"'))
def sistema_permite_login_senha_original(client, cpf, senha_original):
    r = client.post("/users/login", json={"cpf": cpf, "senha": senha_original})
    assert r.status_code == 200, \
        f"Login com senha original falhou: {r.status_code} — {r.text}"


@then(parsers.parse(
    'o servidor retorna os dados do usuario com CPF "{cpf}" com status desativado'
))
def retorna_usuario_desativado(context, cpf):
    r = context["response"]
    assert r.status_code == 200, f"Esperava 200, recebeu {r.status_code}: {r.text}"
    body = r.json()
    assert body.get("cpf") == cpf
    assert body.get("status") is False, \
        f"Esperava status=False, recebeu status={body.get('status')}"


@then(parsers.parse(
    'o sistema armazena o usuario com CPF "{cpf}" com status desativado'
))
def sistema_armazena_status_desativado(cpf):
    user = _get_user_by_cpf(cpf)
    assert user is not None
    assert user.status is False, f"Esperava status desativado, mas status={user.status}"


@then(parsers.parse(
    'o sistema armazena todas as reservas do usuario com CPF "{cpf}" com status "{status}"'
))
def reservas_com_status(cpf, status):
    db = SessionLocal()
    reservas = db.query(Reservation).filter(Reservation.user_cpf == cpf).all()
    db.close()
    for reserva in reservas:
        assert reserva.status.value == status, \
            f"Reserva {reserva.id} com status '{reserva.status.value}', esperava '{status}'"


@then("o servidor retorna um erro informando que a conta ja esta desativada")
def erro_conta_ja_desativada(context):
    r = context["response"]
    assert r.status_code == 400, f"Esperava 400, recebeu {r.status_code}: {r.text}"
    detail = _normalize(r.json().get("detail", ""))
    assert "desativada" in detail or "desativ" in detail, \
        f"Mensagem inesperada: {r.json().get('detail')}"