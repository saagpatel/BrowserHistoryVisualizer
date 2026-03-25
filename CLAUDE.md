# Browser History Visualizer (BHV)

## Overview
A local personal analytics web app that reads Chrome, Atlas, and Comet SQLite history
databases and renders 5 interactive visualizations: GitHub-style heatmap, topic donut
chart, rabbit hole node graph, domain ranking, and hourly productivity curve. All data
stays on 127.0.0.1 — no cloud services, no telemetry, no external requests.

## Tech Stack
- Python: 3.11+
- FastAPI: 0.110+ — async REST API, API-only (no static file serving)
- uvicorn: 0.29+ — ASGI server, bound to 127.0.0.1:8000
- pandas: 2.x — vectorized visit normalization and analytics
- anthropic: 0.25+ — batch domain categorization, cached permanently
- React + TypeScript: 18 / 5.x — hooks-only frontend
- Vite: 5.x — dev server (proxy to :8000) + production build to frontend/dist/
- Recharts: 2.x — 4 of 5 charts
- D3: 7.x — rabbit hole force-directed graph only
- nginx (Homebrew): serves frontend/dist/ on 127.0.0.1:8080, reverse-proxies /api/ to :8000
- launchd: 3 agents — com.bhv.server, com.bhv.nginx, com.bhv.pipeline (daily 6am)

## Project Structure
See IMPLEMENTATION-ROADMAP.md for full file tree.
Working directory for backend: `backend/`
Working directory for frontend: `frontend/`
nginx config template: `nginx/bhv.conf`
launchd plists: `launchd/`

## Development Conventions
- TypeScript strict mode — zero `any` types
- Python type hints on all function signatures
- kebab-case filenames, PascalCase React components
- All thresholds (session gap, duration cap, rabbit hole minimums) live in `backend/config.py` only
- Unit tests for all data transform functions before marking a phase complete
- `make dev` for development (Vite :5173 + uvicorn :8000 with --reload)
- `make install` for production (nginx :8080 + launchd services)

## Current Phase
**Phase 3: Rabbit Holes + AI Categorization + launchd + Polish** (complete)
See IMPLEMENTATION-ROADMAP.md → Phase 3 for tasks and acceptance criteria.

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

## Do NOT
- Do not bind uvicorn to 0.0.0.0 — always 127.0.0.1:8000
- Do not add CORSMiddleware to FastAPI — nginx handles the single origin
- Do not mount StaticFiles in FastAPI — nginx serves frontend/dist/ directly
- Do not hardcode any threshold (session gap, duration cap, visit minimums) outside config.py
- Do not modify browser SQLite files — read-only + copy-on-lock only
- Do not call the Claude API on every app launch — categorization is a one-time batch, results cached in categories.json
- Do not run Vite dev server in production — `make build` → nginx serves the static dist/
- Do not add features not in the current phase of IMPLEMENTATION-ROADMAP.md
