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

# ── Steps: GIVEN ─────────────────────────────────────────────────────────────

@given(parsers.parse('o sistema nao tem um usuario com CPF "{cpf}"'))
def sistema_sem_usuario(cpf):
    assert _count_users_by_cpf(cpf) == 0, \
        f"Esperava ausencia de usuario com CPF {cpf}, mas ele existe"

@given(parsers.parse('o sistema ja tem um usuario com CPF "{cpf}"'))
def sistema_ja_tem_usuario(cpf):
    _insert_user(nome="John Logan", cpf=cpf, tipo="discente", senha="senha123",
                 matricula="20230001", curso="Computacao")

@given(parsers.parse('o sistema tem um usuario ativo com CPF "{cpf}" e senha "{senha}"'))
def sistema_tem_usuario_ativo(context, cpf, senha):
    uid = _insert_user(nome="John Logan", cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=True)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem um usuario ativo com CPF "{cpf}", nome "{nome}" e senha "{senha}"'))
def sistema_tem_usuario_ativo_com_nome(context, cpf, nome, senha):
    uid = _insert_user(nome=nome, cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=True)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem um usuario ativo com CPF "{cpf}"'))
def sistema_tem_usuario_ativo_sem_senha(context, cpf):
    uid = _insert_user(nome="John Logan", cpf=cpf, tipo="discente", senha="senha123",
                       matricula="20230001", curso="Computacao", status=True)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem um usuario desativado com CPF "{cpf}" e senha "{senha}"'))
def sistema_tem_usuario_desativado_com_senha(context, cpf, senha):
    uid = _insert_user(nome="John Logan", cpf=cpf, tipo="discente", senha=senha,
                       matricula="20230001", curso="Computacao", status=False)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem um usuario desativado com CPF "{cpf}"'))
def sistema_tem_usuario_desativado(context, cpf):
    uid = _insert_user(nome="John Logan", cpf=cpf, tipo="discente", senha="senha123",
                       matricula="20230001", curso="Computacao", status=False)
    context["user_id"] = uid
    context["user_cpf"] = cpf

@given(parsers.parse('o sistema tem uma reserva com status "{status}" associada ao usuario com CPF "{cpf}"'))
def sistema_tem_reserva(cpf, status):
    _insert_reservation_for_user(cpf, status)

@given(parsers.parse('o sistema nao tem reservas associadas ao usuario com CPF "{cpf}"'))
def sistema_sem_reservas(cpf):
    db = SessionTest()
    count = db.query(Reservation).filter(Reservation.user_cpf == cpf).count()
    db.close()
    assert count == 0, f"Esperava ausencia de reservas para CPF {cpf}, mas existem {count}"

# ── Steps: WHEN ──────────────────────────────────────────────────────────────

@when(parsers.parse(
    'uma requisicao "POST" for enviada para "/users" com nome "{nome}", CPF "{cpf}", '
    'tipo "{tipo}", matricula "{matricula}", curso "{curso}" e senha "{senha}"'
))
def post_cadastrar_discente(client, context, nome, cpf, tipo, matricula, curso, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "matricula": matricula, "curso": curso, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'uma requisicao "POST" for enviada para "/users" com nome "{nome}", CPF "{cpf}", '
    'tipo "{tipo}", siape "{siape}" e senha "{senha}"'
))
def post_cadastrar_docente(client, context, nome, cpf, tipo, siape, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "siape": siape, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'uma requisicao "POST" for enviada para "/users" com nome "{nome}", CPF "{cpf}", '
    'tipo "{tipo}", sem siape e senha "{senha}"'
))
def post_cadastrar_docente_sem_siape(client, context, nome, cpf, tipo, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'uma requisicao "POST" for enviada para "/users" com nome "{nome}", CPF "{cpf}", '
    'tipo "{tipo}", curso "{curso}", sem matricula e senha "{senha}"'
))
def post_cadastrar_discente_sem_matricula(client, context, nome, cpf, tipo, curso, senha):
    r = client.post("/users/", json={
        "nome": nome, "cpf": cpf, "tipo": tipo,
        "curso": curso, "senha": senha,
    })
    context["response"] = r

