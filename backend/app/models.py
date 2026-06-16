from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, LargeBinary
from sqlalchemy.sql import func
from app.database import Base

class AdminInterno(Base):
    __tablename__ = "admins_internos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    is_ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cnpj = Column(String, unique=True, index=True, nullable=True)
    email_contato = Column(String, nullable=True)
    
    # Dados do Representante
    representante_nome = Column(String, nullable=False)
    representante_email = Column(String, nullable=False, index=True)
    representante_telefone = Column(String, nullable=True)
    
    # Status
    is_ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    
    # Tipo de usuário: 'interno' (admin do sistema) ou 'empresa' (representante)
    tipo = Column(String, nullable=False, default='interno')
    
    # Se for tipo 'empresa', vincula à empresa
    empresa_id = Column(Integer, nullable=True)
    
    # Status e controle
    is_ativo = Column(Boolean, default=True)
    ultimo_acesso = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    
    # Vínculo
    empresa_id = Column(Integer, nullable=False, index=True)
    
    # Identificação (SKU é crucial para o ETL saber se é update ou insert)
    sku = Column(String, nullable=False, index=True) 
    nome = Column(String, nullable=False)
    marca = Column(String, nullable=True)
    modelo = Column(String, nullable=True)
    descricao = Column(Text, nullable=True)
    
    # Atributos
    categoria = Column(String, nullable=True)
    cor = Column(String, nullable=True)
    tamanho = Column(String, nullable=True)
    
    # Dados Comerciais
    preco = Column(Float, nullable=False, default=0.0)
    estoque_atual = Column(Integer, nullable=False, default=0)
    
    # Mídia (Armazenamento local da imagem)
    imagem_blob = Column(LargeBinary, nullable=True)      # A imagem em bytes
    imagem_mime_type = Column(String, nullable=True)      # Ex: 'image/jpeg', 'image/png'
    
    # Controle
    is_ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())