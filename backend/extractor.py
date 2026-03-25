"""Extract visits from Chromium SQLite databases. Read-only with copy-on-lock fallback."""

import atexit
import hashlib
import logging
import os
import shutil
import sqlite3
import tempfile

import pandas as pd

from detector import detect_browsers

logger = logging.getLogger(__name__)

_temp_copies: list[str] = []


def _cleanup_temp() -> None:
    """Remove temporary database copies on exit."""
    for path in _temp_copies:
        try:
            os.unlink(path)
            logger.debug("Cleaned up temp file: %s", path)
        except OSError:
            pass


atexit.register(_cleanup_temp)


def _open_readonly(path: str) -> sqlite3.Connection:
    """Open a History database read-only, falling back to a temp copy if locked."""
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=0.1)
        # Test that we can actually read
        conn.execute("SELECT 1 FROM urls LIMIT 1")
        return conn
    except sqlite3.OperationalError:
        logger.info("Database locked, copying to temp: %s", path)
        path_hash = hashlib.md5(path.encode()).hexdigest()[:12]
        tmp_path = os.path.join(tempfile.gettempdir(), f"bhv_{path_hash}.db")
        shutil.copy2(path, tmp_path)
        os.chmod(tmp_path, 0o600)
        _temp_copies.append(tmp_path)
        return sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)


_QUERY = """
    SELECT
        u.url,
        u.title,
        u.visit_count,
        u.typed_count,
        v.visit_time,
        v.from_visit
    FROM urls u
    JOIN visits v ON u.id = v.url
"""


def extract_browser(browser: dict) -> pd.DataFrame:
    """Extract visits from a single browser's History database."""
    path = browser["path"]
    name = browser["name"]

    try:
        conn = _open_readonly(path)
    except (sqlite3.Error, OSError) as e:
        logger.error("Cannot open %s (%s): %s", name, path, e)
        return pd.DataFrame()

    try:
        df = pd.read_sql_query(_QUERY, conn)
        conn.close()
    except (sqlite3.Error, pd.errors.DatabaseError) as e:
        logger.error("Query failed for %s: %s", name, e)
        conn.close()
        return pd.DataFrame()

    if df.empty:
        logger.info("%s: 0 visits", name)
        return df

    df = df.copy()
    df["browser"] = name
    logger.info("%s: %d visits", name, len(df))
    return df


def extract_all(browsers: list[dict] | None = None) -> pd.DataFrame:
    """Extract visits from all detected browsers. Returns concatenated DataFrame."""
    if browsers is None:
        browsers = detect_browsers()

    frames: list[pd.DataFrame] = []
    for browser in browsers:
        df = extract_browser(browser)
        if not df.empty:
            frames.append(df)

    if not frames:
        logger.warning("No visits extracted from any browser.")
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    browsers = detect_browsers()
    print(f"Detected {len(browsers)} browser(s)")
    df = extract_all(browsers)
    if not df.empty:
        for name, group in df.groupby("browser"):
            print(f"  {name}: {len(group)} visits")
        print(f"  Total: {len(df)} visits")
    else:
        print("  No visits extracted.")
