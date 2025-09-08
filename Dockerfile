##SentinelaApolo/Dockerfile
FROM python:3.12

# Cria diretório de trabalho
WORKDIR /app

# Variáveis para otimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema (para compilar NumPy/Pandas/psycopg2/etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto
COPY . /app/

# Expor porta usada pelo Gunicorn
EXPOSE 8000

# Permissão de execução no script de entrada
RUN chmod +x /app/entrypoint.prod.sh

# Comando padrão do contêiner
CMD ["/app/entrypoint.prod.sh"]
