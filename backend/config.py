"""All BHV thresholds and constants — single source of truth."""

# Session detection
SESSION_GAP_S: int = 900  # 15 minutes = new session

# Duration inference
DURATION_CAP_S: int = 1200  # 20 minutes max per single visit

# Rabbit hole minimums
RABBIT_MIN_VISITS: int = 4
RABBIT_MIN_DURATION_S: int = 600  # 10 minutes
RABBIT_MIN_DOMAINS: int = 2

# AI categorization
AI_BATCH_SIZE: int = 50

# Category taxonomy (order matters for display)
CATEGORY_TAXONOMY: list[str] = [
    "work",
    "research",
    "social",
    "news",
    "entertainment",
    "shopping",
    "devtools",
    "uncategorized",
]

# Focus vs distraction grouping for productivity curve
FOCUS_CATEGORIES: set[str] = {"work", "research", "devtools"}
DISTRACTION_CATEGORIES: set[str] = {"social", "entertainment"}

# Chrome timestamp epoch offset (microseconds since 1601-01-01 → Unix seconds)
CHROME_EPOCH_OFFSET: int = 11_644_473_600

# Paths
DATA_DIR: str = "data"
ANALYTICS_CACHE_FILE: str = "data/analytics_cache.json"
CATEGORIES_FILE: str = "data/categories.json"
SETTINGS_FILE: str = "data/settings.json"

# Cache staleness
CACHE_MAX_AGE_S: int = 86400  # 24 hours
