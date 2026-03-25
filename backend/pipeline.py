"""Standalone pipeline: extract → process → categorize → compute → cache.

Run directly: python pipeline.py
Used by launchd daily at 6am and by POST /api/refresh.
"""

import logging
import sys
import time

import pandas as pd

pd.set_option("mode.copy_on_write", True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline() -> dict:
    """Execute full pipeline. Returns analytics data dict."""
    from analytics import compute_all, save_cache
    from categorizer import categorize_visits
    from detector import detect_browsers
    from extractor import extract_all
    from processor import process_visits

    t0 = time.perf_counter()

    # Step 1: Detect browsers
    t = time.perf_counter()
    browsers = detect_browsers()
    logger.info("Detect: %d browser(s) found (%.2fs)", len(browsers), time.perf_counter() - t)
    for b in browsers:
        logger.info("  %s: %s", b["name"], b["path"])

    if not browsers:
        logger.error("No browsers detected. Exiting.")
        sys.exit(1)

    # Step 2: Extract visits
    t = time.perf_counter()
    df = extract_all(browsers)
    logger.info("Extract: %d visits (%.2fs)", len(df), time.perf_counter() - t)

    if df.empty:
        logger.error("No visits extracted. Exiting.")
        sys.exit(1)

    # Step 3: Process (normalize, filter, durations)
    t = time.perf_counter()
    df = process_visits(df)
    logger.info("Process: %d clean visits (%.2fs)", len(df), time.perf_counter() - t)

    # Step 4: Categorize
    t = time.perf_counter()
    df = categorize_visits(df)
    logger.info("Categorize: done (%.2fs)", time.perf_counter() - t)

    # Step 5: Compute analytics
    t = time.perf_counter()
    data = compute_all(df)
    logger.info("Analytics: done (%.2fs)", time.perf_counter() - t)

    # Step 6: Store browser metadata for API status endpoint
    data["_browsers"] = browsers
    data["_total_visits"] = len(df)

    # Step 7: Save cache
    t = time.perf_counter()
    save_cache(data)
    logger.info("Cache: saved (%.2fs)", time.perf_counter() - t)

    total = time.perf_counter() - t0
    logger.info("Pipeline complete in %.2fs", total)

    return data


if __name__ == "__main__":
    try:
        run_pipeline()
        sys.exit(0)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)
