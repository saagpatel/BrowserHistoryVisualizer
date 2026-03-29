# BrowserHistoryVisualizer

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey?logo=apple)](https://www.apple.com/macos/)

Local browser history analytics — no cloud, no tracking. BHV reads your Chromium-family browser history files directly, runs an analysis pipeline, and serves a React dashboard showing how you actually spend your time online.

## Features

- **Multi-browser detection** — auto-discovers Chrome, Arc, Brave, Edge, Vivaldi, Opera, and any other Chromium-based browser installed under `~/Library/Application Support`
- **GitHub-style activity heatmap** — visits per day with 5-level intensity buckets across your full history
- **Category breakdown** — domain visits and estimated minutes per topic category (static allowlist + optional AI classification via Claude)
- **Top domains** — ranked by visit count with category and estimated time
- **Hourly productivity chart** — focus vs. distraction minutes for each hour of the day
- **Rabbit hole detection** — identifies browsing sessions that span multiple domains over an extended period
- **Date range filtering** — scope the heatmap and rabbit-hole views to any date window
- **On-demand refresh** — re-run the pipeline without restarting the server
- **launchd integration** — optional background service that runs the pipeline daily at 6 AM and keeps the API and nginx proxy alive

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, pandas, uvicorn |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, Recharts, D3 |
| Proxy | nginx (Homebrew) |
| Service management | macOS launchd |
| AI categorization | Anthropic Claude API (optional) |

## Prerequisites

- macOS (launchd + `~/Library/Application Support` paths are macOS-specific)
- Python 3.11+
- Node.js 18+
- [Homebrew](https://brew.sh/) (used to install nginx if not present)

## Getting Started

### Development (no nginx, hot reload)

```bash
# 1. Create the Python virtual environment and install all dependencies
make check-deps

# 2. Start backend (uvicorn --reload on :8000) + frontend (Vite on :5173)
make dev
# Open http://localhost:5173
```

### Production (nginx on :8080, launchd services)

```bash
# Build the frontend and install all three launchd services
make install

# Open the app in your browser
make open  # → http://localhost:8080
```

To remove the launchd services:

```bash
make uninstall
```

### AI categorization (optional)

Set `ANTHROPIC_API_KEY` in your environment before running `make install` or calling the endpoint manually:

```bash
curl -X POST http://localhost:8000/api/categorize
```

Domains not found in the static allowlist are batched and sent to Claude for classification. Results are cached in `output/categories.json`.

## Project Structure

```
BrowserHistoryVisualizer/
├── backend/
│   ├── main.py          # FastAPI app + API routes
│   ├── pipeline.py      # Extract → process → categorize → cache
│   ├── detector.py      # Auto-detect Chromium browser History files
│   ├── extractor.py     # Copy-safe SQLite extraction
│   ├── processor.py     # Normalize visits, compute durations
│   ├── categorizer.py   # Static allowlist + AI classification
│   ├── analytics.py     # Heatmap, topics, domains, productivity, rabbit holes
│   ├── allowlist.py     # Domain → category static map
│   ├── models.py        # Pydantic response models
│   ├── config.py        # Paths, thresholds, taxonomy constants
│   └── tests/           # pytest test suite
├── frontend/
│   └── src/             # React + TypeScript dashboard
├── launchd/             # macOS service plists
├── nginx/               # nginx config template
├── Makefile             # install / uninstall / dev / logs / refresh
└── output/              # Generated cache files (gitignored)
```

## Screenshot

> _Screenshot placeholder — run `make dev` and open http://localhost:5173_

## License

MIT — see [LICENSE](LICENSE).
