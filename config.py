from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "radar.log"
SOURCES_FILE = BASE_DIR / "config" / "sources.yaml"
BLOG_SOURCES_RAW_FILE = RAW_DATA_DIR / "blog_sources_raw.json"
BLOG_DISCOVERY_CACHE_FILE = CACHE_DIR / "blog_feed_cache.json"

load_dotenv(BASE_DIR / ".env")

REQUEST_TIMEOUT = 15
MAX_ITEMS = 40
SUMMARY_MAX_LENGTH = 240
SUMMARY_TOP_ITEMS = 12
BLOG_SECTION_LIMIT = 12
BLOG_SUMMARY_MIN_LENGTH = 140
DEFAULT_SOURCE_SETTINGS = {
    "max_items_per_source": 10,
    "max_items_total": 80,
    "lookback_days": 7,
}

FEEDS = [
    {"name": "GitHub Blog", "url": "https://github.blog/feed/"},
    {"name": "GitHub Changelog", "url": "https://github.blog/changelog/feed/"},
    {"name": "DuckDB News", "url": "https://duckdb.org/news/index.xml"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
]

CATEGORIES = {
    "python": [
        "python",
        "pandas",
        "fastapi",
        "django",
        "flask",
        "pydata",
    ],
    "dados": [
        "data",
        "analytics",
        "analysis",
        "duckdb",
        "spark",
        "etl",
        "warehouse",
        "lakehouse",
        "sql",
        "dbt",
    ],
    "ia": [
        "ai",
        "artificial intelligence",
        "llm",
        "machine learning",
        "ml",
        "gpt",
        "openai",
        "ollama",
        "rag",
    ],
    "desenvolvimento": [
        "developer",
        "development",
        "programming",
        "software",
        "github",
        "open source",
        "devops",
        "automation",
        "release",
        "api",
    ],
    "bi": [
        "bi",
        "business intelligence",
        "dashboard",
        "power bi",
        "looker",
        "tableau",
        "metric",
        "reporting",
    ],
    "seguranca": [
        "security",
        "vulnerability",
        "cve",
        "auth",
        "authentication",
        "authorization",
        "token",
        "encryption",
        "malware",
        "breach",
    ],
}

GENERAL_CATEGORY = "geral"

SPAM_KEYWORDS = [
    "casino",
    "betting",
    "viagra",
    "crypto giveaway",
    "loan",
    "adult",
]

IRRELEVANT_KEYWORDS = [
    "hiring",
    "job opening",
    "merch",
    "swag",
]

RELEVANCE_KEYWORDS = {
    "python": 5,
    "duckdb": 5,
    "ai": 4,
    "analytics": 4,
    "github": 4,
    "automation": 3,
    "open source": 3,
}

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "Radar Tech Diario")


def smtp_configured() -> bool:
    required = [SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO]
    return all(required)
