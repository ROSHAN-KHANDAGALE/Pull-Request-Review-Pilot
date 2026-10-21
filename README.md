# ReviewPilot

ReviewPilot reviews GitHub pull requests and presents structured, severity-tagged findings with a category-weighted score. It includes a React interface and can process reviews directly through the API or use an optional Celery and Redis queue.

**GitHub About description:** AI-assisted GitHub pull request reviews with scored findings and optional background processing.

---

## Contents

- [What it does](#what-it-does)
- [Scoring system](#scoring-system)
- [Technology](#tech-stack)
- [Getting started](#getting-started)
- [API reference](#api-reference)
- [Contributing and community standards](#contributing-and-community-standards)
- [License](#license)

## What It Does

ReviewPilot takes a GitHub Pull Request URL and:

1. Fetches the raw diff via the GitHub API
2. Runs a structured LLM review using a Groq chat-completions model.
3. Extracts issues tagged by severity (`critical`, `major`, `minor`, `info`) and category (`correctness`, `security`, `maintainability`, `test_coverage`, `documentation`)
4. Calculates a **category-weighted score from 0 to 10,000**
5. Optionally benchmarks against a simulated vanilla Claude baseline
6. Processes reviews directly through the API or asynchronously with Celery and Redis

---

## Why This Agent Exists

ReviewPilot is designed to make review results easier to scan and compare:

| | Vanilla Claude/Cursor | ReviewPilot Agent |
|---|---|---|
| Output format | Freeform text | Structured JSON → typed UI |
| Severity tagging | Varies | Critical / Major / Minor / Info |
| Scoring | Varies | 0–10,000 category-weighted |
| Category awareness | Varies | 5 categories with weighted pools |
| GitHub integration | None | Fetches diff directly from PR URL |
| Consistency | Varies per prompt | Same rubric every run |
| Authentication | Varies | JWT-based user auth |
| Rate limiting | Varies | Configurable; 10 requests/hour per IP by default |
| Background processing | Varies | Optional Celery + Redis queue |

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
| Frontend | React 19 + Axios |
| Styling | Custom CSS — dark theme, Syne + DM Mono fonts |
| Backend | FastAPI (async Python) |
| Database | PostgreSQL + SQLAlchemy (async) + asyncpg |
| Task Queue | Optional Celery + Redis |
| LLM | Groq Chat Completions |
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
│   │   ├── task.py                  # Background review task
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
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── .cursorrules
├── BENCHMARK.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (local or remote)
- Redis only when using queued reviews (Docker is one way to run Redis)
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
MODEL_NAME=your_groq_chat_model_id
SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0
USE_CELERY=false
ENABLE_RATE_LIMITING=false
```

For local testing without Redis, leave `USE_CELERY=false`; reviews run directly
through the API. `ENABLE_RATE_LIMITING` independently controls the API's
10-submissions-per-hour limit and defaults to `true`. Disabling it is intended
for local development. These settings are loaded at startup, so restart the
backend after changing them.

To use the queue, set `USE_CELERY=true`, configure `REDIS_URL`, and run Redis
plus a Celery worker. The UI will offer a direct-versus-queued processing
choice when queueing is enabled. On Windows, start the worker with `--pool=solo`.

`MODEL_NAME` must be a Groq chat-completions model that supports JSON output.
Prompt Guard models, including `meta-llama/llama-prompt-guard-2-22m`, are for
moderation and cannot generate code-review results. `DEFAULT_MODEL` is accepted
as a legacy alternative; `MODEL_NAME` takes precedence.

Start Redis only when using Celery. For example:

```bash
docker run -d --name reviewpilot-redis -p 6379:6379 redis:alpine
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Start a Celery worker in another terminal when queueing is enabled:

```bash
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

On first run, the lifespan handler automatically creates the database and all tables.

---

### Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

Start the frontend with `npm start`; it runs at `http://localhost:3000`.

---

### Running All Services

For direct local processing, start PostgreSQL, the backend, and the frontend;
Redis and Celery are not required. For queued processing, start Redis and the
worker too.

```bash
# From the backend directory
uvicorn app.main:app --reload

# In another backend terminal, only when USE_CELERY=true
celery -A app.worker.celery_app worker --loglevel=info --pool=solo

# From the frontend directory
npm start
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
| POST | `/reviews/` | Submit a PR for direct or queued review |
| GET | `/reviews/{id}` | Poll review status and fetch results |
| GET | `/reviews/options` | Read queue availability and rate-limit state |

Rate limiting is configured on the backend, not in the browser. The UI displays
its state but cannot disable it. Queue selection is available only when
`USE_CELERY=true`.

### Review Flow

```
Direct: POST /reviews/ → returns the completed review
Queued: POST /reviews/ → returns { id, status: "pending" }
        GET /reviews/{id} → poll until status = "completed" or "failed"
```

Full Swagger docs at `http://localhost:8000/docs`.

### Common setup issues

- If a queued review cannot be submitted, check that Redis is reachable at
  `REDIS_URL` and that a Celery worker is running. Direct mode does not need
  either service.
- If the API reports that Prompt Guard cannot generate reviews, set
  `MODEL_NAME` to a supported Groq chat-completions model and restart the API.

---

## Cursor Configuration

This project is Cursor-ready. The `.cursorrules` file at the root defines stack conventions, naming rules, service patterns, and the full scoring system reference. Open the project root in Cursor and the rules apply automatically.

---

## Performance Metrics

Scoring methodology and benchmark results are documented in [`BENCHMARK.md`](./BENCHMARK.md).

---

## Contributing and Community Standards

Contributions and clear bug reports are welcome. Please read the project
guidelines before opening an issue or pull request:

- [Contributing guide](./CONTRIBUTING.md)
- [Code of conduct](./CODE_OF_CONDUCT.md)
- [Security policy](./SECURITY.md)
- [Bug report and feature request templates](./.github/ISSUE_TEMPLATE/)
- [Pull request template](./.github/PULL_REQUEST_TEMPLATE.md)

## License

This repository does not currently include a license. No license to use,
modify, or redistribute this code is granted. Please contact the repository
owner if you need permission.
