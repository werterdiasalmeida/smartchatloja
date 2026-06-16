from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/estatisticas")
def obter_estatisticas(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Retorna estatísticas gerais do sistema para o dashboard.
    """
    # Empresas
    total_empresas = db.query(func.count(models.Empresa.id)).scalar() or 0
    empresas_ativas = db.query(func.count(models.Empresa.id)).filter(
        models.Empresa.is_ativo == True
    ).scalar() or 0
    
    # Usuários
    total_usuarios = db.query(func.count(models.Usuario.id)).scalar() or 0
    usuarios_internos = db.query(func.count(models.Usuario.id)).filter(
        models.Usuario.tipo == 'interno'
    ).scalar() or 0
    usuarios_empresas = db.query(func.count(models.Usuario.id)).filter(
        models.Usuario.tipo == 'empresa'
    ).scalar() or 0
    
    # Produtos
    total_produtos = db.query(func.count(models.Produto.id)).filter(
        models.Produto.is_ativo == True
    ).scalar() or 0
    
    produtos_sem_estoque = db.query(func.count(models.Produto.id)).filter(
        models.Produto.is_ativo == True,
        models.Produto.estoque_atual <= 0
    ).scalar() or 0
    
    # Valor total em estoque (preço * quantidade)
    valor_estoque = db.query(
        func.sum(models.Produto.preco * models.Produto.estoque_atual)
    ).filter(
        models.Produto.is_ativo == True
    ).scalar() or 0.0
    
    # Produtos por empresa (top 5)
    produtos_por_empresa = db.query(
        models.Empresa.nome,
        func.count(models.Produto.id).label('total')
    ).join(
        models.Produto, models.Empresa.id == models.Produto.empresa_id
    ).filter(
        models.Produto.is_ativo == True
    ).group_by(
        models.Empresa.id, models.Empresa.nome
    ).order_by(
        func.count(models.Produto.id).desc()
    ).limit(5).all()
    
    return {
        "empresas": {
            "total": total_empresas,
            "ativas": empresas_ativas
        },
        "usuarios": {
            "total": total_usuarios,
            "internos": usuarios_internos,
            "empresas": usuarios_empresas
        },
        "produtos": {
            "total": total_produtos,
            "sem_estoque": produtos_sem_estoque,
            "valor_total_estoque": float(valor_estoque)
        },
        "top_empresas": [
            {"nome": nome, "total_produtos": total}
            for nome, total in produtos_por_empresa
        ]
    }