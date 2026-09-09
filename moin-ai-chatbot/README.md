# MoinSystems AI Chatbot

A production-style RAG (Retrieval-Augmented Generation) chatbot with a FastAPI backend and an embeddable React widget — built to answer questions about a company's services, qualify leads through a guided conversation, and notify a sales team by email when a real lead is captured.

**Live demo:** https://moinsystems-ai-chatbot-three.vercel.app
**API:** https://moinsystems-ai-chatbot-m5js.onrender.com/api/v1/health

> Hosted on free infrastructure tiers (Render, Supabase, Vercel), so the backend may take 30–60 seconds to wake up on the first request if it's been idle.

---

## What it does

- Answers natural-language questions about a business's services, pricing approach, and process using semantic retrieval over a curated knowledge base — not a generic LLM guess.
- Detects when a conversation signals real purchase intent and smoothly transitions into a structured lead-capture flow, collecting name, email, and project details through the chat itself rather than a separate form.
- Sends an email notification to the business the moment a lead is captured, with full conversation context.
- Ships as a single embeddable widget script that can be dropped into any website (WordPress, static HTML, etc.) via a small config object — no iframe, no page reload.

## Architecture

**Backend — FastAPI (Python)**
- **LLM & embeddings:** Google Gemini (`gemini-flash-lite-latest` for chat, `gemini-embedding-001` for retrieval embeddings, 768 dimensions)
- **Vector store:** PostgreSQL with the `pgvector` extension (hosted on Supabase)
- **ORM / migrations:** SQLAlchemy + Alembic
- **Retrieval:** top-k semantic search with a similarity threshold, evaluated against a held-out set of test queries (75% top-3 / 84% top-5 retrieval accuracy across 32 evaluation queries and 97 knowledge chunks)
- **Lead capture:** a small conversation state machine tracks progress through name → email → project details, persisted per session so users can pick up mid-flow
- **Email delivery:** provider-agnostic email layer (SMTP or Resend's HTTP API) selected via config, so it can run on hosts that block outbound SMTP ports without any code changes
- **Reliability:** rate limiting (SlowAPI), request size limits, structured JSON logging with request-id tracing, CORS locked to known origins

**Widget — React + TypeScript + Vite**
- Compiles to a single predictably-named JS/CSS bundle for easy embedding
- Talks to the backend via a small typed API client with graceful handling of network errors, rate limits, and validation failures
- Session continuity via local storage, so a user can close and reopen the widget without losing their conversation

**Infrastructure**
- Backend: [Render](https://render.com) (free web service)
- Database: [Supabase](https://supabase.com) (managed Postgres + pgvector)
- Widget: [Vercel](https://vercel.com) (static hosting)
- Uptime: a scheduled health-check ping ([cron-job.org](https://cron-job.org)) keeps the free-tier backend and database from idling out

## Project structure

```
moin-ai-chatbot/          FastAPI backend
├── app/
│   ├── api/v1/           HTTP route handlers (chat, lead capture, sessions, health)
│   ├── chat/             Intent detection, lead-capture logic, conversation service
│   ├── rag/              Embeddings, ingestion, retrieval, prompt construction
│   ├── llm/              LLM provider abstraction (Gemini implementation)
│   ├── email/            Email provider abstraction (SMTP + Resend implementations)
│   ├── db/               Models, session management, Alembic migrations
│   ├── core/             Settings, logging, rate limiting
│   └── schemas/          Pydantic request/response models
├── scripts/              Dataset conversion, RAG ingestion, retrieval evaluation
└── tests/                Unit tests

widget/                   React + TypeScript embeddable chat widget
├── src/
│   ├── api/              Typed backend client
│   ├── components/       Chat panel, message list, lead form, launcher button
│   ├── hooks/            Widget state management
│   └── __tests__/        Component tests
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (for the widget)
- PostgreSQL 14+ with the `pgvector` extension available (Docker is the easiest local route, or `postgresql-16` + `postgresql-16-pgvector` on Linux, or Postgres.app on Mac — pgvector is a `CREATE EXTENSION`, not a separate service)

## Getting started — backend

```bash
cd moin-ai-chatbot

# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env template and fill in real values
cp .env.example .env            # Windows: copy .env.example .env
# at minimum set: DATABASE_URL, APP_SECRET, GEMINI_API_KEY

# 4. Create the database (if it doesn't exist yet)
createdb moin_ai_chatbot

# 5. Run migrations — creates the pgvector extension and all tables
alembic upgrade head

# 6. Load the knowledge base with real embeddings
python scripts/ingest_rag.py data/raw/moinsystems_rag_dataset_v2.jsonl

# 7. Run the app
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/v1/health` — should return `{"status": "ok", "app": "up", "database": "up"}`.
Interactive API docs (non-production only): `http://localhost:8000/docs`.

## Getting started — widget

```bash
cd widget
npm install
npm run dev
```

The dev harness (`index.html`) simulates an embedding page and points the widget at `http://localhost:8000/api/v1` by default — update the `window.MoinChatWidgetConfig` block there if your backend runs elsewhere.

## Environment variables

See `.env.example` for the full list with comments. Required: `DATABASE_URL`, `APP_SECRET`, `GEMINI_API_KEY`. Everything else (rate limits, similarity threshold, email provider choice, etc.) has a working default.

## Testing

```bash
# Backend
cd moin-ai-chatbot && pytest

# Widget
cd widget && npm run test
```

Retrieval quality can be re-evaluated at any time with:
```bash
python scripts/evaluate_retrieval.py
```

## Migrations

After changing `app/db/models.py`:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

`0001_initial_schema.py` is hand-written rather than autogenerated — review it against your actual Postgres/pgvector version before running it in a new environment.

## Embedding the widget on a real site

The built widget reads its backend URL from a global config object set by the embedding page, before the widget script loads:

```html
<script>
  window.MoinChatWidgetConfig = { apiBaseUrl: "https://your-backend-url/api/v1" };
</script>
<script type="module" src="/moin-chat-widget.js"></script>
```

This keeps the built bundle environment-agnostic — the same file works in development, staging, or production depending on what the host page sets.

## Design notes

- Embeddings use Gemini's `gemini-embedding-001` at 768 dimensions. Switching embedding models with a different dimension requires updating both `EMBEDDING_DIMENSIONS` in `.env` and the vector column width in `0001_initial_schema.py` — it's fixed at creation time, not adjustable after the fact.
- The `ivfflat` index uses `lists = 100` as a starting point; this should be re-tuned based on real row counts as the knowledge base grows.

## Notes on the deployment stack

This project intentionally uses only free-tier infrastructure to demonstrate that a full RAG application — vector database, LLM integration, transactional email, and a live frontend — can be built and deployed end-to-end at zero cost. That comes with a couple of honest tradeoffs, handled explicitly rather than hidden: the backend cold-starts after 15 minutes of inactivity, and outbound email uses an HTTP-based provider (Resend) instead of SMTP, since most free hosting tiers block SMTP ports outright to prevent abuse.
