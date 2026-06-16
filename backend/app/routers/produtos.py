import base64
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/produtos", tags=["Produtos"])


def format_produto_response(produto: models.Produto, empresas_dict: dict = None) -> dict:
    if empresas_dict is None:
        empresas_dict = {}
        
    resp = {
        "id": produto.id,
        "empresa_id": produto.empresa_id,
        "empresa_nome": empresas_dict.get(produto.empresa_id, "Empresa Desconhecida"),
        "sku": produto.sku,
        "nome": produto.nome,
        "marca": produto.marca,
        "modelo": produto.modelo,
        "descricao": produto.descricao,
        "categoria": produto.categoria,
        "cor": produto.cor,
        "tamanho": produto.tamanho,
        "preco": produto.preco,
        "estoque_atual": produto.estoque_atual,
        "imagem_mime_type": produto.imagem_mime_type,
        "is_ativo": produto.is_ativo,
        "criado_em": produto.criado_em,
        "atualizado_em": produto.atualizado_em,
        "imagem_base64": None
    }
    
    if produto.imagem_blob:
        mime = produto.imagem_mime_type or "image/jpeg"
        b64_bytes = base64.b64encode(produto.imagem_blob)
        resp["imagem_base64"] = f"data:{mime};base64,{b64_bytes.decode('utf-8')}"
        
    return resp


@router.post("/", status_code=status.HTTP_201_CREATED)
def upsert_produto(
    produto_in: schemas.ProdutoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    sku_final = produto_in.sku.strip() if produto_in.sku else ""
    if not sku_final:
        random_suffix = secrets.token_hex(4).upper()
        sku_final = f"EMP{produto_in.empresa_id}-{random_suffix}"

    existing = db.query(models.Produto).filter(
        models.Produto.sku == sku_final,
        models.Produto.empresa_id == produto_in.empresa_id
    ).first()

    image_bytes = None
    mime_type = produto_in.imagem_mime_type
    
    if produto_in.imagem_base64:
        b64_data = produto_in.imagem_base64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        try:
            image_bytes = base64.b64decode(b64_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de imagem base64 inválido")

    # Busca nome da empresa para o retorno
    emp = db.query(models.Empresa).filter(models.Empresa.id == produto_in.empresa_id).first()
    emp_dict = {produto_in.empresa_id: emp.nome} if emp else {}

    if existing:
        update_data = produto_in.dict(exclude_unset=True)
        update_data.pop("imagem_base64", None)
        update_data.pop("sku", None)
        
        for field, value in update_data.items():
            setattr(existing, field, value)
        
        if image_bytes is not None:
            existing.imagem_blob = image_bytes
        if mime_type:
            existing.imagem_mime_type = mime_type
            
        db.commit()
        db.refresh(existing)
        return format_produto_response(existing, emp_dict)
        
    else:
        novo_produto = models.Produto(
            empresa_id=produto_in.empresa_id,
            sku=sku_final,
            nome=produto_in.nome,
            marca=produto_in.marca,
            modelo=produto_in.modelo,
            descricao=produto_in.descricao,
            categoria=produto_in.categoria,
            cor=produto_in.cor,
            tamanho=produto_in.tamanho,
            preco=produto_in.preco,
            estoque_atual=produto_in.estoque_atual,
            imagem_blob=image_bytes,
            imagem_mime_type=mime_type,
            is_ativo=True
        )
        db.add(novo_produto)
        db.commit()
        db.refresh(novo_produto)
        return format_produto_response(novo_produto, emp_dict)


@router.get("/")
def listar_produtos(
    empresa_id: Optional[int] = Query(None, description="Filtrar por ID da empresa"),
    skip: int = Query(0, ge=0, description="Quantos registros pular"),
    limit: int = Query(50, ge=1, le=100, description="Limite de registros por página"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Busca todas as empresas uma única vez para evitar N+1 queries
    empresas_dict = {e.id: e.nome for e in db.query(models.Empresa.id, models.Empresa.nome).all()}
    
    query = db.query(models.Produto).filter(models.Produto.is_ativo == True)
    if empresa_id:
        query = query.filter(models.Produto.empresa_id == empresa_id)
    
    produtos = query.order_by(models.Produto.atualizado_em.desc()).offset(skip).limit(limit).all()
    return [format_produto_response(p, empresas_dict) for p in produtos]


@router.get("/{produto_id}")
def obter_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    emp = db.query(models.Empresa).filter(models.Empresa.id == produto.empresa_id).first()
    emp_dict = {produto.empresa_id: emp.nome} if emp else {}
    
    return format_produto_response(produto, emp_dict)


@router.put("/{produto_id}")
def atualizar_produto(
    produto_id: int,
    produto_update: schemas.ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    update_data = produto_update.dict(exclude_unset=True)
    
    if "imagem_base64" in update_data:
        b64_data = update_data.pop("imagem_base64")
        if b64_data:
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            try:
                produto.imagem_blob = base64.b64decode(b64_data)
            except Exception:
                raise HTTPException(status_code=400, detail="Formato de imagem base64 inválido")
    
    if "imagem_mime_type" in update_data:
        produto.imagem_mime_type = update_data.pop("imagem_mime_type")

    for field, value in update_data.items():
        setattr(produto, field, value)

    db.commit()
    db.refresh(produto)
    
    emp = db.query(models.Empresa).filter(models.Empresa.id == produto.empresa_id).first()
    emp_dict = {produto.empresa_id: emp.nome} if emp else {}
    
    return format_produto_response(produto, emp_dict)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    produto.is_ativo = False
    db.commit()
    return None