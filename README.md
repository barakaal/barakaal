# AI Dropship Company OS

An AI-powered operating system for running a fully automated dropshipping company, orchestrating a hierarchy of AI agents across 12 departments.

---

## Vision

AI Dropship Company OS replaces a traditional e-commerce operations team with a structured hierarchy of AI agents. A CEO agent directs 8 department managers (Research, Sourcing, Marketing, Orders, Finance, Customer Support, Legal, Data), who in turn delegate to specialist employee agents. Every financially significant decision requires explicit human approval — the system is a decision-support engine, not an autonomous spender.

---

## Architecture

```
                         +------------------+
                         |   Next.js 14 UI  |  :3000
                         |  (Dashboard/UX)  |
                         +--------+---------+
                                  |  REST / JSON
                         +--------v---------+
                         |  FastAPI Backend  |  :8000
                         |  (API + AI Logic) |
                         +--+----------+----+
                            |          |
               +------------+          +------------+
               |                                    |
    +----------v----------+            +------------v-----------+
    |  PostgreSQL 16       |            |  Redis 7               |
    |  (Primary DB)        |            |  (Cache + Celery MQ)   |
    +---------------------+            +------------------------+
                                                   |
                                    +--------------+--------------+
                                    |                             |
                          +---------v--------+       +-----------v-------+
                          |  Celery Worker   |       |  Celery Beat      |
                          |  (Async tasks)   |       |  (Scheduler/CRON) |
                          +------------------+       +-------------------+

Agent Hierarchy:
  CEO Agent
  ├── Product Research Manager  →  [Amazon Analyst, AliExpress Analyst]
  ├── Sourcing Manager
  ├── Market Analysis Manager   →  [TikTok Analyst, Google Trends Analyst]
  ├── Marketing Manager
  ├── Order Manager             →  [Fraud Detector]
  ├── Finance Manager
  ├── Customer Support Manager
  └── Legal/Compliance Manager  →  [Product Writer]
```

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend API | Python 3.11, FastAPI 0.110          |
| Database    | PostgreSQL 16, SQLAlchemy 2 (async) |
| Migrations  | Alembic                             |
| Cache / MQ  | Redis 7                             |
| Task Queue  | Celery 5.3                          |
| AI Engine   | Anthropic Claude / OpenAI (pluggable)|
| Frontend    | Next.js 14, TypeScript, Tailwind CSS |
| Containers  | Docker, Docker Compose              |

---

## Project Structure

```
barakaal/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py               # Async Alembic configuration
│   │   ├── script.py.mako
│   │   └── versions/            # Migration files
│   ├── app/
│   │   ├── api/v1/              # REST API routers
│   │   │   ├── router.py        # Main router aggregator
│   │   │   ├── auth.py
│   │   │   ├── agents.py
│   │   │   ├── products.py
│   │   │   ├── suppliers.py
│   │   │   ├── orders.py
│   │   │   ├── campaigns.py
│   │   │   ├── finance.py
│   │   │   ├── approvals.py
│   │   │   ├── dashboard.py
│   │   │   └── ...
│   │   ├── agents/              # AI agent implementations
│   │   │   ├── base.py
│   │   │   ├── ceo_agent.py
│   │   │   ├── managers/
│   │   │   └── employees/
│   │   ├── connectors/          # Marketplace API connectors
│   │   │   ├── base.py
│   │   │   ├── amazon.py
│   │   │   ├── aliexpress.py
│   │   │   ├── ebay.py
│   │   │   ├── tiktok.py
│   │   │   ├── google_trends.py
│   │   │   └── csv_import.py
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic settings
│   │   │   ├── database.py      # Async SQLAlchemy engine
│   │   │   ├── deps.py          # FastAPI dependencies
│   │   │   └── security.py      # JWT / bcrypt
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── product_scoring.py  # 12-criteria scoring engine
│   │   ├── tasks/               # Celery tasks
│   │   └── workflows/           # Weekly orchestration workflow
│   ├── scripts/
│   │   └── seed.py              # DB seeder with demo data
│   └── tests/
│       ├── conftest.py
│       ├── test_health.py
│       └── test_auth.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── app/                 # Next.js 14 App Router
│       ├── components/
│       └── lib/
│           ├── api.ts
│           ├── auth.ts
│           └── utils.ts
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/) v2+
- **OR** for manual install:
  - Python 3.11+
  - Node.js 20+
  - PostgreSQL 16
  - Redis 7

---

## Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/your-org/ai-dropship-os.git
cd ai-dropship-os

# 2. Configure environment
cp .env.example .env
# Edit .env and add your API keys (at minimum ANTHROPIC_API_KEY and SECRET_KEY)

# 3. Start all services
docker-compose up -d

# 4. Seed the database with demo data
docker-compose exec backend python scripts/seed.py

# 5. Access the application
# Dashboard:    http://localhost:3000
# API Docs:     http://localhost:8000/docs
# ReDoc:        http://localhost:8000/redoc
```

