"""Categorize domains: static allowlist → JSON cache → uncategorized."""

import json
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd

from allowlist import ALLOWLIST
from config import AI_BATCH_SIZE, CATEGORIES_FILE, CATEGORY_TAXONOMY

logger = logging.getLogger(__name__)


def _load_cache() -> dict[str, dict]:
    """Load categories.json cache. Returns empty dict if absent or corrupt."""
    if not os.path.exists(CATEGORIES_FILE):
        return {}
    try:
        with open(CATEGORIES_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Cache load failed: %s", e)
        return {}


def _save_cache(cache: dict[str, dict]) -> None:
    """Atomically write categories.json (write to temp, then rename)."""
    os.makedirs(os.path.dirname(CATEGORIES_FILE) or ".", exist_ok=True)
    tmp_path = CATEGORIES_FILE + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(cache, f, indent=2, sort_keys=True)
        os.replace(tmp_path, CATEGORIES_FILE)
    except OSError as e:
        logger.error("Cache write failed: %s", e)
        # Clean up temp file if rename failed
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def categorize_static(domain: str) -> str:
    """Look up domain in the static allowlist. Returns category or 'uncategorized'."""
    # Try exact match first
    if domain in ALLOWLIST:
        return ALLOWLIST[domain]
    # Try with www. prefix
    if f"www.{domain}" in ALLOWLIST:
        return ALLOWLIST[f"www.{domain}"]
    # Try stripping www.
    if domain.startswith("www.") and domain[4:] in ALLOWLIST:
        return ALLOWLIST[domain[4:]]
    return "uncategorized"


def run_ai_classification(domains: list[str]) -> dict[str, str]:
    """Classify domains using the Claude API. Returns domain→category mapping.

    Batches into groups of AI_BATCH_SIZE. Writes results to categories.json
    after each batch (crash-safe). Requires ANTHROPIC_API_KEY in environment.
    """
    import anthropic

    client = anthropic.Anthropic()
    categories = ",".join(CATEGORY_TAXONOMY[:-1])  # exclude 'uncategorized'

    cache = _load_cache()
    results: dict[str, str] = {}
    api_calls = 0

    for i in range(0, len(domains), AI_BATCH_SIZE):
        batch = domains[i : i + AI_BATCH_SIZE]
        domain_list = "\n".join(batch)

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=(
                    f"Classify each domain into exactly one of: {categories}. "
                    "Return ONLY a JSON object mapping domain to category. "
                    "No explanation, no markdown."
                ),
                messages=[{"role": "user", "content": domain_list}],
            )
            api_calls += 1

            # Parse response — strip markdown fences if present
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].strip()

            batch_results = json.loads(text)

            # Validate and store
            valid_categories = set(CATEGORY_TAXONOMY)
            for domain, category in batch_results.items():
                if category in valid_categories and domain in batch:
                    results[domain] = category
                    cache[domain] = {
                        "category": category,
                        "source": "ai",
                        "ts": int(time.time()),
                    }

            # Save after each batch (crash-safe)
            _save_cache(cache)
            logger.info(
                "AI batch %d/%d: classified %d domains",
                i // AI_BATCH_SIZE + 1,
                (len(domains) + AI_BATCH_SIZE - 1) // AI_BATCH_SIZE,
                len(batch_results),
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response for batch %d: %s", i // AI_BATCH_SIZE + 1, e)
        except Exception as e:
            logger.error("AI classification error for batch %d: %s", i // AI_BATCH_SIZE + 1, e)

    return results


def get_uncategorized_domains() -> list[str]:
    """Return all domains in categories.json that are uncategorized or missing."""
    cache = _load_cache()
    return [
        domain for domain, info in cache.items()
        if info.get("category") == "uncategorized" or info.get("source") == "static"
        and info.get("category") == "uncategorized"
    ]


def categorize_visits(df: pd.DataFrame) -> pd.DataFrame:
    """Assign categories to all visits in the DataFrame.

    Priority: static allowlist → cache (AI/user overrides) → uncategorized.
    Updates categories.json cache with any new static lookups.
    """
    if df.empty:
        return df

    df = df.copy()
    cache = _load_cache()

    unique_domains = df["domain"].unique()
    stats = {"static": 0, "cached": 0, "uncategorized": 0}

    # Build domain → category mapping
    domain_categories: dict[str, str] = {}

    for domain in unique_domains:
        # Check cache first (user overrides take priority)
        if domain in cache and cache[domain].get("source") == "user":
            domain_categories[domain] = cache[domain]["category"]
            stats["cached"] += 1
            continue

        # Static allowlist
        static_cat = categorize_static(domain)
        if static_cat != "uncategorized":
            domain_categories[domain] = static_cat
            # Cache static lookups for consistency
            if domain not in cache or cache[domain].get("source") != "user":
                cache[domain] = {
                    "category": static_cat,
                    "source": "static",
                    "ts": int(time.time()),
                }
            stats["static"] += 1
            continue

        # Check AI cache
        if domain in cache and cache[domain].get("source") == "ai":
            domain_categories[domain] = cache[domain]["category"]
            stats["cached"] += 1
            continue

        # Uncategorized
        domain_categories[domain] = "uncategorized"
        stats["uncategorized"] += 1

    # Apply categories to DataFrame
    df = df.assign(category=df["domain"].map(domain_categories))

    # Save updated cache
    _save_cache(cache)

    total = sum(stats.values())
    logger.info(
        "Categories — Static: %d (%.0f%%) | Cached: %d (%.0f%%) | Uncategorized: %d (%.0f%%)",
        stats["static"], 100 * stats["static"] / max(total, 1),
        stats["cached"], 100 * stats["cached"] / max(total, 1),
        stats["uncategorized"], 100 * stats["uncategorized"] / max(total, 1),
    )

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if "--stats" in sys.argv:
        from extractor import extract_all
        from processor import process_visits

        df = extract_all()
        df = process_visits(df)
        df = categorize_visits(df)

        print(f"\nDomain breakdown:")
        for cat, group in df.groupby("category"):
            domains = group["domain"].nunique()
            print(f"  {cat:>20}: {len(group):>6} visits ({domains} domains)")
    else:
        print("Usage: python categorizer.py --stats")
