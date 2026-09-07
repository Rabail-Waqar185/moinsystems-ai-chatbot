# MoinSystems AI — Public Website Chatbot (Backend)

RAG-based support chatbot backend: FastAPI + PostgreSQL/pgvector + an
OpenAI/Claude provider adapter. This README covers **Day 1** setup —
skeleton, DB connection, health check. It will be extended each
milestone day.

## Status: Day 1 of 8 (Foundation & Environment)

Done: repo skeleton, typed settings, DB connection + pooling, initial
schema migration (6 tables + pgvector extension + ivfflat index),
`/api/v1/health`, tests, `.env.example`.

Not yet done (later days): ingestion pipeline, retriever, chat
orchestration/LLM adapter, lead capture, email, React widget, Render
deployment.

## Prerequisites

- Python 3.11+ (pinned via `.python-version`)
- PostgreSQL 14+ with the `pgvector` extension available (locally via
  Docker is easiest, or use `postgresql-16` + `postgresql-16-pgvector`
  on Linux, or Postgres.app on Mac — pgvector ships as an extension you
  `CREATE EXTENSION`, not a separate service)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env template and fill in real values
cp .env.example .env      # Windows: copy .env.example .env
# then edit .env: at minimum set DATABASE_URL and APP_SECRET

# 4. Create the database (if it doesn't exist yet)
# e.g. with local postgres: createdb moin_ai_chatbot

# 5. Run migrations (creates pgvector extension + all tables)
alembic upgrade head

# 6. Run the app
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/v1/health` — should return
`{"status": "ok", "app": "up", "database": "up"}`.
API docs (non-production only): `http://localhost:8000/docs`.

## Running tests

```bash
pytest
```

`tests/unit/test_health.py` mocks the DB check so it runs without a
live database. Later days add `tests/integration`, `tests/rag`,
`tests/api` which will need a real (or test) Postgres instance.

## Environment variables

See `.env.example` for the full list with comments. Required now:
`DATABASE_URL`, `APP_SECRET`. Everything else has a sane default or is
only required once its milestone day is implemented (LLM keys on Day
4, SMTP on Day 6, etc).

## Folder structure

```
app/
  main.py              FastAPI app instance, CORS, routers
  api/v1/              versioned route handlers (health done; sessions,
                       chat, leads, feedback come in later days)
  core/                config.py (typed settings), logging.py (structured
                       JSON logs), security.py (added Day 6)
  db/                  session.py (engine/pooling), models.py (ORM models),
                       migrations/ (Alembic)
  rag/                 ingestion, embeddings, retriever, filters, prompts
                       (Day 2-3)
  llm/                 provider adapter — base + openai/claude (Day 4)
  chat/                orchestrator, intent routing, state machine (Day 4-5)
  leads/               lead service + validation (Day 5)
  email/               email service + templates (Day 6)
  schemas/             Pydantic request/response models
data/                  knowledge base JSONL goes here
tests/                 unit / integration / rag / api
widget/                React + TypeScript chat widget (Day 7)
scripts/               ingest.py, evaluate_rag.py
```

## Migrations

New migration after changing `app/db/models.py`:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

`0001_initial_schema.py` is hand-written (no live DB was available to
autogenerate against) — review it against your actual Postgres/pgvector
version before running in a new environment.

## Notes / decisions

- Embedding dimension defaults to 1536 (`text-embedding-3-small`).
  If you switch embedding models with a different dimension, update
  `EMBEDDING_DIMENSIONS` in `.env` **and** the `EMBEDDING_DIM` constant
  in the `0001_initial_schema.py` migration before running it — the
  vector column width is fixed at creation time.
- `ivfflat` index uses `lists = 100` as a starting point; this should
  be re-tuned once the real dataset is loaded (Day 2) based on row
  count.
