# -*- coding: utf-8 -*-
"""
Configurações da aplicação EFD Compliance.
Carrega variáveis de ambiente e define constantes globais.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Diretórios — BASE_DIR aponta para a raiz do projeto (efd-compliance/)
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_OUTPUT_DIR = BASE_DIR / "reports" / "output"

# Criar diretórios de saída se não existirem
UPLOADS_DIR.mkdir(exist_ok=True)
REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_CORS_ORIGINS = os.getenv("API_CORS_ORIGINS", "http://localhost:5173").split(",")

# Supabase (configuração posterior)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "sped-uploads")

# SQLite fallback
SQLITE_DB_PATH = BASE_DIR / "database" / "efd_compliance.db"

# Limites
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# SPED Layout versions suportados
SUPPORTED_LAYOUT_VERSIONS = [
    "001",  # v1.0.x (2009)
    "002",  # v2.0.x (2010)
    "003",  # v3.0.x (2011-2012)
    "004",  # v3.0.1 (2012)
    "005",  # v3.0.2 (2013)
    "006",  # v3.0.3 (2013)
    "007",  # v3.0.4 (2014)
    "008",  # v3.0.5 (2015)
    "009",  # v3.0.6 (2016)
    "010",  # v3.0.7 (2016)
    "011",  # v3.0.8 (2017)
    "012",  # v3.0.9 (2017)
    "013",  # v3.1.0 (2018)
    "014",  # v3.1.1 (2019)
    "015",  # v3.1.2 (2020)
    "016",  # v3.1.3 (2021)
    "017",  # v3.1.4 (2022)
    "018",  # v3.1.5 (2023)
    "019",  # v3.2.0 (2024)
    "020",  # v3.2.1 (2025)
    "021",  # v3.2.2 (2026)
]

# UFs do Brasil
UFS_BRASIL = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
]

# UFs sem Tabela 5.1.1 publicada
UFS_SEM_TABELA_511 = ["RR"]

# App metadata
APP_NAME = "EFD Compliance"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Validador Expert de SPED EFD ICMS/IPI — Análise pós-PVA com cruzamento entre blocos, validação de legislação e geração de dossiê técnico."
