# Base image otimizada para Python
FROM python:3.12-slim

# Variáveis de ambiente estruturais
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalação das dependências nativas (C++) críticas para gerar o PDF via WeasyPrint no Linux
# O Hugging Face roda sob Debian/Ubuntu
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Definindo o diretório principal do container
WORKDIR /app

# Instalar dependências Python (aproveitando o cache de layer do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Importar o código do servidor Python (backend) para dentro do container
COPY . .

# Comando obrigatório do Hugging Face Spaces: Rodar o ASGI Uvicorn na porta 7860
EXPOSE 7860
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
