"""Tests for analytics.py — heatmap, topics, sessions, rabbit holes."""

import pandas as pd
import pytest

from analytics import (
    compute_heatmap,
    compute_productivity,
    compute_rabbit_holes,
    compute_topics,
    _assign_sessions,
)
from config import SESSION_GAP_S


def _make_visits(n: int, start_time: int = 1700000000, gap: int = 180, **kwargs) -> pd.DataFrame:
    """Factory for test visit DataFrames."""
    defaults = {
        "url": [f"https://example{i}.com/page" for i in range(n)],
        "domain": [f"example{i}.com" for i in range(n)],
        "title": [f"Page {i}" for i in range(n)],
        "visit_time": [start_time + i * gap for i in range(n)],
        "duration_seconds": [gap] * n,
        "category": ["devtools"] * n,
        "browser": ["chrome"] * n,
    }
    defaults.update(kwargs)
    return pd.DataFrame(defaults)


class TestComputeHeatmap:
    def test_single_day(self):
        # All visits on same day
        df = _make_visits(5, start_time=1700000000, gap=60)
        result = compute_heatmap(df)
        assert len(result) == 1
        assert result[0]["count"] == 5
        assert result[0]["intensity"] == 4  # single day always max

    def test_multiple_days(self):
        # Spread across 3 days
        day1 = 1700000000  # 2023-11-14
        day2 = day1 + 86400
        day3 = day1 + 86400 * 2
        df = pd.DataFrame({
            "visit_time": [day1, day1, day2, day3, day3, day3],
            "url": ["https://a.com"] * 6,
            "domain": ["a.com"] * 6,
        })
        result = compute_heatmap(df)
        assert len(result) == 3
        dates = {r["date"] for r in result}
        assert len(dates) == 3

    def test_empty(self):
        df = pd.DataFrame({"visit_time": [], "url": [], "domain": []})
        assert compute_heatmap(df) == []


class TestComputeTopics:
    def test_all_categories_present(self):
        df = _make_visits(3, category=["work", "social", "devtools"])
        result = compute_topics(df)
        categories = {r["category"] for r in result}
        assert "work" in categories
        assert "uncategorized" in categories  # always included even if 0

    def test_percentages_sum_to_100(self):
        df = _make_visits(10)
        result = compute_topics(df)
        total = sum(r["percentage"] for r in result)
        assert abs(total - 100.0) < 1.0  # allow rounding error

    def test_empty(self):
        df = pd.DataFrame({"category": [], "duration_seconds": []})
        assert compute_topics(df) == []


class TestAssignSessions:
    def test_single_session(self):
        df = _make_visits(5, gap=60)  # 60s gaps, well under SESSION_GAP_S
        sessions = _assign_sessions(df)
        assert sessions.nunique() == 1

    def test_two_sessions(self):
        # 3 visits, then a long gap, then 2 more
        times = [1000, 1060, 1120, 1120 + SESSION_GAP_S + 1, 1120 + SESSION_GAP_S + 61]
        df = pd.DataFrame({"visit_time": times})
        sessions = _assign_sessions(df)
        assert sessions.nunique() == 2

    def test_gap_exactly_at_threshold(self):
        # Gap exactly equal to SESSION_GAP_S should NOT create new session
        times = [1000, 1000 + SESSION_GAP_S]
        df = pd.DataFrame({"visit_time": times})
        sessions = _assign_sessions(df)
        assert sessions.nunique() == 1


class TestComputeRabbitHoles:
    def test_qualifying_session(self):
        # 6 visits to 3 domains over 15 minutes with 3-minute gaps
        df = pd.DataFrame({
            "url": [f"https://d{i%3}.com/p{i}" for i in range(6)],
            "domain": [f"d{i%3}.com" for i in range(6)],
            "title": [f"Page {i}" for i in range(6)],
            "visit_time": [1000 + i * 180 for i in range(6)],
            "duration_seconds": [180] * 6,
            "category": ["devtools"] * 6,
            "browser": ["chrome"] * 6,
        })
        result = compute_rabbit_holes(df)
        assert len(result) == 1
        assert result[0]["visit_count"] == 6
        assert result[0]["dominant_topic"] == "devtools"
        assert len(result[0]["nodes"]) >= 3  # at least 3 unique domain+title combos

    def test_too_few_visits(self):
        df = _make_visits(2, gap=60)  # Only 2 visits, need >= 4
        result = compute_rabbit_holes(df)
        assert len(result) == 0

    def test_too_few_domains(self):
        # 5 visits but all same domain
        df = _make_visits(5, gap=120, domain=["example.com"] * 5)
        result = compute_rabbit_holes(df)
        assert len(result) == 0

    def test_too_short_duration(self):
        # 5 visits, 2 domains, but only 40s total (need 600s)
        df = pd.DataFrame({
            "url": [f"https://d{i%2}.com/p{i}" for i in range(5)],
            "domain": [f"d{i%2}.com" for i in range(5)],
            "title": [f"Page {i}" for i in range(5)],
            "visit_time": [1000 + i * 10 for i in range(5)],
            "duration_seconds": [10] * 5,
            "category": ["devtools"] * 5,
            "browser": ["chrome"] * 5,
        })
        result = compute_rabbit_holes(df)
        assert len(result) == 0

    def test_empty(self):
        df = pd.DataFrame({
            "url": [], "domain": [], "title": [], "visit_time": [],
            "duration_seconds": [], "category": [], "browser": [],
        })
        assert compute_rabbit_holes(df) == []


class TestComputeProductivity:
    def test_24_hours(self):
        df = _make_visits(3)
        result = compute_productivity(df)
        assert len(result) == 24  # always 24 entries

    def test_focus_vs_distraction(self):
        df = pd.DataFrame({
            "visit_time": [1700000000, 1700000000],  # same hour
            "duration_seconds": [600, 300],
            "category": ["work", "social"],
        })
        result = compute_productivity(df)
        # Find the hour with data
        active_hours = [r for r in result if r["focus_minutes"] > 0 or r["distraction_minutes"] > 0]
        assert len(active_hours) == 1
        assert active_hours[0]["focus_minutes"] == 10  # 600s = 10min
        assert active_hours[0]["distraction_minutes"] == 5  # 300s = 5min

    def test_empty(self):
        df = pd.DataFrame({"visit_time": [], "duration_seconds": [], "category": []})
        assert compute_productivity(df) == []
