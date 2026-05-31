from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from services.user import (
    criar_usuario_service,
    login_service,
    listar_usuarios_service,
    buscar_usuario_service,
    atualizar_usuario_service,
    desativar_usuario_service,
)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(user: UserCreate, db: Session = Depends(get_db)):
    return criar_usuario_service(user, db)

@router.post("/login", response_model=UserResponse)
def login(dados: UserLogin, db: Session = Depends(get_db)):
    return login_service(dados, db)

@router.get("/", response_model=List[UserResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return listar_usuarios_service(db)

@router.get("/{user_id}", response_model=UserResponse)
def buscar_usuario(user_id: int, db: Session = Depends(get_db)):
    return buscar_usuario_service(user_id, db)

@router.patch("/{user_id}", response_model=UserResponse)
def atualizar_usuario(user_id: int, dados: UserUpdate, db: Session = Depends(get_db)):
    return atualizar_usuario_service(user_id, dados, db)

@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def desativar_usuario(user_id: int, db: Session = Depends(get_db)):
    return desativar_usuario_service(user_id, db)