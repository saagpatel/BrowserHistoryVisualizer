# BrowserHistoryVisualizer

[![Python](https://img.shields.io/badge/python-%233776ab?style=flat-square&logo=python)](#) [![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](#)

> Find out where your time actually goes — without sending your browsing history anywhere.

BHV reads your Chromium-family browser history files directly, runs an analysis pipeline, and serves a React dashboard showing how you actually spend time online. No cloud, no tracking — your history stays on your machine.

## Features

- **Multi-browser detection** — auto-discovers Chrome, Arc, Brave, Edge, Vivaldi, Opera, and any Chromium browser under `~/Library/Application Support`
- **GitHub-style activity heatmap** — visits per day with 5-level intensity buckets across your full history
- **Category breakdown** — domain visits and estimated minutes per topic category (static allowlist + optional Claude AI classification)
- **Top domains** — ranked by visit count with category and estimated time
- **Hourly productivity chart** — focus vs. distraction minutes by hour
- **Rabbit hole detection** — identifies multi-domain browsing sessions spanning extended periods
- **Date range filtering** — scope heatmap and rabbit-hole views to any date window
- **launchd integration** — optional background service for daily pipeline runs at 6 AM

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- macOS (uses `~/Library/Application Support` paths)

### Installation
```bash
git clone https://github.com/saagpatel/BrowserHistoryVisualizer
cd BrowserHistoryVisualizer
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install
```

### Usage
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

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, pandas, uvicorn |
| Frontend | React 19 + TypeScript + Tailwind CSS 4 + Recharts + D3 |
| AI categorization | Anthropic Claude API (optional) |
| Proxy | nginx (Homebrew) |
| Service management | macOS launchd |

## License

MIT
