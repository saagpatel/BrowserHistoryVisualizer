"""Tests for categorizer.py — static lookup, cache round-trip, unknown domains."""

import json
import os
import tempfile

import pandas as pd
import pytest

from categorizer import categorize_static, categorize_visits


class TestCategorizeStatic:
    def test_known_domains(self):
        cases = [
            ("google.com", "work"),
            ("github.com", "devtools"),
            ("reddit.com", "social"),
            ("youtube.com", "entertainment"),
            ("stackoverflow.com", "devtools"),
            ("x.com", "social"),
            ("linkedin.com", "social"),
            ("slack.com", "work"),
            ("notion.so", "work"),
            ("figma.com", "work"),
            ("jira.atlassian.com", "work"),
            ("amazon.com", "shopping"),
            ("netflix.com", "entertainment"),
            ("wikipedia.org", "research"),
            ("nytimes.com", "news"),
        ]
        for domain, expected in cases:
            assert categorize_static(domain) == expected, f"{domain} → expected {expected}"

    def test_unknown_domain(self):
        assert categorize_static("obscure-domain-xyz-12345.com") == "uncategorized"

    def test_www_prefix_fallback(self):
        # Should find google.com even with www. prefix
        assert categorize_static("www.google.com") == "work"

    def test_case_sensitivity(self):
        # Domain should be lowercase already from processor
        assert categorize_static("GITHUB.COM") == "uncategorized"  # case-sensitive lookup


class TestCategorizeVisits:
    def test_applies_categories(self):
        df = pd.DataFrame({
            "url": ["https://github.com/test", "https://youtube.com/watch"],
            "domain": ["github.com", "youtube.com"],
            "category": ["uncategorized", "uncategorized"],
        })
        result = categorize_visits(df)
        assert result.iloc[0]["category"] == "devtools"
        assert result.iloc[1]["category"] == "entertainment"

    def test_unknown_stays_uncategorized(self):
        df = pd.DataFrame({
            "url": ["https://unknown-xyz-98765.com"],
            "domain": ["unknown-xyz-98765.com"],
            "category": ["uncategorized"],
        })
        result = categorize_visits(df)
        assert result.iloc[0]["category"] == "uncategorized"

    def test_empty_dataframe(self):
        df = pd.DataFrame({"url": [], "domain": [], "category": []})
        result = categorize_visits(df)
        assert len(result) == 0

    def test_cache_round_trip(self, tmp_path, monkeypatch):
        """Verify categories.json is written and read correctly."""
        cache_file = str(tmp_path / "categories.json")
        monkeypatch.setattr("categorizer.CATEGORIES_FILE", cache_file)

        # First run — writes cache
        df = pd.DataFrame({
            "url": ["https://github.com/test"],
            "domain": ["github.com"],
            "category": ["uncategorized"],
        })
        categorize_visits(df)
        assert os.path.exists(cache_file)

        with open(cache_file) as f:
            cache = json.load(f)
        assert "github.com" in cache
        assert cache["github.com"]["source"] == "static"
        assert cache["github.com"]["category"] == "devtools"

    def test_user_override_takes_priority(self, tmp_path, monkeypatch):
        """User overrides should take priority over static allowlist."""
        cache_file = str(tmp_path / "categories.json")
        monkeypatch.setattr("categorizer.CATEGORIES_FILE", cache_file)

        # Pre-populate cache with user override
        with open(cache_file, "w") as f:
            json.dump({
                "github.com": {"category": "work", "source": "user", "ts": 1000},
            }, f)

        df = pd.DataFrame({
            "url": ["https://github.com/test"],
            "domain": ["github.com"],
            "category": ["uncategorized"],
        })
        result = categorize_visits(df)
        # User override → "work", not static allowlist → "devtools"
        assert result.iloc[0]["category"] == "work"
