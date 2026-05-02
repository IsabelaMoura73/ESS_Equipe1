from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
import models, schemas, auth

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.cpf == data.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado no sistema.")

    user = models.User(
        nome=data.nome,
        cpf=data.cpf,
        senha_hash=auth.hash_password(data.senha),
        tipo=data.tipo,
        matricula=data.matricula,
        curso=data.curso,
        siape=data.siape,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.cpf == data.cpf).first()
    if not user or not auth.verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="CPF ou senha incorretos.")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Conta desativada.")

    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not auth.verify_password(data.senha, current_user.senha_hash):
        raise HTTPException(status_code=400, detail="Senha incorreta.")

    if data.nome is not None:
        if not data.nome.strip():
            raise HTTPException(status_code=400, detail="O campo Nome não pode ser vazio.")
        current_user.nome = data.nome

    if data.nova_senha is not None:
        current_user.senha_hash = auth.hash_password(data.nova_senha)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me")
def deactivate_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for res in current_user.reservas_sala:
        if res.status in ("pendente", "confirmada"):
            res.status = "cancelada"
    for res in current_user.reservas_lab:
        if res.status in ("pendente", "confirmada"):
            res.status = "cancelada"

    current_user.ativo = False
    db.commit()
    return {"message": "Conta desativada com sucesso!"}
