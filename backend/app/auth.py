from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas
from .config import settings

# Configuração do Bcrypt (mesma usada no seed.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurações do JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha informada corresponde ao hash armazenado."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera o hash da senha usando bcrypt."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str):
    """
    Autentica um usuário verificando primeiro em AdminInterno, depois em Usuario (tipo interno).
    Retorna uma tupla: (objeto_usuario, tipo_string)
    """
    # 1. Tentar autenticar como AdminInterno
    admin = db.query(models.AdminInterno).filter(
        models.AdminInterno.email == email
    ).first()

    if admin:
        if not admin.senha_hash or not verify_password(password, admin.senha_hash) or not admin.is_ativo:
            return None, None
        return admin, 'admin'

    # 2. Tentar autenticar como Usuario (tipo interno)
    usuario = db.query(models.Usuario).filter(
        models.Usuario.email == email,
        models.Usuario.tipo == 'interno'
    ).first()

    if usuario:
        if not usuario.senha_hash or not verify_password(password, usuario.senha_hash) or not usuario.is_ativo:
            return None, None
        return usuario, 'usuario'

    # 3. Não encontrou em nenhuma tabela
    return None, None


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Cria um token JWT com os dados fornecidos."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Tuple[Any, str]:
    """
    Dependência para extrair e validar o usuário atual do token JWT.
    Retorna uma tupla: (objeto_usuario, 'admin' ou 'usuario')
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_tipo: str = payload.get("tipo")

        if email is None or user_tipo is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = None
    
    # Buscar na tabela correta com base no tipo
    if user_tipo == 'admin':
        user = db.query(models.AdminInterno).filter(models.AdminInterno.email == email).first()
    elif user_tipo == 'usuario':
        user = db.query(models.Usuario).filter(
            models.Usuario.email == email,
            models.Usuario.tipo == 'interno'
        ).first()

    if user is None:
        raise credentials_exception

    if not getattr(user, 'is_ativo', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    return user, user_tipo


async def get_current_active_user(
    current_user_data: Tuple[Any, str] = Depends(get_current_user)
) -> Tuple[Any, str]:
    """
    Dependência para garantir que o usuário atual está ativo.
    Repassa a tupla (user, tipo) para os endpoints.
    """
    return current_user_data