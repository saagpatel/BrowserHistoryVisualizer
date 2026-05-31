# Browser History Visualizer (BHV)

Local personal analytics web app — reads Chrome, Atlas, and Comet SQLite history databases, renders 5 interactive visualizations: GitHub-style heatmap, topic donut chart, rabbit hole node graph, domain ranking, and hourly productivity curve. All data stays on 127.0.0.1 — no cloud services, no telemetry, no external requests.

## Stack

- Python 3.11+, FastAPI 0.110+ (API-only), uvicorn 0.29+ bound to 127.0.0.1:8000
- pandas 2.x — vectorized visit normalization; anthropic 0.25+ — batch categorization, cached permanently
- React + TypeScript 19 / 5.x (hooks-only), Vite 8.x (dev proxy to :8000; prod build to `frontend/dist/`)
- Recharts 3.x (4 charts), D3 7.x (rabbit hole force-directed graph only)
- nginx (Homebrew): serves `frontend/dist/` on 127.0.0.1:8080, reverse-proxies `/api/` to :8000
- launchd: 3 agents — `com.bhv.server`, `com.bhv.nginx`, `com.bhv.pipeline` (daily 6am)

## Project Structure

- Backend: `backend/` — FastAPI app, `config.py` owns all thresholds
- Frontend: `frontend/`
- nginx config template: `nginx/bhv.conf`
- launchd plists: `launchd/`
- Full file tree: `IMPLEMENTATION-ROADMAP.md`

## Build / Test / Run

```bash
make dev          # Vite :5173 + uvicorn :8000 --reload (development)
make install      # nginx :8080 + launchd services (production)
make build        # Vite prod build → frontend/dist/

# Manual dev start:
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload
cd frontend && npm run dev
# Open http://localhost:5173
```

## Conventions

- TypeScript strict mode; Python type hints on all function signatures
- kebab-case filenames, PascalCase React components
- All thresholds (session gap, duration cap, rabbit hole minimums) live in `backend/config.py` only — no hardcoding elsewhere
- Unit tests for all data transform functions before marking a phase complete

## Gotchas

- **uvicorn binding**: always 127.0.0.1:8000, never 0.0.0.0 — privacy constraint
- **CORSMiddleware**: omit it; nginx owns the single origin
- **StaticFiles in FastAPI**: omit it; nginx serves `frontend/dist/` directly
- **Browser SQLite files**: read-only + copy-on-lock only — never modify source files
- **Claude API calls**: categorization is a one-time batch; results cached in `categories.json` — call only when new domains appear, never on every launch
- **Vite in production**: run `make build` then serve via nginx; Vite dev server is development only

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Serving model | nginx :8080 → FastAPI :8000 | Single origin, no CORS, nginx owns static files |
| FastAPI role | API-only, no StaticFiles mount | nginx is faster for static; cleaner separation |
| Browser detection | Glob + Chromium schema validation | Catches Chrome/Atlas/Comet + future forks |
| Category AI | Hybrid: static allowlist → Claude API batch → cached | Never re-classifies same domain twice |
| Duration inference | Gap-to-next capped at 1200s, flagged as estimated | Handles idle/sleep; honest about approximation |
| Session gap | 900s = new session | Standard UX research convention |
| Rabbit hole minimums | 4 visits, 600s, 2 unique domains | Filters noise; all in config.py |
| launchd pipeline | Daily 6am + manual /api/refresh | Both scheduled and on-demand |

<!-- portfolio-context:start -->
# Portfolio Context

## What This Project Is

A local personal analytics web app that reads Chrome, Atlas, and Comet SQLite history
databases and renders 5 interactive visualizations: GitHub-style heatmap, topic donut
chart, rabbit hole node graph, domain ranking, and hourly productivity curve. All data
stays on 127.0.0.1 — no cloud services, no telemetry, no external requests.

## Current State

**Phase 3: Rabbit Holes + AI Categorization + launchd + Polish** (complete)
See IMPLEMENTATION-ROADMAP.md → Phase 3 for tasks and acceptance criteria.

## Stack

- Python: 3.11+
- FastAPI: 0.110+ — async REST API, API-only (no static file serving)
- uvicorn: 0.29+ — ASGI server, bound to 127.0.0.1:8000
- pandas: 2.x — vectorized visit normalization and analytics
- anthropic: 0.25+ — batch domain categorization, cached permanently
- React + TypeScript: 19 / 5.x — hooks-only frontend
- Vite: 8.x — dev server (proxy to :8000) + production build to frontend/dist/
- Recharts: 3.x — 4 of 5 charts
- D3: 7.x — rabbit hole force-directed graph only
- nginx (Homebrew): serves frontend/dist/ on 127.0.0.1:8080, reverse-proxies /api/ to :8000
- launchd: 3 agents — com.bhv.server, com.bhv.nginx, com.bhv.pipeline (daily 6am)

## How To Run

```bash
# Start both services together (recommended)
make dev
# Open http://localhost:5173

# Or start manually:
# Backend
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# Frontend (separate terminal)
cd frontend && npm run dev
# Open http://localhost:5173
```

## Known Risks

- Do not bind uvicorn to 0.0.0.0 — always 127.0.0.1:8000
- Do not add CORSMiddleware to FastAPI — nginx handles the single origin
- Do not mount StaticFiles in FastAPI — nginx serves frontend/dist/ directly
- Do not hardcode any threshold (session gap, duration cap, visit minimums) outside config.py
- Do not modify browser SQLite files — read-only + copy-on-lock only
- Do not call the Claude API on every app launch — categorization is a one-time batch, results cached in categories.json
- Do not run Vite dev server in production — `make build` → nginx serves the static dist/
- Do not add features not in the current phase of IMPLEMENTATION-ROADMAP.md

## Next Recommended Move

Use this context plus the README and supporting docs to resume the next active task, then promote the repo beyond minimum-viable by capturing a dedicated handoff, roadmap, or discovery artifact.

<!-- portfolio-context:end -->
