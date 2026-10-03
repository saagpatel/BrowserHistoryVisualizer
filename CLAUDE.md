# Browser History Visualizer (BHV)

Local personal analytics web app — reads Chrome, Atlas, and Comet SQLite history databases, renders 5 interactive visualizations: GitHub-style heatmap, topic donut chart, rabbit hole node graph, domain ranking, and hourly productivity curve. History analysis stays local with no telemetry; optional AI categorization sends domain names to the Anthropic API.

## Stack

- Python 3.12 (CI), FastAPI 0.141.1 (API-only), uvicorn 0.54.0 bound to 127.0.0.1:8000
- pandas 3.0.6 — vectorized visit normalization; anthropic 1.3.0 — optional batch categorization, cached on disk
- React + TypeScript 19 / 5.x (hooks-only), Vite 8.x (dev proxy to :8000; prod build to `frontend/dist/`)
- Recharts 3.x (3 charts; heatmap uses custom SVG), D3 7.x (rabbit hole force-directed graph only)
- nginx (Homebrew): serves `frontend/dist/` on 127.0.0.1:8080, reverse-proxies `/api/` to :8000
- launchd: 3 agents — `com.bhv.server`, `com.bhv.nginx`, `com.bhv.pipeline` (daily 6am)

## Project Structure

- Backend: `backend/` — FastAPI app, `config.py` owns session, duration-cap, rabbit-hole and AI-batch constants
- Frontend: `frontend/`
- nginx config template: `nginx/bhv.conf`
- launchd plists: `launchd/`
- Architecture and implementation plan: `IMPLEMENTATION-ROADMAP.md` (contains stale implementation details)

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
- snake_case Python filenames, PascalCase React component filenames, camelCase hook filenames
- All thresholds (session gap, duration cap, rabbit hole minimums) live in `backend/config.py` only — no hardcoding elsewhere
- Unit tests for all data transform functions before marking a phase complete

## Gotchas

- **uvicorn binding**: always 127.0.0.1:8000, never 0.0.0.0 — privacy constraint
- **CORSMiddleware**: omit it; nginx owns the single origin
- **StaticFiles in FastAPI**: omit it; nginx serves `frontend/dist/` directly
- **Browser SQLite files**: read-only + copy-on-lock only — never modify source files
- **Claude API calls**: `POST /api/categorize` batches cached uncategorized entries; results persist in `backend/data/categories.json`. The startup pipeline uses static/cache categorization only; newly seen unknown domains are not added to that cache
- **Vite in production**: run `make build` then serve via nginx; Vite dev server is development only

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Serving model | nginx :8080 → FastAPI :8000 | Single origin, no CORS, nginx owns static files |
| FastAPI role | API-only, no StaticFiles mount | nginx is faster for static; cleaner separation |
| Browser detection | Glob + Chromium schema validation | Catches Chrome/Atlas/Comet + future forks |
| Category AI | User cache → static allowlist → AI cache → uncategorized; explicit API batch | AI endpoint processes cached uncategorized entries; retries are possible |
| Duration inference | Gap-to-next capped at 1200s, flagged as estimated | Handles idle/sleep; honest about approximation |
| Session gap | Gap > 900s starts a new session | Standard UX research convention |
| Rabbit hole minimums | 4 visits, 600s, 2 unique domains | Filters noise; all in config.py |
| launchd pipeline | Daily 6am + manual /api/refresh | Both scheduled and on-demand |

<!-- portfolio-context:start -->
# Portfolio Context

## What This Project Is

A local personal analytics web app that reads Chrome, Atlas, and Comet SQLite history
databases and renders 5 interactive visualizations: GitHub-style heatmap, topic donut
chart, rabbit hole node graph, domain ranking, and hourly productivity curve. History analysis
stays local with no telemetry; optional AI categorization sends domain names to the Anthropic API.

## Current State

**Phase 3: Rabbit Holes + AI Categorization + launchd + Polish** (implemented with gaps: saved browser overrides are not consumed by the pipeline; new unknown domains are not cached for AI classification; AI classification does not recompute analytics)
See IMPLEMENTATION-ROADMAP.md → Phase 3 for tasks and acceptance criteria.

## Stack

- Python: 3.12 (CI)
- FastAPI: 0.141.1 — async REST API, API-only (no static file serving)
- uvicorn: 0.54.0 — ASGI server, bound to 127.0.0.1:8000
- pandas: 3.0.6 — vectorized visit normalization and analytics
- anthropic: 1.3.0 — optional batch domain categorization, cached on disk
- React + TypeScript: 19 / 5.x — hooks-only frontend
- Vite: 8.x — dev server (proxy to :8000) + production build to frontend/dist/
- Recharts: 3.x — 3 of 5 charts; heatmap uses custom SVG
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
- Claude API calls run through `POST /api/categorize`, not on launch; results persist in `backend/data/categories.json`, but analytics are not recomputed by that endpoint
- Do not run Vite dev server in production — `make build` → nginx serves the static dist/
- Do not add features not in the current phase of IMPLEMENTATION-ROADMAP.md

## Next Recommended Move

Use this context plus the README and supporting docs to resume the next active task, then promote the repo beyond minimum-viable by capturing a dedicated handoff, roadmap, or discovery artifact.

<!-- portfolio-context:end -->
