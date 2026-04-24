# ReviewPilot

> AI-native code review agent — submit a GitHub PR URL, get a structured review with scored findings, severity-tagged issues, and a benchmark comparison against vanilla Claude.

Built as a quest submission for the **FDE/APO AI-Native Talent Recruitment** by MUST Company.

---

## What It Does

ReviewPilot takes a GitHub Pull Request URL and:

1. Fetches the raw diff via the GitHub API
2. Runs a structured LLM review using Groq (`llama-3.3-70b-versatile`)
3. Extracts issues tagged by severity (`critical`, `major`, `minor`, `info`) and category (`correctness`, `security`, `maintainability`, `test_coverage`, `documentation`)
4. Calculates a **category-weighted score from 0 to 10,000**
5. Optionally benchmarks against a simulated vanilla Claude baseline to demonstrate the agent's structured advantage

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
| Critical | 100% of category max per issue |
| Major | 40% |
| Minor | 13% |
| Info | 0% |

Each category is independently capped — one bad category cannot collapse the full score. This is the key structural advantage over the flat-deduction baseline.

### Benchmark Comparison

When benchmark mode is enabled, the API also computes a **baseline score** using flat severity deductions (no category awareness) — simulating how a vanilla Claude response would score under the same rubric. The UI shows both side-by-side.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Axios |
| Styling | Custom CSS — dark theme, Syne + DM Mono fonts |
| Backend | FastAPI (async Python) |
| Database | PostgreSQL + SQLAlchemy (async) + asyncpg |
| LLM | Groq — `llama-3.3-70b-versatile` |
| GitHub | GitHub REST API v3 (httpx) |
| Config | pydantic-settings |

---

## Project Structure

```
reviewpilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entrypoint, lifespan, CORS
│   │   ├── config.py            # Env settings
│   │   ├── db.py                # Async DB engine + session
│   │   ├── models/review.py     # ORM models: Review, Issue, BenchmarkRun
│   │   ├── schemas/review.py    # Pydantic schemas
│   │   ├── routers/review.py    # API routes
│   │   └── services/
│   │       ├── github.py        # Diff fetcher
│   │       ├── llm.py           # LLM review pipeline
│   │       ├── scorer.py        # Scoring engine
│   │       └── review.py        # Orchestration service
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ReviewForm.jsx
│   │   │   ├── ScoreGauge.jsx
│   │   │   ├── IssueList.jsx
│   │   │   └── BenchmarkPanel.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx
│   │   └── App.css
│   ├── .env
│   └── package.json
├── .cursorrules
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local or remote)
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
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/reviewpilot
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=github_pat_your_token
ALLOWED_ORIGINS=["http://localhost:5173"]
MODEL_NAME=llama-3.3-70b-versatile
```

Start the server:

```bash
uvicorn app.main:app --reload
```

On first run, the lifespan handler automatically creates the database and all tables. No pgAdmin setup needed.

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

Start the dev server:

```bash
npm run dev
```

App runs at `http://localhost:3000`.

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

## Cursor Configuration

This project is Cursor-ready. The `.cursorrules` file at the root defines:

- Stack conventions (FastAPI async patterns, SQLAlchemy async, React hooks)
- File naming and structure rules
- Service layer patterns
- Pydantic schema conventions

Open the project root in Cursor and the rules apply automatically.

---

## API Reference

### `POST /reviews/`

```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "include_benchmark": false
}
```

### `GET /reviews/{review_id}`

Returns a previously completed review by UUID.

Full Swagger docs available at `http://localhost:8000/docs`.

---

## Performance Metrics

Scoring methodology and benchmark results are documented in [`BENCHMARK.md`](./BENCHMARK.md).

---

## Quest Submission Checklist

- [x] Agent code (FastAPI + Groq + GitHub API)
- [x] Cursor-configured (`.cursorrules`)
- [x] Performance metrics and calculation method
- [x] Comparison with default Cursor/Claude baseline
- [x] Problem specialization explanation
- [x] Comprehensive documentation
- [x] All sensitive information removed (`.env` gitignored)

---
