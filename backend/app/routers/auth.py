from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, models
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de login. Aceita tanto AdminInterno quanto Usuario (tipo interno).
    """
    usuario, tipo = authenticate_user(db, form_data.username, form_data.password)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Incluir o tipo no token para controle de acesso
    token_data = {
        "sub": usuario.email, 
        "id": usuario.id,
        "tipo": tipo
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def read_users_me(
    current_user_data = Depends(get_current_active_user)
):
    """
    Retorna os dados do usuário autenticado (seja AdminInterno ou Usuario interno).
    """
    user, user_tipo = current_user_data
    
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "tipo": user_tipo,
        "is_ativo": user.is_ativo
    }


@router.post("/test")
async def test_auth(
    current_user_data = Depends(get_current_active_user)
):
    """
    Endpoint de teste para verificar se a autenticação está funcionando.
    """
    user, user_tipo = current_user_data
    
    return {
        "message": "Autenticação funcionando!",
        "user": user.email,
        "id": user.id,
        "tipo": user_tipo
    }