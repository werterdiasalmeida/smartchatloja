from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user, get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


@router.post("/", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Cria um novo usuário. Requer autenticação de admin interno.
    Se o tipo for 'empresa', o empresa_id é obrigatório e deve existir.
    """
    # Validação: Se for tipo empresa, empresa_id é obrigatório
    if usuario.tipo == 'empresa' and not usuario.empresa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O campo 'empresa_id' é obrigatório para usuários do tipo 'empresa'."
        )
    
    # Validação: Verificar se a empresa existe (se fornecida)
    if usuario.empresa_id:
        empresa = db.query(models.Empresa).filter(models.Empresa.id == usuario.empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada."
            )
        if not empresa.is_ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível vincular usuário a uma empresa inativa."
            )

    # Verificar se e-mail já está em uso
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este e-mail."
        )
    
    # Criar novo usuário com senha hasheada
    novo_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=get_password_hash(usuario.senha),
        tipo=usuario.tipo,
        empresa_id=usuario.empresa_id,
        is_ativo=True
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return novo_usuario


@router.get("/", response_model=List[schemas.UsuarioResponse])
def listar_usuarios(
    tipo: str = None,
    empresa_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Lista usuários. Permite filtrar por tipo ('interno' ou 'empresa') ou por empresa_id.
    """
    query = db.query(models.Usuario)
    
    if tipo:
        query = query.filter(models.Usuario.tipo == tipo)
    if empresa_id:
        query = query.filter(models.Usuario.empresa_id == empresa_id)
        
    usuarios = query.order_by(models.Usuario.criado_em.desc()).all()
    return usuarios


@router.get("/{usuario_id}", response_model=schemas.UsuarioResponse)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Obtém os detalhes de um usuário específico.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return usuario


@router.put("/{usuario_id}", response_model=schemas.UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    usuario_update: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Atualiza os dados de um usuário.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Se estiver tentando mudar o e-mail, verificar se já existe
    update_data = usuario_update.dict(exclude_unset=True)
    if 'email' in update_data and update_data['email'] != usuario.email:
        existente = db.query(models.Usuario).filter(models.Usuario.email == update_data['email']).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um usuário com este e-mail."
            )
    
    # Se estiver tentando mudar para tipo empresa, validar empresa_id
    if update_data.get('tipo') == 'empresa' and not update_data.get('empresa_id') and not usuario.empresa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O campo 'empresa_id' é obrigatório para usuários do tipo 'empresa'."
        )

    # Hashear senha se estiver sendo atualizada
    if 'senha' in update_data:
        update_data['senha_hash'] = get_password_hash(update_data.pop('senha'))
    
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.patch("/{usuario_id}/desativar", response_model=schemas.UsuarioResponse)
def desativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Desativa um usuário (soft delete).
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Proteção: não permitir desativar a si mesmo
    if usuario.email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar sua própria conta."
        )
    
    usuario.is_ativo = False
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.patch("/{usuario_id}/reativar", response_model=schemas.UsuarioResponse)
def reativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Reativa um usuário que estava inativo.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    usuario.is_ativo = True
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Deleta permanentemente um usuário do banco de dados.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Proteção: não permitir deletar a si mesmo
    if usuario.email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode deletar sua própria conta."
        )
    
    db.delete(usuario)
    db.commit()
    
    return None