@when(parsers.parse(
    'uma requisicao "POST" for enviada para "/users/login" com CPF "{cpf}" e senha "{senha}"'
))
def post_login(client, context, cpf, senha):
    r = client.post("/users/login", json={"cpf": cpf, "senha": senha})
    context["response"] = r

@when(parsers.parse(
    'uma requisicao "PATCH" for enviada para "/users/{cpf}" com o novo nome "{novo_nome}"'
))
def patch_atualizar_nome(client, context, cpf, novo_nome):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}", json={"nome": novo_nome})
    context["response"] = r

@when(parsers.parse(
    'uma requisicao "PATCH" for enviada para "/users/{cpf}" com a nova senha "{nova_senha}"'
))
def patch_atualizar_senha(client, context, cpf, nova_senha):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}", json={"senha": nova_senha})
    context["response"] = r

@when(parsers.parse('uma requisicao "PATCH" for enviada para "/users/{cpf}/deactivate"'))
def patch_desativar_conta(client, context, cpf):
    user_id = context.get("user_id")
    r = client.patch(f"/users/{user_id}/deactivate")
    context["response"] = r

# ── Steps: THEN ──────────────────────────────────────────────────────────────

@then(parsers.parse('o status da resposta deve ser "{status_code}"'))
def status_da_resposta(context, status_code):
    r = context["response"]
    assert r.status_code == int(status_code), \
        f"Esperava {status_code}, recebeu {r.status_code}: {r.text}"

@then(parsers.parse(
    'o JSON da resposta deve conter CPF "{cpf}", nome "{nome}", tipo "{tipo}" e status "{status}"'
))
def json_contem_dados_cadastro_discente(context, cpf, nome, tipo, status):
    body = context["response"].json()
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    assert _normalize(body.get("nome", "")) == _normalize(nome), \
        f"Nome esperado '{nome}', recebido '{body.get('nome')}'"
    assert body.get("tipo") == tipo, \
        f"Tipo esperado '{tipo}', recebido '{body.get('tipo')}'"
    status_bool = status == "ativo"
    assert body.get("status") == status_bool, \
        f"Status esperado '{status}' ({status_bool}), recebido '{body.get('status')}'"

@then(parsers.parse(
    'o JSON da resposta deve conter CPF "{cpf}", nome "{nome}" e tipo "{tipo}"'
))
def json_contem_dados_cadastro_docente(context, cpf, nome, tipo):
    body = context["response"].json()
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    assert _normalize(body.get("nome", "")) == _normalize(nome), \
        f"Nome esperado '{nome}', recebido '{body.get('nome')}'"
    assert body.get("tipo") == tipo, \
        f"Tipo esperado '{tipo}', recebido '{body.get('tipo')}'"

@then('o JSON da resposta deve conter uma mensagem informando que o CPF ja esta cadastrado')
def json_erro_cpf_ja_cadastrado(context):
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "cpf" in detail or "cadastrado" in detail, \
        f"Mensagem de erro inesperada: {context['response'].json().get('detail')}"

@then(parsers.parse(
    'uma requisicao "GET" para "/users?cpf={cpf}" retorna exatamente 1 usuario'
))
def get_retorna_exatamente_um_usuario(cpf):
    assert _count_users_by_cpf(cpf) == 1, \
        f"Esperava exatamente 1 usuario com CPF {cpf}, encontrou {_count_users_by_cpf(cpf)}"

@then('o JSON da resposta deve conter uma mensagem de erro de validacao')
def json_erro_validacao(context):
    # FastAPI/Pydantic retorna 422 com lista de erros em "detail"
    body = context["response"].json()
    assert "detail" in body, f"Resposta sem campo 'detail': {body}"

