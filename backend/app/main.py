from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import (
    auth,
    admin_interno,
    empresas,
    usuarios,
    produtos,
    chat
)

# Cria as tabelas no banco de dados na inicialização
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart ChatLoja API",
    description="API para o vendedor inteligente de moda e calçados",
    version="1.0.0"
)

# ==========================================
# CONFIGURAÇÃO DE CORS
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://localhost",
        "https://smartchatloja.com.br",
        "https://www.smartchatloja.com.br"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# INCLUSÃO DE ROTAS (ROUTERS)
# ==========================================
app.include_router(auth.router)
app.include_router(admin_interno.router)
app.include_router(empresas.router)
app.include_router(usuarios.router)
app.include_router(produtos.router)
app.include_router(chat.router)

# ==========================================
# ENDPOINTS BASE
# ==========================================
@app.get("/", tags=["Status"])
def read_root():
    return {
        "message": "Smart ChatLoja API - Servidor funcionando"
    }

@app.get("/api/health", tags=["Status"])
def health_check():
    return {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0"
    }

@app.get("/api/test", tags=["Status"])
def test_endpoint():
    return {
        "message": "Conexão com backend estabelecida com sucesso"
    }