---

## Manual Installation

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env: set DATABASE_URL, REDIS_URL, SECRET_KEY, ANTHROPIC_API_KEY

# Run database migrations
alembic upgrade head

# Seed demo data
python scripts/seed.py

# Start the development server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Celery Workers (background tasks)

Open two separate terminals in the `backend/` directory with the venv activated:

```bash
# Terminal 1 — task worker
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2

# Terminal 2 — scheduler (weekly workflow CRON)
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Configuring AI Agents

The system supports two AI providers. Configure in `.env`:

```bash
# Use Anthropic Claude (recommended)
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...

# OR use OpenAI
AI_PROVIDER=openai
AI_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

If no API key is provided, all agent actions use **mock mode** — the system still runs but returns simulated AI responses. This is useful for local development and testing.

---

## Marketplace Connectors

All connectors fall back to **mock mode** automatically when API credentials are absent.

| Connector        | Platform         | Env Vars Required                              | Mock Available |
|------------------|------------------|------------------------------------------------|----------------|
| Amazon PA-API    | AMAZON           | `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG` | Yes |
| AliExpress DS    | ALIEXPRESS       | `ALIEXPRESS_APP_KEY`, `ALIEXPRESS_APP_SECRET`  | Yes |
| eBay Browse API  | EBAY             | `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`         | Yes |
| TikTok Business  | TIKTOK           | `TIKTOK_APP_ID`, `TIKTOK_APP_SECRET`           | Yes |
| Google Trends    | GOOGLE_TRENDS    | None (uses pytrends, public)                   | Yes |
| CSV Import       | CSV_IMPORT       | None                                           | N/A |

---

## Security Model

The system is designed with a **human-in-the-loop** philosophy:

```
HUMAN_APPROVAL_REQUIRED=true   # All financial decisions require human sign-off
MAX_AUTO_SPEND_USD=0.0         # Zero autonomous spending by default
```

When an agent proposes a decision with financial impact (launching a product, creating an ad campaign, issuing a refund), it creates an `AgentDecision` record with `status=PENDING_APPROVAL`. The human operator reviews and approves or rejects via the dashboard or the `/api/v1/approvals` endpoint.

Only after explicit approval does the system execute the action.

---

## Weekly Workflow

The CEO agent orchestrates an 11-step weekly cycle, triggered every Monday at 09:00 (configurable via `WEEKLY_WORKFLOW_CRON`):

1. **Trend Collection** — All market analysts pull fresh data from connectors
2. **Product Scoring** — Each candidate scored on 12 weighted criteria (0–100)
3. **Sourcing** — Sourcing manager identifies best suppliers and calculates margins
4. **Legal Review** — Compliance manager flags any product/supplier risks
5. **Pricing** — Finance manager sets optimal prices targeting 60%+ gross margin
6. **Content Creation** — Product writer generates SEO-optimised listings
7. **Marketing Strategy** — Marketing manager proposes campaign budgets (pending approval)
8. **Order Processing** — Order manager reviews pending orders, fraud scores
9. **Financial Report** — Finance manager generates weekly P&L summary
10. **Customer Support Review** — Support manager flags unresolved tickets
11. **CEO Weekly Report** — Consolidated strategic summary + next-week priorities

---

## Default Credentials

| Field    | Value                    |
|----------|--------------------------|
| Email    | admin@dropship-os.com    |
| Password | Admin123!                |

> **Warning:** Change these credentials immediately before any public or production deployment. Set a strong `SECRET_KEY` (minimum 32 random characters) in your `.env` file.

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
```

The test suite uses SQLite in-memory so no external database is required for tests.

---

## Disclaimer

This system is a decision-support tool. All AI agent outputs are recommendations — final decisions on product launches, supplier selection, advertising spend, and any other business actions remain the sole responsibility of the human operator. The authors accept no liability for business outcomes arising from use of this software.