@then(parsers.parse('o JSON da resposta deve conter CPF "{cpf}" e nome "{nome}"'))
def json_contem_cpf_e_nome(context, cpf, nome):
    body = context["response"].json()
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    assert _normalize(body.get("nome", "")) == _normalize(nome), \
        f"Nome esperado '{nome}', recebido '{body.get('nome')}'"

@then('o JSON da resposta deve conter uma mensagem informando CPF ou senha invalidos')
def json_erro_cpf_ou_senha(context):
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "cpf" in detail or "senha" in detail or "invalido" in detail, \
        f"Mensagem inesperada: {context['response'].json().get('detail')}"

@then('o JSON da resposta deve conter uma mensagem informando que a conta esta desativada')
def json_erro_conta_desativada(context):
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "desativada" in detail or "desativ" in detail, \
        f"Mensagem inesperada: {context['response'].json().get('detail')}"

@then(parsers.parse(
    'uma requisicao "POST" para "/users/login" com CPF "{cpf}" e senha "{senha}" retorna status "{status_code}"'
))
def post_login_retorna_status(client, cpf, senha, status_code):
    r = client.post("/users/login", json={"cpf": cpf, "senha": senha})
    assert r.status_code == int(status_code), \
        f"Esperava {status_code} para login com CPF {cpf}, recebeu {r.status_code}: {r.text}"

@then(parsers.parse('o JSON da resposta deve conter CPF "{cpf}" e status "{status}"'))
def json_contem_cpf_e_status(context, cpf, status):
    body = context["response"].json()
    assert body.get("cpf") == cpf, \
        f"CPF esperado '{cpf}', recebido '{body.get('cpf')}'"
    status_bool = status == "ativo"
    assert body.get("status") == status_bool, \
        f"Status esperado '{status}' ({status_bool}), recebido '{body.get('status')}'"

@then(parsers.parse(
    'o sistema deve ter todas as reservas do usuario com CPF "{cpf}" com status "{status}"'
))
def sistema_reservas_com_status(cpf, status):
    db = SessionTest()
    reservas = db.query(Reservation).filter(Reservation.user_cpf == cpf).all()
    db.close()
    assert len(reservas) > 0, f"Nenhuma reserva encontrada para CPF {cpf}"
    for reserva in reservas:
        assert reserva.status.value == status, \
            f"Reserva {reserva.id} com status '{reserva.status.value}', esperava '{status}'"

@then('o JSON da resposta deve conter uma mensagem informando que a conta ja esta desativada')
def json_erro_conta_ja_desativada(context):
    detail = _normalize(context["response"].json().get("detail", ""))
    assert "desativada" in detail or "desativ" in detail, \
        f"Mensagem inesperada: {context['response'].json().get('detail')}"

@then(parsers.parse('o sistema armazena o usuario "{nome}" com CPF "{cpf}" e tipo "{tipo}"'))
def sistema_armazena_usuario_com_tipo(nome, cpf, tipo):
    user = _get_user_by_cpf(cpf)
    assert user is not None, f"Usuario com CPF {cpf} nao encontrado no banco"
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"
    assert user.tipo.value == tipo, \
        f"Tipo esperado '{tipo}', encontrado '{user.tipo.value}'"

@then(parsers.parse('o status do usuario com CPF "{cpf}" e "{status}"'))
def status_do_usuario(cpf, status):
    user = _get_user_by_cpf(cpf)
    assert user is not None, f"Usuario com CPF {cpf} nao encontrado"
    status_bool = status == "ativo"
    assert user.status == status_bool, \
        f"Esperava status '{status}' ({status_bool}), encontrado '{user.status}'"

@then(parsers.parse('o sistema armazena o usuario com CPF "{cpf}" com nome "{nome}"'))
def sistema_armazena_nome(cpf, nome):
    user = _get_user_by_cpf(cpf)
    assert user is not None, f"Usuario com CPF {cpf} nao encontrado"
    assert _normalize(user.nome) == _normalize(nome), \
        f"Nome esperado '{nome}', encontrado '{user.nome}'"