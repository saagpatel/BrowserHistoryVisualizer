"""Normalize timestamps, clean URLs, infer duration, dedup visits."""

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from config import CHROME_EPOCH_OFFSET, DURATION_CAP_S

logger = logging.getLogger(__name__)

# URL schemes to filter out
_GARBAGE_SCHEMES: set[str] = {"chrome-extension", "chrome", "edge", "about", "brave", "vivaldi"}


@dataclass
class Visit:
    url: str
    domain: str
    title: str
    visit_time: int  # Unix timestamp seconds
    duration_seconds: int  # Inferred, capped at DURATION_CAP_S
    is_duration_estimated: bool  # Always True
    visit_count: int  # From urls table (total historical count)
    typed: bool  # True if user typed URL directly
    browser: str  # "chrome" | "atlas" | "comet" | "arc" | etc.
    category: str  # Populated by categorizer.py


def chrome_ts_to_unix(ts: int | float) -> int:
    """Convert Chrome/Chromium microseconds-since-1601 to Unix timestamp (seconds)."""
    try:
        unix_ts = int(ts / 1_000_000 - CHROME_EPOCH_OFFSET)
        # Sanity check: should be between 2000-01-01 and 2100-01-01
        if unix_ts < 946_684_800 or unix_ts > 4_102_444_800:
            return 0
        return unix_ts
    except (ValueError, OverflowError):
        return 0


def extract_domain(url: str) -> str:
    """Extract domain from URL, stripping www. prefix."""
    try:
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower()
    except (ValueError, AttributeError):
        return ""


def filter_garbage_urls(df: pd.DataFrame) -> pd.DataFrame:
    """Remove internal browser pages, extensions, and empty-domain rows."""
    if df.empty:
        return df

    # Parse schemes
    schemes = df["url"].str.split("://", n=1).str[0].str.lower()
    scheme_mask = ~schemes.isin(_GARBAGE_SCHEMES)

    # Filter empty domains
    domain_mask = df["domain"].str.len() > 0

    # Filter data: URIs and javascript: URIs
    prefix_mask = ~df["url"].str.lower().str.startswith(("data:", "javascript:"))

    filtered = df[scheme_mask & domain_mask & prefix_mask].copy()

    removed = len(df) - len(filtered)
    if removed > 0:
        logger.info("Filtered %d garbage URLs (%.1f%%)", removed, 100 * removed / len(df))

    return filtered


def infer_durations(df: pd.DataFrame) -> pd.Series:
    """Infer visit duration from gap-to-next-visit, capped at DURATION_CAP_S.

    Within each browser, sorted by time: duration = next_visit_time - visit_time.
    Last visit in each browser gets the median duration for that browser.
    """
    if df.empty:
        return pd.Series(dtype="int64")

    result = pd.Series(0, index=df.index, dtype="int64")

    for _browser, group in df.groupby("browser"):
        sorted_group = group.sort_values("visit_time")
        idx = sorted_group.index

        # Gap to next visit
        gaps = sorted_group["visit_time"].diff(-1).abs()

        # Cap at DURATION_CAP_S
        durations = gaps.clip(upper=DURATION_CAP_S).fillna(0).astype("int64")

        # Last visit gets median duration (or 60s if no valid durations)
        valid_durations = durations[durations > 0]
        median_dur = int(valid_durations.median()) if len(valid_durations) > 0 else 60
        median_dur = min(median_dur, DURATION_CAP_S)

        # Set last visit duration
        if len(idx) > 0:
            durations.iloc[-1] = median_dur

        result.loc[idx] = durations

    return result


def process_visits(df: pd.DataFrame) -> pd.DataFrame:
    """Full processing pipeline: timestamps, domains, filtering, duration inference."""
    if df.empty:
        logger.warning("Empty DataFrame passed to process_visits")
        return df

    initial_count = len(df)

    # Convert Chrome timestamps to Unix seconds
    df = df.copy()
    df["visit_time"] = df["visit_time"].apply(chrome_ts_to_unix)

    # Drop rows with invalid timestamps
    df = df[df["visit_time"] > 0].copy()
    if len(df) < initial_count:
        logger.info("Dropped %d rows with invalid timestamps", initial_count - len(df))

    # Extract domains
    df["domain"] = df["url"].apply(extract_domain)

    # Filter garbage
    df = filter_garbage_urls(df)

    # Infer durations
    df["duration_seconds"] = infer_durations(df)
    df["is_duration_estimated"] = True

    # Rename typed_count → typed (bool)
    if "typed_count" in df.columns:
        df["typed"] = df["typed_count"] > 0
        df.drop(columns=["typed_count"], inplace=True)
    else:
        df["typed"] = False

    # Initialize category column (populated by categorizer)
    df["category"] = "uncategorized"

    # Drop from_visit (no longer needed after extraction)
    df.drop(columns=["from_visit"], errors="ignore", inplace=True)

    # Sort by time
    df.sort_values("visit_time", inplace=True)
    df.reset_index(drop=True, inplace=True)

    clean_count = len(df)
    filtered_count = initial_count - clean_count
    logger.info("Processed: %d clean, %d filtered", clean_count, filtered_count)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    from extractor import extract_all

    df = extract_all()
    if not df.empty:
        result = process_visits(df)
        print(f"\nProcessed: {len(result)} clean, {len(df) - len(result)} filtered")
        print(f"Date range: {pd.to_datetime(result['visit_time'].min(), unit='s')} → "
              f"{pd.to_datetime(result['visit_time'].max(), unit='s')}")
        print(f"Unique domains: {result['domain'].nunique()}")
        print(f"Duration stats: median={result['duration_seconds'].median():.0f}s, "
              f"max={result['duration_seconds'].max()}s")
