import unicodedata

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
import models.user  # noqa: F401
import models.reservation  # noqa: F401
from models.user import User, UserRole
from models.reservation import Reservation, ReservationStatus
from main import app
from passlib.context import CryptContext

scenarios("features/user.feature")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

@pytest.fixture(autouse=True)
def clean_database():
    db = SessionTest()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
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

# ── Utilitários ───────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()

def _insert_user(nome, cpf, tipo, senha, status=True, siape=None, matricula=None, curso=None):
    db = SessionTest()
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
    db = SessionTest()
    user = db.query(User).filter(User.cpf == cpf).first()
    db.close()
    return user

def _count_users_by_cpf(cpf):
    db = SessionTest()
    count = db.query(User).filter(User.cpf == cpf).count()
    db.close()
    return count

def _insert_reservation_for_user(cpf, status_str):
    db = SessionTest()
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

# helpers
def _assert_response_ok(context, expected_status):
    r = context["response"]
    assert r.status_code == expected_status, \
        f"Esperava {expected_status}, recebeu {r.status_code}: {r.text}"
    return r.json()

def _assert_user_in_db(cpf):
    user = _get_user_by_cpf(cpf)
    assert user is not None, f"Usuario com CPF {cpf} nao encontrado no banco"
    return user

def _assert_user_status_in_db(cpf, expected_status: bool):
    user = _assert_user_in_db(cpf)
    label = "ativo" if expected_status else "desativado"
    assert user.status is expected_status, \
        f"Esperava usuario {label} no banco para CPF {cpf}, encontrado '{user.status}'"

# ── Steps: GIVEN ─────────────────────────────────────────────────────────────

@given(parsers.parse('o sistema nao tem um usuario com CPF "{cpf}"'))
def sistema_sem_usuario(cpf):
    assert _count_users_by_cpf(cpf) == 0, \
        f"Esperava ausencia de usuario com CPF {cpf}, mas ele existe"

@given(parsers.parse('o sistema tem um usuario "{nome}" com CPF "{cpf}"'))
def sistema_tem_usuario_generico(context, nome, cpf):
    uid = _insert_user(nome=nome, cpf=cpf, tipo="discente", senha="senha123",
                       matricula="20230001", curso="Computacao", status=True)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem um usuario ativo "{nome}" com CPF "{cpf}" e senha "{senha}"'))
def sistema_tem_usuario_ativo(context, nome, cpf, senha):
    uid = _insert_user(nome=nome, cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=True)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem um usuario desativado "{nome}" com CPF "{cpf}" e senha "{senha}"'))
def sistema_tem_usuario_desativado(context, nome, cpf, senha):
    uid = _insert_user(nome=nome, cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=False)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem uma reserva com status "{status}" associada ao usuario com CPF "{cpf}"'))
def sistema_tem_reserva(cpf, status):
    _insert_reservation_for_user(cpf, status)

# ── Steps: WHEN ──────────────────────────────────────────────────────────────

@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'matricula "{matricula}", curso "{curso}" e senha "{senha}"'
))
def when_cadastrar_discente(client, context, nome, cpf, tipo, matricula, curso, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "matricula": matricula, "curso": curso, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'siape "{siape}" e senha "{senha}"'
))
def when_cadastrar_docente(client, context, nome, cpf, tipo, siape, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "siape": siape, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'sem siape e senha "{senha}"'
))
def when_cadastrar_docente_sem_siape(client, context, nome, cpf, tipo, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'eu tento cadastrar o usuario "{nome}" com CPF "{cpf}", tipo "{tipo}", '
    'curso "{curso}", sem matricula e senha "{senha}"'
))
def when_cadastrar_discente_sem_matricula(client, context, nome, cpf, tipo, curso, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "curso": curso, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse('eu realizo o login com CPF "{cpf}" e senha "{senha}"'))
def when_login(client, context, cpf, senha):
    r = client.post("/users/login", json={"cpf": cpf, "senha": senha})
    context["response"] = r

def _patch_user(client, context, payload):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}", json=payload)
    context["response"] = r

@when(parsers.parse('eu atualizo o nome do usuario com CPF "{cpf}" para "{novo_nome}"'))
def when_atualizar_nome(client, context, cpf, novo_nome):
    _patch_user(client, context, {"nome": novo_nome})

@when(parsers.parse('eu atualizo a senha do usuario com CPF "{cpf}" para "{nova_senha}"'))
def when_atualizar_senha(client, context, cpf, nova_senha):
    _patch_user(client, context, {"senha": nova_senha})

@when(parsers.parse('eu tento atualizar a senha do usuario com CPF "{cpf}" para "{nova_senha}"'))
def when_tentar_atualizar_senha(client, context, cpf, nova_senha):
    _patch_user(client, context, {"senha": nova_senha})

@when(parsers.parse('eu solicito a desativacao da conta do usuario com CPF "{cpf}"'))
def when_desativar_conta(client, context, cpf):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}/deactivate")
    context["response"] = r

# ── Steps: THEN ──────────────────────────────────────────────────────────────

@then(parsers.parse(
    'o servidor retorna os dados do usuario "{nome}" com CPF "{cpf}" e tipo "{tipo}"'
))
def then_retorna_dados_com_tipo(context, nome, cpf, tipo):
    body = _assert_response_ok(context, 201)
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    assert _normalize(body.get("nome", "")) == _normalize(nome), \
        f"Nome esperado '{nome}', recebido '{body.get('nome')}'"
    assert body.get("tipo") == tipo, \
        f"Tipo esperado '{tipo}', recebido '{body.get('tipo')}'"

