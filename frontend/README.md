# ReviewPilot — Frontend

React 18 frontend for the ReviewPilot AI code review agent. Submits GitHub PR URLs, polls for async review completion, and displays structured results with severity-tagged issues, a scored gauge, and a benchmark comparison panel.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 18 (Create React App) |
| Styling | Custom CSS (CSS variables, dark theme) |
| HTTP Client | Axios |
| Fonts | Syne + DM Mono (Google Fonts) |

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ReviewForm.jsx       # PR URL input + benchmark toggle
│   │   ├── ScoreGauge.jsx       # SVG arc gauge (0–10,000)
│   │   ├── IssueList.jsx        # Severity-sorted issue cards
│   │   └── BenchmarkPanel.jsx   # Agent vs baseline comparison bars
│   ├── services/
│   │   └── api.js               # Axios calls + polling logic
│   ├── App.jsx                  # Root layout, state, polling orchestration
│   └── App.css                  # Global styles and design tokens
├── .env                         # REACT_APP_API_URL (never commit)
└── package.json
```

---

## Prerequisites

- Node.js 18+
- npm
- ReviewPilot backend running on `http://localhost:8000`
- Celery worker running
- Redis running via Docker

---

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment

Create a `.env` file in the `frontend/` directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

Note: React (Create React App) uses `REACT_APP_` prefix for environment variables

### 3. Start the dev server

```bash
npm start
```

App runs at `http://localhost:3000`.

---

## How Polling Works

ReviewPilot reviews are processed asynchronously in the background. The frontend handles this with a polling loop:

```
POST /reviews/
  → returns { id, status: "pending" } instantly

pollReview() starts — calls GET /reviews/{id} every 3 seconds
  → status: pending   (queued, waiting for worker)
  → status: processing (diff fetching + LLM running)
  → status: completed  (results ready → stop polling)
  → status: failed     (something went wrong → show error)

Timeout: 60 attempts × 3s = 3 minutes max wait
```

The `pollReview` function in `api.js` returns a cleanup function stored in a `useRef` — this ensures polling stops cleanly if the component unmounts or the user submits a new review before the previous one completes.

---

## Components

### `ReviewForm`
- Accepts a GitHub PR URL (`https://github.com/owner/repo/pull/123`)
- Client-side URL validation before submission
- Optional benchmark comparison toggle
- Enter key support
- Disabled during active review

### `ScoreGauge`
- SVG arc gauge rendering the 0–10,000 score
- Color-coded: green (≥80%), amber (≥50%), red (<50%)
- Smooth fill transition on result load
- Shows score label (Excellent / Good / Fair / Needs Work)

### `IssueList`
- Issues sorted by severity: critical → major → minor → info
- Each card shows: severity dot, category badge, file path, line number, description, suggestion
- Color-coded severity indicators
- Empty state for clean diffs

### `BenchmarkPanel`
- Shown only when `include_benchmark` was checked
- Side-by-side bar comparison: ReviewPilot Agent vs Vanilla Claude
- Score difference with +/- indicator
- Explains the scoring methodology difference inline

---

## Design System

- Dark theme — deep navy/slate palette (`#0b0e14` base)
- Typography — Syne (display) + DM Mono (code/labels)
- Accent — `#4f8aff` blue
- Severity colors: critical red, major orange, minor amber, info blue
- Animations — fade-up on results, spinner on loading, gauge fill transition
- Fully responsive down to 375px

---

## Available Scripts

```bash
npm start      # Start development server (http://localhost:3000)
npm run build  # Production build
npm test       # Run tests
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `REACT_APP_API_URL` | Base URL of the FastAPI backend |

All environment variables in Create React App must be prefixed with `REACT_APP_` to be accessible in the browser.