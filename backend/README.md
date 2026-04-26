# ReviewPilot — Backend

AI-native code review API built with FastAPI, PostgreSQL, Groq, and Celery. Accepts a GitHub PR URL, fetches the diff, runs a structured async LLM review, and returns a scored report with categorized issues.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy (async) + asyncpg |
| Task Queue | Celery + Redis |
| LLM | Groq — `llama-3.3-70b-versatile` |
| GitHub Integration | GitHub REST API v3 (httpx) |
| Authentication | JWT via python-jose + passlib bcrypt |
| Rate Limiting | slowapi (10 requests/hour per IP) |
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
│   ├── tasks.py             # Background review task (asyncio.run wrapper)
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
- Docker (for Redis)
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

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://yourusername:yourpassword@localhost:5432/reviewpilot
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=github_pat_your_token
ALLOWED_ORIGINS=["http://localhost:3000"]
MODEL_NAME=your_model_name
SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0
```

### 4. Start Redis

```bash
docker run -d --name reviewpilot-redis -p 6379:6379 redis:alpine
```

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

On first startup the lifespan handler automatically creates the database and all tables.

### 6. Start the Celery worker (new terminal)

```bash
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

`--pool=solo` is required on Windows for asyncio compatibility.

On startup you should see:

```
[tasks]
  . run_review_task
```

---

## How It Works

### Async Review Pipeline

```
POST /reviews/
      ↓
Create Review record (status: pending) → return instantly
      ↓
Queue task to Redis via Celery .delay()
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