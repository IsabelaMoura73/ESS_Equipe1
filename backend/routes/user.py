from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from models.reservation import Reservation, ReservationStatus
from schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(user: UserCreate, db: Session = Depends(get_db)):
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

@router.post("/login", response_model=UserResponse)
def login(dados: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.cpf == dados.cpf).first()
    if not user or not pwd_context.verify(dados.senha, user.senha):
        raise HTTPException(status_code=401, detail="CPF ou senha inválidos")

    if not user.status:
        raise HTTPException(status_code=403, detail="Conta desativada")
    
    return user

@router.get("/", response_model=List[UserResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserResponse)
def buscar_usuario(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@router.patch("/{user_id}", response_model=UserResponse)
def atualizar_usuario(user_id: int, dados: UserUpdate, db: Session = Depends(get_db)):
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

@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def desativar_usuario(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if not user.status:
        raise HTTPException(status_code=400, detail="Conta já desativada")
    
    db.query(Reservation).filter(Reservation.user_cpf == user.cpf, Reservation.status.in_([ReservationStatus.pending, ReservationStatus.confirmed])
    ).update({"status": ReservationStatus.denied}, synchronize_session=False)

    user.status = False
    db.commit()
    db.refresh(user)
    return user