from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from config import IRRELEVANT_KEYWORDS, MAX_ITEMS, RELEVANCE_KEYWORDS, SPAM_KEYWORDS
from utils import make_content_hash, normalize_text

PROMO_KEYWORDS = ["webinar", "register", "sponsor", "conference", "ebook", "customer story"]
TECH_DENSITY_KEYWORDS = [
    "python",
    "duckdb",
    "llm",
    "rag",
    "openai",
    "data engineering",
    "analytics",
    "parquet",
    "api",
    "django",
    "airflow",
    "orchestration",
    "architecture",
    "infra",
]


def filter_items(items: list[dict[str, Any]], logger) -> list[dict[str, Any]]:
    unique_links: set[str] = set()
    unique_titles: set[str] = set()
    unique_hashes: set[str] = set()
    filtered: list[dict[str, Any]] = []
    deduped_count = 0

    for item in items:
        title = normalize_text(item.get("title", ""))
        link = canonicalize_url(item.get("url") or item.get("link", ""))
        summary = normalize_text(item.get("summary", ""))
        content = normalize_text(item.get("content", ""))
        source = normalize_text(item.get("source_name") or item.get("source", ""))
        item_hash = item.get("hash") or make_content_hash(title, link, content or summary)
        haystack = f"{title} {summary} {content} {' '.join(item.get('tags', []))} {source}".lower()

        if not title or not link:
            continue
        if title in unique_titles or link in unique_links or item_hash in unique_hashes:
            deduped_count += 1
            continue
        if is_spam(haystack) or is_irrelevant(haystack):
            continue
        if not summary and not content and "hacker news" not in source.lower():
            continue

        unique_titles.add(title)
        unique_links.add(link)
        unique_hashes.add(item_hash)

        scored_item = dict(item)
        scored_item["link"] = link
        scored_item["url"] = link
        scored_item["source"] = source
        scored_item["source_name"] = source
        scored_item["published"] = item.get("published_at") or item.get("published", "")
        scored_item["published_at"] = item.get("published_at") or item.get("published", "")
        scored_item["hash"] = item_hash
        scored_item["score"] = compute_relevance(haystack, scored_item)
        filtered.append(scored_item)

    filtered.sort(
        key=lambda item: (item.get("score", 0), item.get("published_at", "")),
        reverse=True,
    )

    limited = filtered[:MAX_ITEMS]
    logger.info("Itens apos filtros: %s | deduplicados: %s", len(limited), deduped_count)
    return limited


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    clean_query = "&".join(
        chunk for chunk in parts.query.split("&") if not chunk.startswith("utm_")
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, clean_query, ""))


def is_spam(text: str) -> bool:
    return any(keyword in text for keyword in SPAM_KEYWORDS)


def is_irrelevant(text: str) -> bool:
    return any(keyword in text for keyword in IRRELEVANT_KEYWORDS)


def compute_relevance(text: str, item: dict[str, Any]) -> int:
    score = int(item.get("priority", 0)) * 3
    for keyword, weight in RELEVANCE_KEYWORDS.items():
        if keyword in text:
            score += weight

    score += sum(2 for keyword in TECH_DENSITY_KEYWORDS if keyword in text)
    score += recency_score(item.get("published_at") or item.get("published", ""))

    content_length = len(normalize_text(item.get("content", "") or item.get("summary", "")))
    if content_length >= 600:
        score += 3
    elif content_length >= 250:
        score += 2
    elif content_length >= 120:
        score += 1

    if any(keyword in text for keyword in PROMO_KEYWORDS):
        score -= 4
    return score


def recency_score(value: str) -> int:
    if not value:
        return 0

    try:
        published_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 0

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)

    age = datetime.now(UTC) - published_at.astimezone(UTC)
    if age.days <= 1:
        return 4
    if age.days <= 3:
        return 3
    if age.days <= 7:
        return 2
    return 0
