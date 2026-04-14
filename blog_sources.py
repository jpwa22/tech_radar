from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import requests
import yaml

from config import (
    BLOG_DISCOVERY_CACHE_FILE,
    BLOG_SOURCES_RAW_FILE,
    BLOG_SUMMARY_MIN_LENGTH,
    DEFAULT_SOURCE_SETTINGS,
    REQUEST_TIMEOUT,
    SOURCES_FILE,
)
from feed_compat import parse_feed
from filters import canonicalize_url
from html_compat import discover_feed_links, html_to_text
from utils import make_content_hash, normalize_text, safe_trim

USER_AGENT = "TechRadar/1.0 (+https://localhost)"
PROMO_KEYWORDS = ("register", "webinar", "event", "conference", "sponsor", "customers")


def fetch_blog_sources(logger) -> list[dict[str, Any]]:
    settings, sources = load_source_catalog(logger)
    if not sources:
        logger.info("Nenhuma fonte tecnica configurada em %s", SOURCES_FILE)
        return []

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    discovery_cache = load_discovery_cache()
    collected: list[dict[str, Any]] = []
    raw_payload: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "settings": settings,
        "sources": [],
    }

    for source in sources:
        source_name = source.get("name", "Fonte tecnica")
        try:
            feed_url = resolve_feed_url(source, session, discovery_cache, logger)
            if not feed_url:
                logger.warning("Fonte %s sem feed descoberto", source_name)
                raw_payload["sources"].append({"name": source_name, "status": "missing_feed", "items": []})
                continue

            logger.info("Coletando fonte tecnica %s: %s", source_name, feed_url)
            parsed = fetch_parsed_feed(feed_url, session)
            normalized_items = normalize_source_entries(source, parsed.entries, session, settings)
            collected.extend(normalized_items)
            raw_payload["sources"].append(
                {
                    "name": source_name,
                    "feed_url": feed_url,
                    "status": "ok",
                    "item_count": len(normalized_items),
                    "items": normalized_items,
                }
            )
            logger.info("Fonte tecnica %s retornou %s itens", source_name, len(normalized_items))
        except Exception as exc:
            logger.exception("Falha ao processar fonte tecnica %s: %s", source_name, exc)
            raw_payload["sources"].append({"name": source_name, "status": "error", "error": str(exc), "items": []})

    save_discovery_cache(discovery_cache, logger)
    save_raw_payload(raw_payload, logger)
    max_items_total = int(settings.get("max_items_total", DEFAULT_SOURCE_SETTINGS["max_items_total"]))
    return collected[:max_items_total]


def load_source_catalog(logger) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not SOURCES_FILE.exists():
        logger.warning("Arquivo de fontes tecnicas nao encontrado: %s", SOURCES_FILE)
        return dict(DEFAULT_SOURCE_SETTINGS), []

    payload = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}
    settings = dict(DEFAULT_SOURCE_SETTINGS)
    settings.update(payload.get("settings") or {})

    enabled_sources = []
    for source in payload.get("sources") or []:
        if source.get("enabled", True):
            enabled_sources.append(source)
    return settings, enabled_sources


