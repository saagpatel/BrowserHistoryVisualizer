"""Compute all 5 analytics datasets from processed visit data."""

import json
import logging
import os
import time
from collections import Counter
from datetime import datetime, timezone
from hashlib import md5

import numpy as np
import pandas as pd

from config import (
    ANALYTICS_CACHE_FILE,
    CACHE_MAX_AGE_S,
    CATEGORY_TAXONOMY,
    DISTRACTION_CATEGORIES,
    FOCUS_CATEGORIES,
    RABBIT_MIN_DOMAINS,
    RABBIT_MIN_DURATION_S,
    RABBIT_MIN_VISITS,
    SESSION_GAP_S,
)

logger = logging.getLogger(__name__)


def compute_heatmap(df: pd.DataFrame) -> list[dict]:
    """GitHub-style heatmap: visits per day with 5-level intensity."""
    if df.empty:
        return []

    dates = pd.to_datetime(df["visit_time"], unit="s").dt.strftime("%Y-%m-%d")
    daily = dates.value_counts().reset_index()
    daily.columns = ["date", "count"]

    # Compute intensity levels (0-4) using quantile bins
    if len(daily) <= 1:
        intensity = pd.Series([4] * len(daily), index=daily.index)
    else:
        counts = daily["count"]
        try:
            intensity = pd.qcut(counts, q=5, labels=[0, 1, 2, 3, 4], duplicates="drop").astype(int)
        except ValueError:
            intensity = pd.cut(
                counts,
                bins=max(2, min(5, counts.nunique())),
                labels=list(range(min(5, counts.nunique()))),
                duplicates="drop",
            ).astype(int)

    daily = daily.assign(intensity=intensity)
    return daily[["date", "count", "intensity"]].to_dict("records")


def compute_topics(df: pd.DataFrame) -> list[dict]:
    """Category breakdown: visits, estimated minutes, percentage per category."""
    if df.empty:
        return []

    results: list[dict] = []
    total_visits = len(df)

    for category in CATEGORY_TAXONOMY:
        cat_df = df[df["category"] == category]
        visits = len(cat_df)
        minutes = int(cat_df["duration_seconds"].sum() / 60) if not cat_df.empty else 0
        percentage = round(100 * visits / total_visits, 1) if total_visits > 0 else 0.0

        results.append({
            "category": category,
            "visits": visits,
            "estimated_minutes": minutes,
            "percentage": percentage,
        })

    return results


def compute_domains(df: pd.DataFrame) -> list[dict]:
    """Top domains by visit count with category and estimated minutes."""
    if df.empty:
        return []

    grouped = df.groupby("domain").agg(
        visit_count=("url", "size"),
        estimated_minutes=("duration_seconds", "sum"),
        category=("category", "first"),
    ).reset_index().copy()

    grouped["estimated_minutes"] = (grouped["estimated_minutes"] / 60).astype(int)
    grouped = grouped.sort_values("visit_count", ascending=False).head(100)

    return grouped[["domain", "category", "visit_count", "estimated_minutes"]].to_dict("records")


def compute_productivity(df: pd.DataFrame) -> list[dict]:
    """Hourly focus vs distraction minutes."""
    if df.empty:
        return []

    hours = pd.to_datetime(df["visit_time"], unit="s").dt.hour
    minutes = df["duration_seconds"] / 60
    categories = df["category"]

    results: list[dict] = []
    for hour in range(24):
        hour_mask = hours == hour
        hour_mins = minutes[hour_mask]
        hour_cats = categories[hour_mask]
        focus = hour_mins[hour_cats.isin(FOCUS_CATEGORIES)].sum()
        distraction = hour_mins[hour_cats.isin(DISTRACTION_CATEGORIES)].sum()
        total = focus + distraction
        ratio = round(focus / total, 2) if total > 0 else 0.0

        results.append({
            "hour": hour,
            "focus_minutes": int(focus),
            "distraction_minutes": int(distraction),
            "ratio": ratio,
        })

    return results


def _assign_sessions(df: pd.DataFrame) -> pd.Series:
    """Assign session IDs based on time gaps > SESSION_GAP_S."""
    if df.empty:
        return pd.Series(dtype="str")

    df = df.sort_values("visit_time")
    gaps = df["visit_time"].diff().fillna(0)
    session_breaks = (gaps > SESSION_GAP_S).cumsum()

    # Generate readable session IDs
    session_ids = session_breaks.apply(lambda x: f"session-{x:04d}")
    return session_ids


