from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart ChatLoja API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Configurações do Banco de Dados
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "smartchat"
    POSTGRES_PASSWORD: str = "smartchat123"
    POSTGRES_DB: str = "smartchat_db"
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:5432/{POSTGRES_DB}"
    
    # Configurações de Segurança (JWT)
    SECRET_KEY: str = "sua_chave_secreta_super_segura_mude_isso_em_producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()