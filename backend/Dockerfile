# Usa uma imagem oficial do Python estável e leve
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências do Python 
# (Nota: psycopg2-binary já vem compilado, então não precisamos de gcc ou libpq-dev)
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do backend para o container
COPY . .

# Expõe a porta que o FastAPI utilizará
EXPOSE 8000

# O comando base (será sobrescrito pelo docker-compose com --reload em desenvolvimento)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]