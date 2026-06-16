from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ==========================================
# SCHEMAS DE AUTENTICAÇÃO
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ==========================================
# SCHEMAS DO ADMIN INTERNO
# ==========================================

class AdminBase(BaseModel):
    nome: str
    email: EmailStr

class AdminCreate(AdminBase):
    senha: str

class AdminLogin(BaseModel):
    email: EmailStr
    senha: str

class AdminResponse(AdminBase):
    id: int
    is_ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True

# ==========================================
# SCHEMAS DA EMPRESA
# ==========================================

class EmpresaBase(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    email_contato: Optional[str] = None
    representante_nome: str
    representante_email: EmailStr
    representante_telefone: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    email_contato: Optional[str] = None
    representante_nome: Optional[str] = None
    representante_email: Optional[EmailStr] = None
    representante_telefone: Optional[str] = None
    is_ativo: Optional[bool] = None

class EmpresaResponse(EmpresaBase):
    id: int
    is_ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True

# ==========================================
# SCHEMAS DO USUÁRIO
# ==========================================

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    tipo: str
    empresa_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    tipo: Optional[str] = None
    empresa_id: Optional[int] = None
    senha: Optional[str] = None
    is_ativo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: int
    is_ativo: bool
    ultimo_acesso: Optional[datetime] = None
    criado_em: datetime

    class Config:
        from_attributes = True

# ==========================================
# SCHEMAS DO PRODUTO
# ==========================================

class ProdutoBase(BaseModel):
    empresa_id: int
    sku: Optional[str] = None
    nome: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    cor: Optional[str] = None
    tamanho: Optional[str] = None
    preco: float
    estoque_atual: int
    imagem_mime_type: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    # O frontend ou ETL envia a imagem como string Base64
    imagem_base64: Optional[str] = None

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    cor: Optional[str] = None
    tamanho: Optional[str] = None
    preco: Optional[float] = None
    estoque_atual: Optional[int] = None
    imagem_base64: Optional[str] = None
    imagem_mime_type: Optional[str] = None
    is_ativo: Optional[bool] = None

class ProdutoResponse(ProdutoBase):
    id: int
    is_ativo: bool
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    # Retornamos como base64 para o frontend conseguir exibir direto no <img src="data:image/...">
    imagem_base64: Optional[str] = None 

    class Config:
        from_attributes = True