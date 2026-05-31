from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user import User
from models.reservation import Reservation, ReservationStatus
from schemas.user import UserCreate, UserUpdate, UserLogin
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def criar_usuario_service(user: UserCreate, db: Session) -> User:
    db_user = db.query(User).filter(User.cpf == user.cpf).first()
    if db_user:
        raise HTTPException(status_code=400, detail="CPF já cadastrado")

    dados = user.model_dump()
    dados["senha"] = pwd_context.hash(dados["senha"])

    novo_usuario = User(**dados)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

def login_service(dados: UserLogin, db: Session) -> User:
    user = db.query(User).filter(User.cpf == dados.cpf).first()
    if not user or not pwd_context.verify(dados.senha, user.senha):
        raise HTTPException(status_code=401, detail="CPF ou senha inválidos")

    if not user.status:
        raise HTTPException(status_code=403, detail="Conta desativada")

    return user

def listar_usuarios_service(db: Session) -> list[User]:
    return db.query(User).all()

def buscar_usuario_service(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

def atualizar_usuario_service(user_id: int, dados: UserUpdate, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    dados_dict = dados.model_dump(exclude_unset=True)

    if "senha" in dados_dict:
        dados_dict["senha"] = pwd_context.hash(dados_dict["senha"])

    for campo, valor in dados_dict.items():
        setattr(user, campo, valor)

    db.commit()
    db.refresh(user)
    return user

def desativar_usuario_service(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not user.status:
        raise HTTPException(status_code=400, detail="Conta já desativada")

    db.query(Reservation).filter(
        Reservation.user_cpf == user.cpf,
        Reservation.status.in_([ReservationStatus.pending, ReservationStatus.confirmed])
    ).update({"status": ReservationStatus.denied}, synchronize_session=False)

    user.status = False
    db.commit()
    db.refresh(user)
    return user