@then(parsers.parse('o sistema armazena o usuario "{nome}" com CPF "{cpf}" e tipo "{tipo}"'))
def then_armazena_usuario_com_tipo(nome, cpf, tipo):
    user = _assert_user_in_db(cpf)
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"
    assert user.tipo.value == tipo, \
        f"Tipo esperado '{tipo}', encontrado '{user.tipo.value}'"

@then(parsers.parse('o status do usuario "{nome}" com CPF "{cpf}" e ativo'))
def then_status_ativo(nome, cpf):
    _assert_user_status_in_db(cpf, expected_status=True)

@then('o servidor retorna um erro informando que o CPF ja esta cadastrado')
def then_erro_cpf_ja_cadastrado(context):
    assert context["response"].status_code == 400, \
        f"Esperava 400, recebeu {context['response'].status_code}: {context['response'].text}"
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "cpf" in detail or "cadastrado" in detail, \
        f"Mensagem de erro inesperada: {context['response'].json().get('detail')}"

@then(parsers.parse('o sistema ainda tem apenas um usuario com CPF "{cpf}"'))
def then_apenas_um_usuario(cpf):
    count = _count_users_by_cpf(cpf)
    assert count == 1, \
        f"Esperava exatamente 1 usuario com CPF {cpf}, encontrou {count}"

@then('o servidor retorna um erro de validacao')
def then_erro_validacao(context):
    assert context["response"].status_code == 422, \
        f"Esperava 422, recebeu {context['response'].status_code}: {context['response'].text}"
    assert "detail" in context["response"].json(), \
        f"Resposta sem campo 'detail': {context['response'].json()}"

@then(parsers.parse('o sistema nao tem um usuario com CPF "{cpf}"'))
def then_sistema_sem_usuario(cpf):
    count = _count_users_by_cpf(cpf)
    assert count == 0, \
        f"Esperava ausencia de usuario com CPF {cpf}, encontrou {count}"

@then(parsers.parse('o servidor retorna os dados do usuario "{nome}" com CPF "{cpf}"'))
def then_retorna_dados_usuario(context, nome, cpf):
    body = _assert_response_ok(context, 200)
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    assert _normalize(body.get("nome", "")) == _normalize(nome), \
        f"Nome esperado '{nome}', recebido '{body.get('nome')}'"

@then('o servidor retorna um erro informando CPF ou senha invalidos')
def then_erro_cpf_ou_senha(context):
    assert context["response"].status_code == 401, \
        f"Esperava 401, recebeu {context['response'].status_code}: {context['response'].text}"
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "cpf" in detail or "senha" in detail or "invalido" in detail, \
        f"Mensagem inesperada: {context['response'].json().get('detail')}"

@then('o servidor retorna um erro informando que a conta esta desativada')
def then_erro_conta_desativada(context):
    assert context["response"].status_code == 403, \
        f"Esperava 403, recebeu {context['response'].status_code}: {context['response'].text}"
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "desativada" in detail or "desativ" in detail, \
        f"Mensagem inesperada: {context['response'].json().get('detail')}"

@then(parsers.parse('o sistema ainda tem o usuario "{nome}" com CPF "{cpf}" com status desativado'))
def then_usuario_ainda_desativado(nome, cpf):
    user = _assert_user_in_db(cpf)
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"
    _assert_user_status_in_db(cpf, expected_status=False)

@then(parsers.parse('o servidor retorna os dados atualizados com nome "{nome}"'))
def then_retorna_dados_atualizados_com_nome(context, nome):
    body = _assert_response_ok(context, 200)
    assert _normalize(body.get("nome", "")) == _normalize(nome), \
        f"Nome esperado '{nome}', recebido '{body.get('nome')}'"

@then(parsers.parse('o sistema armazena o usuario com CPF "{cpf}" com nome "{nome}"'))
def then_armazena_nome(cpf, nome):
    user = _assert_user_in_db(cpf)
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"

@then(parsers.parse('o servidor retorna os dados do usuario com CPF "{cpf}"'))
def then_retorna_dados_por_cpf(context, cpf):
    body = _assert_response_ok(context, 200)
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"

@then(parsers.parse('o sistema permite login com CPF "{cpf}" e senha "{senha}"'))
def then_permite_login(client, cpf, senha):
    r = client.post("/users/login", json={"cpf": cpf, "senha": senha})
    assert r.status_code == 200, \
        f"Login falhou — esperava 200, recebeu {r.status_code}: {r.text}"

@then(parsers.parse('o servidor retorna os dados do usuario com CPF "{cpf}" com status desativado'))
def then_retorna_usuario_desativado(context, cpf):
    body = _assert_response_ok(context, 200)
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    assert body.get("status") is False, \
        f"Esperava status desativado no response, recebido '{body.get('status')}'"

@then(parsers.parse('o sistema armazena o usuario com CPF "{cpf}" com status desativado'))
def then_armazena_usuario_desativado(cpf):
    _assert_user_status_in_db(cpf, expected_status=False)

@then(parsers.parse(
    'o sistema armazena todas as reservas do usuario com CPF "{cpf}" com status "{status}"'
))
def then_reservas_com_status(cpf, status):
    db = SessionTest()
    reservas = db.query(Reservation).filter(Reservation.user_cpf == cpf).all()
    db.close()
    assert len(reservas) > 0, f"Nenhuma reserva encontrada para CPF {cpf}"
    for reserva in reservas:
        assert reserva.status.value == status, \
            f"Reserva {reserva.id} com status '{reserva.status.value}', esperava '{status}'"

@then('o servidor retorna um erro informando que a conta ja esta desativada')
def then_erro_conta_ja_desativada(context):
    assert context["response"].status_code == 400, \
        f"Esperava 400, recebeu {context['response'].status_code}: {context['response'].text}"
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "desativada" in detail or "desativ" in detail, \
        f"Mensagem inesperada: {context['response'].json().get('detail')}"