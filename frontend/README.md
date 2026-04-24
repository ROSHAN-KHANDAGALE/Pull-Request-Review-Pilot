# ReviewPilot — Frontend

React-based UI for the ReviewPilot AI code review agent. Submits GitHub PR URLs, displays structured review results with severity-tagged issues, a scored gauge, and a benchmark comparison panel.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 18 |
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
│   │   └── api.js               # Axios calls to FastAPI backend
│   ├── App.jsx                  # Root layout and state management
│   └── App.css                  # Global styles and design tokens
├── .env                         # REACT_APP_API_URL (never commit)
└── package.json
```

---

## Prerequisites

- Node.js 18+
- npm or yarn
- ReviewPilot backend running on `http://localhost:8000`

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

### 3. Run the dev server

```bash
npm run dev
```

App runs at `http://localhost:5173`.

---

## Components

### `ReviewForm`
- Accepts a GitHub PR URL (`https://github.com/owner/repo/pull/123`)
- Client-side URL validation before submission
- Optional benchmark toggle
- Enter key support

### `ScoreGauge`
- SVG arc gauge rendering the 0–10,000 score
- Color-coded: green (≥80%), amber (≥50%), red (<50%)
- Animated fill transition on result load

### `IssueList`
- Issues sorted by severity: critical → major → minor → info
- Each card shows severity, category, file path, line number, description, and suggestion
- Color-coded severity dots

### `BenchmarkPanel`
- Shown only when `include_benchmark` was checked
- Side-by-side bar comparison: ReviewPilot Agent vs Vanilla Claude
- Displays score difference with +/- indicator
- Explains the scoring methodology difference

---

## Design

- **Dark theme** — deep navy/slate palette (`#0b0e14` base)
- **Typography** — Syne (display) + DM Mono (code/labels)
- **Accent** — `#4f8aff` blue
- **Animations** — fade-up on results, spinner on loading, gauge fill transition
- Fully responsive down to 375px

---

## Available Scripts

```bash
npm run dev       # Start development server
npm run build     # Production build
npm run preview   # Preview production build locally
```