# EFD Compliance — Guia de Setup

## Pré-requisitos

- **Python 3.12+** instalado
- **Node.js 18+** e npm (para o frontend)
- **Git**

---

## 1. Clonar o repositório

```bash
git clone https://github.com/jacksonsantosjr/EFD-Compliance.git
cd EFD-Compliance
```

## 2. Backend — Instalar dependências Python

> ⚠️ **Nota:** A instalação via `pip` não foi possível na máquina corporativa devido a bloqueio de rede (firewall/proxy corporativo cortando conexões SSL com o PyPI). Execute os comandos abaixo de uma rede sem restrições.

```bash
# Criar ambiente virtual (se ainda não existir)
python -m venv venv

# Ativar o venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Pacotes que precisam ser instalados:

| Pacote | Versão | Finalidade |
|---|---|---|
| `fastapi` | ≥0.115 | Framework da API REST |
| `uvicorn[standard]` | ≥0.34 | Servidor ASGI |
| `python-multipart` | ≥0.0.18 | Upload de arquivos |
| `pydantic` | ≥2.10 | Validação de dados / schemas |
| `python-docx` | ≥1.1 | Geração de relatórios DOCX |
| `weasyprint` | ≥63.0 | Geração de relatórios PDF |
| `supabase` | ≥2.11 | Persistência em nuvem (configurar posteriormente) |
| `aiosqlite` | ≥0.20 | SQLite async (fallback local) |
| `python-dotenv` | ≥1.0 | Variáveis de ambiente |
| `pytest` | ≥8.3 | Testes unitários |
| `pytest-asyncio` | ≥0.24 | Testes async |
| `httpx` | ≥0.28 | Client HTTP para testes |

## 3. Verificar instalação do backend

```bash
# Subir o servidor
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Testar health check (em outro terminal)
curl http://localhost:8000/health
# Resposta esperada: {"status":"healthy","app":"EFD Compliance","version":"1.0.0"}
```

## 4. Frontend — Instalar dependências Node

```bash
cd frontend
npm install
npm run dev
# Acesse http://localhost:5173
```

## 5. Configurar variáveis de ambiente

Copie o arquivo `.env` e configure conforme necessário:

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=http://localhost:5173

# Supabase (configurar quando disponível)
SUPABASE_URL=
SUPABASE_KEY=

# Limites
MAX_FILE_SIZE_MB=500
```

## 6. Base de Conhecimento

A pasta `knowledge_base/` deve conter as tabelas e legislações necessárias.
Os arquivos da base de conhecimento estão em `Base de Conhecimento/` (pasta externa ao projeto).

Para copiar para dentro do projeto:
```bash
# Tabelas 5.1.1 (todas as UFs)
copy "Base de Conhecimento\Tabela 5.1.1*" knowledge_base\tabelas_511\

# CFOP e NCM
copy "Base de Conhecimento\Tabela de CFOP.txt" knowledge_base\
copy "Base de Conhecimento\Tabela_NCM_Vigente*.json" knowledge_base\
copy "Base de Conhecimento\Tabela 4.2.1*" knowledge_base\
```

---

## Estrutura do Projeto

```
efd-compliance/
├── api/                    # FastAPI (backend)
│   ├── main.py             # Entry point
│   ├── config.py           # Configurações
│   ├── models/             # Pydantic schemas
│   └── routes/             # Endpoints REST
├── parser/                 # Engine de parsing SPED
│   ├── sped_parser.py      # Parser principal
│   ├── layout_versions/    # Mapeamento por versão do layout
│   └── blocos/             # Parser de cada bloco
├── validators/             # Engine de validação
│   ├── math_validator.py   # Validações matemáticas
│   ├── cross_block_validator.py
│   └── uf_rules/           # Regras por UF
├── knowledge_base/         # Tabelas e legislação
├── reports/                # Geração de dossiê DOCX/PDF
├── database/               # Persistência (Supabase + SQLite)
├── frontend/               # React + Vite (dashboard)
└── tests/                  # Testes unitários e integração
```
