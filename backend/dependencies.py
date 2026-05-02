from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from database import get_db
import models
import auth

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    try:
        payload = auth.decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(models.User).filter(
        models.User.id == user_id, models.User.ativo == True
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


def require_docente_or_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.tipo not in ("docente", "admin"):
        raise HTTPException(status_code=403, detail="Acesso restrito a docentes e administradores")
    return current_user
