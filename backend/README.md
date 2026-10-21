# ReviewPilot — Backend

AI-assisted code review API built with FastAPI, PostgreSQL, and Groq. It accepts a GitHub PR URL, fetches the diff, runs a structured LLM review, and returns a scored report with categorized findings. Reviews run directly through the API by default in the documented local setup; Celery and Redis are optional.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy (async) + asyncpg |
| Task Queue | Optional Celery + Redis |
| LLM | Groq Chat Completions (model configured with `MODEL_NAME`) |
| GitHub Integration | GitHub REST API v3 (httpx) |
| Authentication | JWT via python-jose + passlib bcrypt |
| Rate Limiting | slowapi (configurable; 10 review submissions/hour by default) |
| Config | pydantic-settings |
| Server | Uvicorn |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # App entrypoint, lifespan, CORS, rate limit handler
│   ├── config.py            # Environment settings via pydantic-settings
│   ├── db.py                # Async engine, session, Base
│   ├── worker.py            # Celery app definition
│   ├── task.py              # Background review task (asyncio event-loop wrapper)
│   ├── middleware/
│   │   └── rate_limit.py    # slowapi Limiter instance
│   ├── models/
│   │   ├── review.py        # Review, Issue, BenchmarkRun ORM models
│   │   └── user.py          # User ORM model
│   ├── schemas/
│   │   ├── review.py        # ReviewCreate, ReviewOut, IssueOut, BenchmarkOut
│   │   └── user.py          # UserCreate, UserOut, TokenOut
│   ├── routers/
│   │   ├── review.py        # POST /reviews/, GET /reviews/{id}
│   │   └── auth.py          # POST /auth/register, /auth/login, GET /auth/me
│   └── services/
│       ├── github.py        # GitHub diff fetcher
│       ├── llm.py           # Groq LLM analysis + diff size validation
│       ├── scorer.py        # Category-weighted scoring engine
│       ├── review.py        # Full review orchestration + run_analysis_only
│       └── auth.py          # Password hashing, JWT creation, user validation
├── .env                     # Environment variables (never commit)
└── requirements.txt
```

---

## Prerequisites

- Python 3.12
- PostgreSQL running locally or remote
- Docker (for Redis, only when Celery is enabled)
- Groq API key → https://console.groq.com
- GitHub Fine-grained Personal Access Token

---

## Setup

### 1. Create virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the `backend/` directory. The settings below select
direct processing and disable rate limiting for local development:

```env
DATABASE_URL=postgresql+asyncpg://yourusername:yourpassword@localhost:5432/reviewpilot
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=github_pat_your_token
ALLOWED_ORIGINS=["http://localhost:3000"]
MODEL_NAME=your_groq_chat_model_id
SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0
USE_CELERY=false
ENABLE_RATE_LIMITING=false
```

Set `USE_CELERY=true` and provide `REDIS_URL` to make queued reviews available.
When `USE_CELERY=false`, reviews are processed directly by the API and Redis is
not required. The UI's worker switch is available only when the backend enables
Celery. `ENABLE_RATE_LIMITING` independently controls the review submission
limit of 10 requests per hour and defaults to `true`. Disabling it is intended
for local development, not an internet-facing deployment. These settings are
read at startup; restart the API after changing them.

`MODEL_NAME` (or the legacy `DEFAULT_MODEL`) must identify a Groq model that
supports Chat Completions and JSON output. If both variables are set,
`MODEL_NAME` takes precedence. Prompt Guard models, including
`meta-llama/llama-prompt-guard-2-22m`, perform moderation/classification and
cannot generate review findings. Select a currently available Groq chat model.

### 4. Start Redis (only when using Celery)

```bash
docker run -d --name reviewpilot-redis -p 6379:6379 redis:alpine
```

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

On first startup the lifespan handler automatically creates the database and all tables.

### 6. Start the Celery worker (only when using Celery, new terminal)

```bash
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

`--pool=solo` is required on Windows for asyncio compatibility.

When `USE_CELERY=true`, the UI offers a choice between direct and queued
processing. With `USE_CELERY=false`, reviews use direct processing. The UI
displays the rate-limiting state reported by the backend; that setting is
configured server-side with `ENABLE_RATE_LIMITING`.

On startup you should see:

```
[tasks]
  . run_review_task
```

---

## How It Works

### Async Review Pipeline

```
POST /reviews/ (queued mode)
      ↓
Create Review record (status: pending) → queue task to Redis via Celery
      ↓
Celery worker picks up task
      ↓
GitHubService.fetch_diff() → raw diff text
      ↓
LLMService.analyze_diff() → structured JSON issues
      ↓
ScorerService.calculate_total_score() → 0–10,000
      ↓
Persist issues + benchmark → status: completed
      ↓
Frontend polls GET /reviews/{id} → shows results
```

In direct mode, the API runs the same review service synchronously and returns
the completed result without using Celery or Redis.

`GET /reviews/options` returns whether queue processing and rate limiting are
enabled, allowing the frontend to reflect the backend configuration. The
client cannot enable or disable rate limiting.

### Authentication Flow

```
POST /auth/register → hash password → store user → return UserOut
POST /auth/login    → verify password → create JWT → return TokenOut
GET  /auth/me       → decode JWT → return current user
```

---

## API Endpoints

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | None | Register new user |
| POST | `/auth/login` | None | Login, receive JWT |
| GET | `/auth/me` | Bearer token | Get current user |

### Reviews

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/reviews/` | None | Submit PR for review |
| GET | `/reviews/{id}` | None | Poll status / fetch results |
| GET | `/reviews/options` | None | Read queue availability and rate-limit state |

---

## Scoring System

Category-weighted model from 0 to 10,000:

| Category | Max Points |
|---|---|
| Correctness | 4,000 |
| Security | 2,000 |
| Maintainability | 2,000 |
| Test Coverage | 1,000 |
| Documentation | 1,000 |

Severity multipliers per category pool:

| Severity | Multiplier |
|---|---|
| Critical | 100% |
| Major | 40% |
| Minor | 13% |
| Info | 0% |

Each category pools independently — one bad category cannot collapse the full score. Full methodology in `BENCHMARK.md`.

---

## GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (Fine-grained)**
3. Repository access → All repositories
4. Permissions → Pull requests: Read-only, Contents: Read-only
5. Paste into `.env` as `GITHUB_TOKEN`

---

## Interactive Docs

Visit `http://localhost:8000/docs` after starting the server.

## Troubleshooting

- **Queued submission returns 503:** confirm Redis is reachable at `REDIS_URL`
  and that a Celery worker is running. Direct processing does not use either.
- **Review reports an unsupported Prompt Guard model:** set `MODEL_NAME` to a
  Groq chat-completions model that supports JSON output, then restart the API
  and worker.
- **Rate limit returns 429:** review submissions are limited to 10 per hour
  by default. For local testing, set `ENABLE_RATE_LIMITING=false` and restart
  the API.