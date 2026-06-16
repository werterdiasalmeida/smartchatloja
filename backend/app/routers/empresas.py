from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/empresas", tags=["Empresas"])


@router.post("/", response_model=schemas.EmpresaResponse, status_code=status.HTTP_201_CREATED)
def criar_empresa(
    empresa: schemas.EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Cria uma nova empresa. Requer autenticação de admin interno.
    """
    # Verificar se CNPJ já existe (se fornecido)
    if empresa.cnpj:
        empresa_existente = db.query(models.Empresa).filter(
            models.Empresa.cnpj == empresa.cnpj
        ).first()
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma empresa com este CNPJ"
            )
    
    # Verificar se email do representante já está em uso
    representante_existente = db.query(models.Empresa).filter(
        models.Empresa.representante_email == empresa.representante_email
    ).first()
    if representante_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma empresa com este email de representante"
        )
    
    # Criar nova empresa
    nova_empresa = models.Empresa(**empresa.dict())
    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)
    
    return nova_empresa


@router.get("/", response_model=List[schemas.EmpresaResponse])
def listar_empresas(
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Lista todas as empresas cadastradas. Requer autenticação.
    """
    empresas = db.query(models.Empresa).order_by(models.Empresa.criado_em.desc()).all()
    return empresas


@router.get("/{empresa_id}", response_model=schemas.EmpresaResponse)
def obter_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Obtém os detalhes de uma empresa específica. Requer autenticação.
    """
    empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    return empresa


@router.put("/{empresa_id}", response_model=schemas.EmpresaResponse)
def atualizar_empresa(
    empresa_id: int,
    empresa_update: schemas.EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    
    update_data = empresa_update.dict(exclude_unset=True)
    
    # 1. Validar CNPJ único (se estiver sendo alterado)
    if 'cnpj' in update_data and update_data['cnpj'] and update_data['cnpj'] != empresa.cnpj:
        if db.query(models.Empresa).filter(models.Empresa.cnpj == update_data['cnpj'], models.Empresa.id != empresa_id).first():
            raise HTTPException(status_code=400, detail="CNPJ já está em uso por outra empresa.")
    
    # 2. Validar E-mail do Representante único (se estiver sendo alterado)
    if 'representante_email' in update_data and update_data['representante_email'] != empresa.representante_email:
        novo_email = update_data['representante_email']
        
        # Verifica se outra empresa já usa este e-mail
        if db.query(models.Empresa).filter(models.Empresa.representante_email == novo_email, models.Empresa.id != empresa_id).first():
            raise HTTPException(status_code=400, detail="E-mail do representante já está em uso por outra empresa.")
        
        # Verifica se outro USUÁRIO já usa este e-mail (Crucial!)
        usuario_com_mesmo_email = db.query(models.Usuario).filter(
            models.Usuario.email == novo_email,
            models.Usuario.empresa_id != empresa_id # Permite manter o mesmo se for o próprio usuário
        ).first()
        if usuario_com_mesmo_email:
            raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado em outro usuário do sistema.")

    # 3. Atualizar dados da Empresa na memória
    for field, value in update_data.items():
        setattr(empresa, field, value)
    
    # 4. Sincronizar com o Usuário vinculado
    usuario = db.query(models.Usuario).filter(
        models.Usuario.empresa_id == empresa_id,
        models.Usuario.tipo == 'empresa'
    ).first()
    
    if usuario:
        # Se o nome mudou na empresa, muda no usuário
        if 'representante_nome' in update_data and update_data['representante_nome'] != usuario.nome:
            usuario.nome = update_data['representante_nome']
            
        # Se o e-mail mudou na empresa, muda no usuário
        if 'representante_email' in update_data and update_data['representante_email'] != usuario.email:
            usuario.email = update_data['representante_email']
            
    # 5. Salvar no banco com tratamento de erro
    try:
        db.commit()
        db.refresh(empresa)
        return empresa
    except Exception as e:
        db.rollback()
        # Isso vai mostrar o erro exato no frontend se algo der errado no banco
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar dados: {str(e)}")


@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Desativa uma empresa (soft delete). Requer autenticação.
    """
    empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    empresa.is_ativo = False
    db.commit()
    
    return None
@router.patch("/{empresa_id}/reativar", response_model=schemas.EmpresaResponse)
def reativar_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminInterno = Depends(get_current_active_user)
):
    """
    Reativa uma empresa que estava inativa.
    """
    empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    empresa.is_ativo = True
    db.commit()
    db.refresh(empresa)
    
    return empresa    