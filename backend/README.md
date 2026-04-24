# ReviewPilot — Backend

AI-native code review API built with FastAPI, PostgreSQL, and Groq. Accepts a GitHub PR URL, fetches the diff, runs a structured LLM review, and returns a scored report with categorized issues.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy (async) + asyncpg |
| LLM | Groq — `llama-3.3-70b-versatile` |
| GitHub Integration | GitHub REST API v3 (httpx) |
| Config | pydantic-settings |
| Server | Uvicorn |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # App entrypoint, lifespan, CORS
│   ├── config.py            # Environment settings via pydantic-settings
│   ├── db.py                # Async engine, session, Base
│   ├── models/
│   │   └── review.py        # Review, Issue, BenchmarkRun ORM models
│   ├── schemas/
│   │   └── review.py        # Pydantic request/response schemas
│   ├── routers/
│   │   └── review.py        # POST /reviews/, GET /reviews/{id}
│   └── services/
│       ├── github.py        # GitHub diff fetcher
│       ├── llm.py           # Groq LLM analysis
│       ├── scorer.py        # Category-weighted scoring engine
│       └── review.py        # Orchestrates the full review pipeline
├── .env                     # Environment variables (never commit)
└── requirements.txt
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL running locally (or remote)
- Groq API key → https://console.groq.com
- GitHub Fine-grained Personal Access Token

---

## Setup

### 1. Clone and create virtual environment

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
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/reviewpilot
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=github_pat_your_token
ALLOWED_ORIGINS=["http://localhost:3000"]
MODEL_NAME=model_name
```

### 4. GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (Fine-grained)**
3. Set **Repository access** → All repositories
4. Under **Permissions → Repository permissions** set:
   - Pull requests → Read-only
   - Contents → Read-only
5. Generate and copy the token into `.env`

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

On first startup, the lifespan handler automatically:
- Creates the `reviewpilot` database if it doesn't exist
- Creates all tables via SQLAlchemy metadata

No manual pgAdmin setup required.

---

## API Endpoints

### `POST /reviews/`

Submit a GitHub PR for review.

**Request body:**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "include_benchmark": false
}
```

**Response:** Full `ReviewOut` object with issues, score, and optional benchmark.

---

### `GET /reviews/{review_id}`

Fetch a previously completed review by UUID.

---

## Scoring System

The agent uses a **category-weighted scoring model** from 0 to 10,000:

| Category | Max Points |
|---|---|
| Correctness | 4,000 |
| Security | 2,000 |
| Maintainability | 2,000 |
| Test Coverage | 1,000 |
| Documentation | 1,000 |

Issues deduct points proportionally by severity:

| Severity | Multiplier |
|---|---|
| Critical | 100% of category max |
| Major | 40% |
| Minor | 13% |
| Info | 0% |

Each category is capped independently — a single bad category cannot tank the entire score.

### Benchmark Comparison

When `include_benchmark: true`, the API also calculates a **baseline score** simulating vanilla Claude/Cursor behavior — flat severity deductions with no category awareness. This demonstrates the agent's structured advantage.

---

## Interactive Docs

Visit `http://localhost:8000/docs` for the Swagger UI after starting the server.