def load_discovery_cache() -> dict[str, str]:
    if not BLOG_DISCOVERY_CACHE_FILE.exists():
        return {}

    try:
        return json.loads(BLOG_DISCOVERY_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_discovery_cache(cache: dict[str, str], logger) -> None:
    BLOG_DISCOVERY_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        BLOG_DISCOVERY_CACHE_FILE.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.exception("Falha ao salvar cache de discovery: %s", exc)


def save_raw_payload(payload: dict[str, Any], logger) -> None:
    BLOG_SOURCES_RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        BLOG_SOURCES_RAW_FILE.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Payload bruto de blogs salvo em %s", BLOG_SOURCES_RAW_FILE)
    except Exception as exc:
        logger.exception("Falha ao salvar bruto de blogs: %s", exc)


def resolve_feed_url(source: dict[str, Any], session: requests.Session, cache: dict[str, str], logger) -> str:
    if source.get("feed_url"):
        return source["feed_url"].strip()

    site_url = source.get("site_url", "").strip()
    if not site_url:
        return ""

    if site_url in cache:
        return cache[site_url]

    response = get_with_retry(session, site_url)
    response.raise_for_status()
    for resolved in discover_feed_links(response.text, site_url):
        if resolved:
            cache[site_url] = resolved
            logger.info("Feed descoberto para %s: %s", source.get("name", site_url), resolved)
            return resolved

    return ""


def fetch_parsed_feed(feed_url: str, session: requests.Session) -> Any:
    response = get_with_retry(session, feed_url)
    response.raise_for_status()
    return parse_feed(response.content)


def get_with_retry(session: requests.Session, url: str) -> requests.Response:
    last_exc: Exception | None = None
    for _ in range(2):
        try:
            return session.get(url, timeout=REQUEST_TIMEOUT)
        except Exception as exc:
            last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Falha ao carregar {url}")


def normalize_source_entries(
    source: dict[str, Any],
    entries: list[Any],
    session: requests.Session,
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    lookback_days = int(settings.get("lookback_days", DEFAULT_SOURCE_SETTINGS["lookback_days"]))
    max_items_per_source = int(
        source.get("max_items_per_source", settings.get("max_items_per_source", DEFAULT_SOURCE_SETTINGS["max_items_per_source"]))
    )
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    normalized_items: list[dict[str, Any]] = []

    for entry in entries:
        published_dt = parse_entry_datetime(entry)
        if published_dt and published_dt < cutoff:
            continue

        title = normalize_text(entry.get("title", ""))
        url = canonicalize_url(entry.get("link", "").strip())
        summary = extract_entry_summary(entry)
        tags = extract_entry_tags(entry)
        author = normalize_text(entry.get("author", ""))
        content = summary

        if url and len(summary) < BLOG_SUMMARY_MIN_LENGTH:
            article_text = extract_article_content(url, session)
            if article_text:
                content = article_text
                if len(summary) < 40:
                    summary = safe_trim(article_text, 400)

        item_hash = make_content_hash(title, url, content)
        normalized_items.append(
            {
                "source": source.get("name", "Fonte tecnica"),
                "source_name": source.get("name", "Fonte tecnica"),
                "source_type": source.get("kind", "rss"),
                "collection": "blog_sources",
                "title": title,
                "author": author,
                "published": published_dt.isoformat() if published_dt else "",
                "published_at": published_dt.isoformat() if published_dt else "",
                "link": url,
                "url": url,
                "summary": summary,
                "content": content,
                "language": source.get("language", ""),
                "tags": tags,
                "category": source.get("category", ""),
                "source_category": source.get("category", ""),
                "priority": int(source.get("priority", 0)),
                "score": 0,
                "hash": item_hash,
                "site_url": source.get("site_url", ""),
                "feed_url": source.get("feed_url", ""),
            }
        )
        if len(normalized_items) >= max_items_per_source:
            break

    return normalized_items


def parse_entry_datetime(entry: Any) -> datetime | None:
    raw_value = entry.get("published") or entry.get("updated") or entry.get("created") or ""
    if not raw_value:
        return None

    try:
        parsed = parsedate_to_datetime(raw_value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except Exception:
        return None


def extract_entry_summary(entry: Any) -> str:
    raw_summary = entry.get("summary") or entry.get("description") or ""
    text = html_to_text(raw_summary)
    return safe_trim(normalize_text(text), 400)


def extract_entry_tags(entry: Any) -> list[str]:
    tags = []
    for tag in entry.get("tags", []):
        term = normalize_text(getattr(tag, "term", "") or tag.get("term", ""))
        if term:
            tags.append(term)
    return tags


def extract_article_content(url: str, session: requests.Session) -> str:
    try:
        response = get_with_retry(session, url)
        response.raise_for_status()
    except Exception:
        return ""

    text = html_to_text(response.text)
    if any(keyword in text.lower() for keyword in PROMO_KEYWORDS) and len(text) < 200:
        return ""
    return safe_trim(text, 2000)
