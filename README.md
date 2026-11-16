# Cognita AI

> Conhecimento conectado. Inteligência aplicada.

Plataforma de processamento documental, RAG e experimentação com LLMs.

## Estrutura

```
cognita-ai/
├── backend/            # Python + FastAPI (pipeline RAG, provedores de IA)
├── frontend/           # Next.js + React + TypeScript + Tailwind
├── docs/               # Arquitetura, roadmap e diário de aprendizado
├── scripts/            # Scripts auxiliares
└── docker-compose.yml  # Postgres + pgvector local (alternativa ao Supabase)
```

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- Docker (opcional, para banco local) **ou** um projeto no Supabase

## Rodando em desenvolvimento

### 1. Banco de dados (opcional, local)

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"
copy .env.example .env          # preencha as chaves
alembic upgrade head            # cria/atualiza as tabelas
uvicorn app.main:app --reload
```

API em http://localhost:8000 — documentação interativa em http://localhost:8000/docs.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface em http://localhost:3000.

### Testes

```bash
cd backend && pytest
cd frontend && npm run lint && npm run build
```

## Roadmap

Veja [docs/roadmap.md](docs/roadmap.md). Status atual: **Etapa 3 — Processamento e embeddings** concluída.
