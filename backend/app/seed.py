import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos corretamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, AdminInterno
from passlib.context import CryptContext

# Configuração do Bcrypt (mesma que usaremos no login)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_database():
    # 1. Cria as tabelas se não existirem
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas do banco de dados verificadas/criadas.")

    # 2. Cria o admin inicial
    db = SessionLocal()
    try:
        email_inicial = "contato@smartchatloja.com.br"
        admin_existente = db.query(AdminInterno).filter(AdminInterno.email == email_inicial).first()

        if not admin_existente:
            senha_hash = pwd_context.hash("5587Çlagosta@10")
            
            novo_admin = AdminInterno(
                nome="Administrador Principal",
                email=email_inicial,
                senha_hash=senha_hash,
                is_ativo=True
            )
            db.add(novo_admin)
            db.commit()
            print("🎉 Administrador inicial criado com sucesso!")
            print(f"   Email: {email_inicial}")
            print("   Senha: 5587Çlagosta@10")
        else:
            print("ℹ️ Administrador inicial já existe no banco de dados.")
            
    except Exception as e:
        print(f"❌ Erro ao criar seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()