def compute_rabbit_holes(df: pd.DataFrame) -> list[dict]:
    """Detect rabbit hole sessions meeting minimum thresholds."""
    if df.empty:
        return []

    df = df.sort_values("visit_time").copy()
    df = df.assign(session_id=_assign_sessions(df))

    sessions: list[dict] = []

    for session_id, group in df.groupby("session_id"):
        visit_count = len(group)
        unique_domains = group["domain"].nunique()
        duration_s = int(group["visit_time"].max() - group["visit_time"].min())

        # Filter by minimums
        if (visit_count < RABBIT_MIN_VISITS
                or duration_s < RABBIT_MIN_DURATION_S
                or unique_domains < RABBIT_MIN_DOMAINS):
            continue

        # Build nodes: unique domain+title combos
        nodes: list[dict] = []
        seen_node_ids: set[str] = set()
        for _, row in group.iterrows():
            node_id = md5(f"{row['domain']}|{row['title']}".encode()).hexdigest()[:10]
            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "domain": row["domain"],
                    "title": str(row["title"] or row["domain"]),
                    "category": row["category"],
                })

        # Build edges: sequential visit pairs
        edges: list[tuple[str, str]] = []
        prev_id = None
        for _, row in group.iterrows():
            node_id = md5(f"{row['domain']}|{row['title']}".encode()).hexdigest()[:10]
            if prev_id is not None and prev_id != node_id:
                edges.append((prev_id, node_id))
            prev_id = node_id

        # Dominant topic: most common category
        cat_counts = Counter(group["category"])
        dominant = cat_counts.most_common(1)[0][0] if cat_counts else "uncategorized"

        sessions.append({
            "session_id": str(session_id),
            "start_time": int(group["visit_time"].min()),
            "duration_minutes": max(1, duration_s // 60),
            "visit_count": visit_count,
            "dominant_topic": dominant,
            "nodes": nodes,
            "edges": edges,
        })

    # Sort by duration descending (most interesting first)
    sessions.sort(key=lambda s: s["duration_minutes"], reverse=True)

    logger.info("Rabbit holes: %d sessions detected (from %d total sessions)",
                len(sessions), df["session_id"].nunique())

    return sessions


def compute_all(df: pd.DataFrame) -> dict:
    """Compute all 5 analytics datasets."""
    return {
        "heatmap": compute_heatmap(df),
        "topics": compute_topics(df),
        "domains": compute_domains(df),
        "productivity": compute_productivity(df),
        "rabbit_holes": compute_rabbit_holes(df),
    }


def save_cache(data: dict) -> None:
    """Write analytics cache to disk."""
    os.makedirs(os.path.dirname(ANALYTICS_CACHE_FILE) or ".", exist_ok=True)
    tmp_path = ANALYTICS_CACHE_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(tmp_path, ANALYTICS_CACHE_FILE)
    logger.info("Cache saved: %s (%.1f KB)", ANALYTICS_CACHE_FILE,
                os.path.getsize(ANALYTICS_CACHE_FILE) / 1024)


def load_cache() -> dict | None:
    """Load analytics cache. Returns None if absent or stale (>24h)."""
    if not os.path.exists(ANALYTICS_CACHE_FILE):
        return None

    mtime = os.path.getmtime(ANALYTICS_CACHE_FILE)
    age = time.time() - mtime
    if age > CACHE_MAX_AGE_S:
        logger.info("Cache stale (%.1f hours old)", age / 3600)
        return None

    try:
        with open(ANALYTICS_CACHE_FILE) as f:
            data = json.load(f)
        logger.info("Cache loaded (%.1f hours old)", age / 3600)
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Cache load failed: %s", e)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    from extractor import extract_all
    from processor import process_visits
    from categorizer import categorize_visits

    df = extract_all()
    df = process_visits(df)
    df = categorize_visits(df)
    data = compute_all(df)
    save_cache(data)

    print(f"\nDatasets:")
    for key, value in data.items():
        print(f"  {key}: {len(value)} entries")
