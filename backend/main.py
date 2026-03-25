"""FastAPI app — API-only, no static files, no CORS."""

import json
import logging
import os
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Query

from analytics import load_cache, save_cache
from categorizer import _load_cache as load_categories, _save_cache as save_categories, run_ai_classification
from config import ANALYTICS_CACHE_FILE, CATEGORIES_FILE, SETTINGS_FILE
from models import (
    AllDatasets,
    AppStatus,
    BrowserPathOverride,
    CategoryOverride,
    DetectedBrowser,
    DomainRankEntry,
    HeatmapDay,
    ProductivityPoint,
    RabbitHoleSession,
    TopicSlice,
)

logger = logging.getLogger(__name__)

# In-memory cache
_cache: dict | None = None


def _ensure_cache() -> dict:
    """Load cache from disk, running pipeline if needed."""
    global _cache
    if _cache is not None:
        return _cache

    data = load_cache()
    if data is None:
        logger.info("No cache found — running pipeline...")
        result = subprocess.run(
            [sys.executable, "pipeline.py"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error("Pipeline failed: %s", result.stderr)
            raise RuntimeError(f"Pipeline failed: {result.stderr[-500:]}")
        data = load_cache()
        if data is None:
            raise RuntimeError("Pipeline completed but cache still not found")

    _cache = data
    return _cache


def _build_status(data: dict) -> AppStatus:
    """Construct AppStatus from cached data."""
    browsers_raw = data.get("_browsers", [])
    browsers = [
        DetectedBrowser(
            name=b["name"],
            path=b["path"],
            visit_count=b.get("visit_count", 0),
            detected=b.get("detected", True),
            manual_override=b.get("manual_override", False),
        )
        for b in browsers_raw
    ]

    # Date range from heatmap
    heatmap = data.get("heatmap", [])
    if heatmap:
        dates = [h["date"] for h in heatmap]
        date_range = (min(dates), max(dates))
    else:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        date_range = (today, today)

    # Last refreshed from cache file mtime
    last_refreshed = None
    if os.path.exists(ANALYTICS_CACHE_FILE):
        last_refreshed = int(os.path.getmtime(ANALYTICS_CACHE_FILE))

    total_visits = data.get("_total_visits", 0)

    return AppStatus(
        browsers=browsers,
        total_visits=total_visits,
        date_range_available=date_range,
        last_refreshed=last_refreshed,
    )


def _filter_by_date(data: dict, start: str, end: str) -> dict:
    """Filter all datasets by date range (YYYY-MM-DD)."""
    filtered = {}

    # Heatmap: filter by date string
    filtered["heatmap"] = [
        h for h in data.get("heatmap", [])
        if start <= h["date"] <= end
    ]

    # Convert date range to Unix timestamps for time-based filtering
    try:
        start_ts = int(datetime.strptime(start, "%Y-%m-%d").replace(
            tzinfo=timezone.utc).timestamp())
        end_ts = int(datetime.strptime(end, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc).timestamp())
    except ValueError:
        # Invalid dates — return unfiltered
        return data

    # Rabbit holes: filter by start_time
    filtered["rabbit_holes"] = [
        rh for rh in data.get("rabbit_holes", [])
        if start_ts <= rh["start_time"] <= end_ts
    ]

    # Topics, domains, productivity: these are aggregates over all data.
    # For Phase 1, return unfiltered (full-range filtering requires
    # re-computing from raw visits, which is a Phase 2+ feature).
    filtered["topics"] = data.get("topics", [])
    filtered["domains"] = data.get("domains", [])
    filtered["productivity"] = data.get("productivity", [])

    return filtered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load cache on startup."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    _ensure_cache()
    logger.info("Cache loaded, server ready")
    yield


app = FastAPI(title="BHV", lifespan=lifespan)


@app.get("/api/status")
async def get_status() -> AppStatus:
    data = _ensure_cache()
    return _build_status(data)


@app.post("/api/refresh")
async def post_refresh() -> AppStatus:
    global _cache
    logger.info("Refresh requested — running pipeline...")
    result = subprocess.run(
        [sys.executable, "pipeline.py"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Pipeline failed: %s", result.stderr)
        raise RuntimeError(f"Pipeline failed: {result.stderr[-500:]}")
    _cache = None  # Invalidate in-memory cache
    data = _ensure_cache()
    return _build_status(data)


@app.post("/api/categorize")
async def post_categorize():
    global _cache
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set", "classified": 0, "cached": 0, "api_calls": 0}

    categories = load_categories()
    uncategorized = [
        domain for domain, info in categories.items()
        if info.get("category") == "uncategorized"
    ]

    if not uncategorized:
        return {"classified": 0, "cached": len(categories), "api_calls": 0}

    logger.info("Classifying %d uncategorized domains...", len(uncategorized))
    results = run_ai_classification(uncategorized)

    # Invalidate cache so next /api/all picks up new categories
    _cache = None

    return {
        "classified": len(results),
        "cached": len(categories),
        "api_calls": (len(uncategorized) + 49) // 50,
    }


@app.get("/api/categories")
async def get_categories() -> dict[str, str]:
    categories = load_categories()
    return {domain: info["category"] for domain, info in categories.items()}


@app.post("/api/categories/{domain}")
async def post_category_override(domain: str, body: CategoryOverride):
    categories = load_categories()
    categories[domain] = {
        "category": body.category,
        "source": "user",
        "ts": int(time.time()),
    }
    save_categories(categories)
    return {"ok": True}


@app.get("/api/settings")
async def get_settings():
    data = _ensure_cache()
    return _build_status(data).browsers


@app.post("/api/settings")
async def post_settings(body: BrowserPathOverride):
    settings_path = SETTINGS_FILE
    settings: dict = {}
    if os.path.exists(settings_path):
        with open(settings_path) as f:
            settings = json.load(f)
    if "browser_overrides" not in settings:
        settings["browser_overrides"] = {}
    settings["browser_overrides"][body.browser] = body.path
    os.makedirs(os.path.dirname(settings_path) or ".", exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    return {"ok": True}


@app.get("/api/all")
async def get_all(
    start: str = Query(default="", description="Start date YYYY-MM-DD"),
    end: str = Query(default="", description="End date YYYY-MM-DD"),
) -> AllDatasets:
    data = _ensure_cache()
    status = _build_status(data)

    # Default to full range if no dates provided
    if not start:
        start = status.date_range_available[0]
    if not end:
        end = status.date_range_available[1]

    filtered = _filter_by_date(data, start, end)

    return AllDatasets(
        status=status,
        heatmap=[HeatmapDay(**h) for h in filtered["heatmap"]],
        topics=[TopicSlice(**t) for t in filtered["topics"]],
        domains=[DomainRankEntry(**d) for d in filtered["domains"]],
        productivity=[ProductivityPoint(**p) for p in filtered["productivity"]],
        rabbit_holes=[RabbitHoleSession(**rh) for rh in filtered["rabbit_holes"]],
    )
