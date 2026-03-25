"""Detect Chromium-based browsers by globbing for History SQLite files and validating schema."""

import glob
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

# Known directory names → browser names
_KNOWN_BROWSERS: dict[str, str] = {
    "google/chrome": "chrome",
    "google chrome": "chrome",
    "chromium": "chromium",
    "com.openai.atlas": "atlas",
    "comet": "comet",
    "arc": "arc",
    "arc/user data": "arc",
    "brave-browser": "brave",
    "microsoft edge": "edge",
    "vivaldi": "vivaldi",
    "opera": "opera",
    "opera software/opera stable": "opera",
}

# Required tables for a valid Chromium history database
_REQUIRED_TABLES: set[str] = {"urls", "visits"}

# Required columns in urls table to distinguish from Electron apps
_REQUIRED_URL_COLUMNS: set[str] = {"id", "url", "title", "visit_count", "last_visit_time"}


def _guess_browser_name(path: str) -> str:
    """Infer browser name from the Application Support subdirectory path."""
    app_support = os.path.expanduser("~/Library/Application Support")
    relative = os.path.relpath(path, app_support)
    # relative looks like "Google/Chrome/Default/History" or "Comet/Default/History"
    # Strip /Default/History suffix
    parts = relative.split(os.sep)
    if len(parts) >= 3:
        # e.g. ["Google", "Chrome", "Default", "History"] → "google/chrome"
        browser_dir = "/".join(parts[:-2]).lower()
    elif len(parts) >= 2:
        # e.g. ["Comet", "Default", "History"] → "comet"
        browser_dir = parts[0].lower()
    else:
        browser_dir = parts[0].lower()

    return _KNOWN_BROWSERS.get(browser_dir, browser_dir.split("/")[-1])


def _validate_schema(path: str) -> bool:
    """Check that a SQLite file has Chromium history schema (not just any SQLite).

    If the database is locked, copies to a temp file for validation.
    """
    def _check(db_path: str) -> bool:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.1)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        if not _REQUIRED_TABLES.issubset(tables):
            conn.close()
            return False
        cursor = conn.execute("PRAGMA table_info(urls)")
        url_columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        return _REQUIRED_URL_COLUMNS.issubset(url_columns)

    try:
        return _check(path)
    except sqlite3.OperationalError:
        # Database locked — validate via SQLite header bytes instead of expensive copy.
        # Chromium History files have "SQLite format 3" magic at offset 0.
        # If it's a valid SQLite file at a */Default/History path, it's almost certainly
        # a Chromium browser. The extractor will do the real validation when it copies.
        try:
            with open(path, "rb") as f:
                header = f.read(16)
            if header.startswith(b"SQLite format 3"):
                logger.debug("Database locked but valid SQLite header: %s", path)
                return True
        except OSError:
            pass
        return False
    except (sqlite3.Error, OSError) as e:
        logger.debug("Schema validation failed for %s: %s", path, e)
        return False


def detect_browsers() -> list[dict]:
    """Find all Chromium-based browser History files on this machine.

    Returns list of dicts with keys: name, path, detected, visit_count.
    """
    app_support = os.path.expanduser("~/Library/Application Support")

    # Dual-level glob: catches both 1-deep (Comet, Atlas) and 2-deep (Chrome, Arc)
    patterns = [
        os.path.join(app_support, "*/Default/History"),
        os.path.join(app_support, "*/*/Default/History"),
    ]

    candidates: set[str] = set()
    for pattern in patterns:
        candidates.update(glob.glob(pattern))

    # Deduplicate by resolved path
    seen: set[str] = set()
    browsers: list[dict] = []

    for path in sorted(candidates):
        real_path = os.path.realpath(path)
        if real_path in seen:
            continue
        seen.add(real_path)

        if not _validate_schema(path):
            logger.debug("Skipping non-Chromium file: %s", path)
            continue

        name = _guess_browser_name(path)

        # Get visit count (may fail if locked)
        visit_count = 0
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=0.1)
            row = conn.execute("SELECT COUNT(*) FROM visits").fetchone()
            visit_count = row[0] if row else 0
            conn.close()
        except sqlite3.OperationalError:
            # Locked — we'll get the count during extraction via temp copy
            visit_count = -1

        browsers.append({
            "name": name,
            "path": path,
            "detected": True,
            "visit_count": visit_count,
            "manual_override": False,
        })

    return browsers


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    results = detect_browsers()
    if not results:
        print("No Chromium browsers detected.")
    for b in results:
        print(f"  {b['name']:>10}: {b['path']}  ({b['visit_count']} visits)")
