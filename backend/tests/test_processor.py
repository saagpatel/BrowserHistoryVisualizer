"""Tests for processor.py — timestamp conversion, URL filtering, duration inference."""

import pandas as pd
import pytest

from config import DURATION_CAP_S
from processor import chrome_ts_to_unix, extract_domain, filter_garbage_urls, infer_durations


class TestChromeTimestampConversion:
    def test_known_timestamp(self):
        # 13000000000000000 Chrome μs → 2012-12-14 23:06:40 UTC
        assert chrome_ts_to_unix(13_000_000_000_000_000) == 1355526400

    def test_recent_timestamp(self):
        # 2024-01-01 00:00:00 UTC → 1704067200
        chrome_ts = (1704067200 + 11_644_473_600) * 1_000_000
        assert chrome_ts_to_unix(chrome_ts) == 1704067200

    def test_zero_returns_zero(self):
        assert chrome_ts_to_unix(0) == 0

    def test_negative_returns_zero(self):
        assert chrome_ts_to_unix(-1) == 0

    def test_overflow_returns_zero(self):
        # Far future (year 2200+)
        assert chrome_ts_to_unix(99_999_999_999_999_999) == 0

    def test_very_old_returns_zero(self):
        # Before year 2000
        assert chrome_ts_to_unix(1_000_000) == 0


class TestExtractDomain:
    def test_simple_url(self):
        assert extract_domain("https://google.com/search?q=test") == "google.com"

    def test_strips_www(self):
        assert extract_domain("https://www.github.com/user/repo") == "github.com"

    def test_subdomain_preserved(self):
        assert extract_domain("https://docs.python.org/3/library/") == "docs.python.org"

    def test_port_stripped(self):
        assert extract_domain("http://localhost:3000/api") == "localhost"

    def test_empty_url(self):
        assert extract_domain("") == ""

    def test_malformed_url(self):
        assert extract_domain("not-a-url") == ""

    def test_lowercase(self):
        assert extract_domain("https://GITHUB.COM/user") == "github.com"


class TestFilterGarbageUrls:
    def test_keeps_valid_urls(self):
        df = pd.DataFrame({
            "url": ["https://google.com", "https://github.com"],
            "domain": ["google.com", "github.com"],
        })
        result = filter_garbage_urls(df)
        assert len(result) == 2

    def test_filters_chrome_extension(self):
        df = pd.DataFrame({
            "url": ["https://google.com", "chrome-extension://abc/popup.html"],
            "domain": ["google.com", "abc"],
        })
        result = filter_garbage_urls(df)
        assert len(result) == 1
        assert result.iloc[0]["domain"] == "google.com"

    def test_filters_chrome_internal(self):
        df = pd.DataFrame({
            "url": ["chrome://newtab", "chrome://settings", "https://google.com"],
            "domain": ["newtab", "settings", "google.com"],
        })
        result = filter_garbage_urls(df)
        assert len(result) == 1

    def test_filters_about_blank(self):
        df = pd.DataFrame({
            "url": ["about:blank", "https://google.com"],
            "domain": ["", "google.com"],
        })
        result = filter_garbage_urls(df)
        assert len(result) == 1

    def test_filters_empty_domain(self):
        df = pd.DataFrame({
            "url": ["https://google.com", "data:text/html,hello"],
            "domain": ["google.com", ""],
        })
        result = filter_garbage_urls(df)
        assert len(result) == 1

    def test_filters_all_garbage_types(self):
        urls = [
            "https://google.com",
            "chrome-extension://abc",
            "about:blank",
            "chrome://newtab",
            "data:text/html,hello",
            "javascript:void(0)",
        ]
        domains = ["google.com", "abc", "", "newtab", "", ""]
        df = pd.DataFrame({"url": urls, "domain": domains})
        result = filter_garbage_urls(df)
        assert len(result) == 1
        assert result.iloc[0]["domain"] == "google.com"

    def test_empty_dataframe(self):
        df = pd.DataFrame({"url": [], "domain": []})
        result = filter_garbage_urls(df)
        assert len(result) == 0


class TestInferDurations:
    def test_basic_gap(self):
        df = pd.DataFrame({
            "visit_time": [0, 100, 200],
            "browser": ["chrome"] * 3,
        })
        result = infer_durations(df)
        assert result.iloc[0] == 100
        assert result.iloc[1] == 100

    def test_duration_cap(self):
        df = pd.DataFrame({
            "visit_time": [0, 100, 5100],
            "browser": ["chrome"] * 3,
        })
        result = infer_durations(df)
        assert result.iloc[1] == DURATION_CAP_S  # 5000 capped to 1200

    def test_last_visit_gets_median(self):
        df = pd.DataFrame({
            "visit_time": [0, 100, 200, 300],
            "browser": ["chrome"] * 4,
        })
        result = infer_durations(df)
        # All gaps are 100, median is 100, last visit gets median
        assert result.iloc[3] == 100

    def test_separate_browsers(self):
        df = pd.DataFrame({
            "visit_time": [0, 100, 0, 200],
            "browser": ["chrome", "chrome", "arc", "arc"],
        })
        result = infer_durations(df)
        # Chrome: gap=100, last=100 (median)
        # Arc: gap=200, last=200 (median, but capped)
        assert result.iloc[0] == 100  # chrome first
        assert result.iloc[2] == 200  # arc first

    def test_empty_dataframe(self):
        df = pd.DataFrame({"visit_time": [], "browser": []})
        result = infer_durations(df)
        assert len(result) == 0

    def test_single_visit(self):
        df = pd.DataFrame({
            "visit_time": [1000],
            "browser": ["chrome"],
        })
        result = infer_durations(df)
        # Single visit gets default median (60s)
        assert result.iloc[0] == 60
