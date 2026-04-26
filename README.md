# ReviewPilot

> AI-native code review agent — submit a GitHub PR URL, get a structured review with scored findings, severity-tagged issues, and a benchmark comparison against vanilla Claude.


---

## What It Does

ReviewPilot takes a GitHub Pull Request URL and:

1. Fetches the raw diff via the GitHub API
2. Runs a structured LLM review using Groq.
3. Extracts issues tagged by severity (`critical`, `major`, `minor`, `info`) and category (`correctness`, `security`, `maintainability`, `test_coverage`, `documentation`)
4. Calculates a **category-weighted score from 0 to 10,000**
5. Optionally benchmarks against a simulated vanilla Claude baseline
6. Processes reviews asynchronously via Celery + Redis — no hanging requests

---

## Why This Agent Exists

Vanilla LLMs can review code — but they return freeform prose with no structure, no scoring, and no consistency. ReviewPilot solves that:

| | Vanilla Claude/Cursor | ReviewPilot Agent |
|---|---|---|
| Output format | Freeform text | Structured JSON → typed UI |
| Severity tagging | None | Critical / Major / Minor / Info |
| Scoring | None | 0–10,000 category-weighted |
| Category awareness | None | 5 categories with weighted pools |
| GitHub integration | None | Fetches diff directly from PR URL |
| Consistency | Varies per prompt | Same rubric every run |
| Authentication | None | JWT-based user auth |
| Rate limiting | None | 10 requests/hour per IP |
| Async processing | None | Celery + Redis background queue |

---

## Scoring System

The agent scores each review from **0 to 10,000** using a category-weighted model:

| Category | Max Points | What It Covers |
|---|---|---|
| Correctness | 4,000 | Logic bugs, wrong behavior, edge cases |
| Security | 2,000 | Injections, exposed secrets, auth flaws |
| Maintainability | 2,000 | Readability, naming, complexity |
| Test Coverage | 1,000 | Missing tests, untested paths |
| Documentation | 1,000 | Missing docstrings, unclear comments |

Issues deduct from their category pool by severity:

| Severity | Deduction |
|---|---|
| Critical | 100% of category max |
| Major | 40% |
| Minor | 13% |
| Info | 0% |

Each category is independently capped — one bad category cannot collapse the full score.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Axios |
| Styling | Custom CSS — dark theme, Syne + DM Mono fonts |
| Backend | FastAPI (async Python) |
| Database | PostgreSQL + SQLAlchemy (async) + asyncpg |
| Task Queue | Celery + Redis |
| LLM | Groq  |
| GitHub | GitHub REST API v3 (httpx) |
| Auth | JWT via python-jose + passlib |
| Config | pydantic-settings |

---

## Project Structure

```
reviewpilot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entrypoint, lifespan, CORS
│   │   ├── config.py                # Env settings
│   │   ├── db.py                    # Async DB engine + session
│   │   ├── worker.py                # Celery app definition
│   │   ├── tasks.py                 # Background review task
│   │   ├── middleware/
│   │   │   └── rate_limit.py        # slowapi limiter
│   │   ├── models/
│   │   │   ├── review.py            # Review, Issue, BenchmarkRun
│   │   │   └── user.py              # User model
│   │   ├── schemas/
│   │   │   ├── review.py            # Review schemas
│   │   │   └── user.py              # User + Token schemas
│   │   ├── routers/
│   │   │   ├── review.py            # Review routes
│   │   │   └── auth.py              # Auth routes
│   │   └── services/
│   │       ├── github.py            # Diff fetcher
│   │       ├── llm.py               # LLM review pipeline
│   │       ├── scorer.py            # Scoring engine
│   │       ├── review.py            # Orchestration service
│   │       └── auth.py              # JWT + password service
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ReviewForm.jsx
│   │   │   ├── ScoreGauge.jsx
│   │   │   ├── IssueList.jsx
│   │   │   └── BenchmarkPanel.jsx
│   │   ├── services/
│   │   │   └── api.js               # Axios + polling logic
│   │   ├── App.jsx
│   │   └── App.css
│   ├── .env
│   └── package.json
├── .cursorrules
├── BENCHMARK.md
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local or remote)
- Docker (for Redis)
- Groq API key → https://console.groq.com
- GitHub Fine-grained Personal Access Token

---

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

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

Start Redis via Docker:

```bash
docker run -d --name reviewpilot-redis -p 6379:6379 redis:alpine
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Start the Celery worker (new terminal):

```bash
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

On first run, the lifespan handler automatically creates the database and all tables.

---

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Create `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

App runs at `http://localhost:3000`.

---

### Running All Services

You need three terminals:

```bash
# Terminal 1 — FastAPI
uvicorn app.main:app --reload

# Terminal 2 — Celery worker
celery -A app.worker.celery_app worker --loglevel=info --pool=solo

# Terminal 3 — Redis (if not already running)
docker start reviewpilot-redis
```

---

## GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Click **Generate new token → Fine-grained token**
3. Set **Repository access** → All repositories
4. Under **Permissions → Repository permissions**:
   - Pull requests → Read-only
   - Contents → Read-only
5. Generate, copy, paste into `backend/.env` as `GITHUB_TOKEN`

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, receive JWT token |
| GET | `/auth/me` | Get current user info |

### Reviews

| Method | Endpoint | Description |
|---|---|---|
| POST | `/reviews/` | Submit a PR for review (rate limited: 10/hour) |
| GET | `/reviews/{id}` | Poll review status and fetch results |

### Async Review Flow

```
POST /reviews/     → returns { id, status: "pending" } instantly
GET  /reviews/{id} → poll every 3s until status = "completed"
```

Full Swagger docs at `http://localhost:8000/docs`.

---

## Cursor Configuration

This project is Cursor-ready. The `.cursorrules` file at the root defines stack conventions, naming rules, service patterns, and the full scoring system reference. Open the project root in Cursor and the rules apply automatically.

---

## Performance Metrics

Scoring methodology and benchmark results are documented in [`BENCHMARK.md`](./BENCHMARK.md).

---

## Quest Checklist

- [x] Agent code (FastAPI + Groq + GitHub API)
- [x] Cursor-configured (`.cursorrules`)
- [x] JWT Authentication
- [x] Rate limiting (10/hour per IP)
- [x] Async background processing (Celery + Redis)
- [x] Performance metrics and calculation method
- [x] Comparison with default Cursor/Claude baseline
- [x] Problem specialization explanation
- [x] Comprehensive documentation
- [x] All sensitive information removed (`.env` gitignored)

---
