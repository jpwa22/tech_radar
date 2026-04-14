from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import Any

import requests

from config import FEEDS, REQUEST_TIMEOUT
from feed_compat import parse_feed
from html_compat import html_to_text
from utils import make_content_hash, normalize_text, safe_trim


def fetch_all_feeds(logger) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    session = requests.Session()
    headers = {"User-Agent": "TechRadar/1.0 (+https://localhost)"}

    for feed in FEEDS:
        try:
            logger.info("Lendo feed: %s", feed["url"])
            response = session.get(feed["url"], timeout=REQUEST_TIMEOUT, headers=headers)
            response.raise_for_status()
            parsed = parse_feed(response.content)
            parsed_items = parse_feed_entries(feed["name"], parsed.entries)
            items.extend(parsed_items)
            logger.info("Feed %s retornou %s itens", feed["name"], len(parsed_items))
        except Exception as exc:
            logger.exception("Falha ao ler feed %s: %s", feed["url"], exc)

    return items


def parse_feed_entries(source_name: str, entries: list[Any]) -> list[dict[str, Any]]:
    parsed_items: list[dict[str, Any]] = []

    for entry in entries:
        title = normalize_text(entry.get("title", ""))
        link = entry.get("link", "").strip()
        summary = extract_summary(entry)
        published = format_published(entry)
        tags = extract_tags(entry)

        parsed_items.append(
            {
                "source": source_name,
                "source_name": source_name,
                "source_type": "rss",
                "collection": "core_feeds",
                "title": title,
                "author": normalize_text(entry.get("author", "")),
                "link": link,
                "url": link,
                "summary": summary,
                "content": summary,
                "published": published,
                "published_at": published,
                "tags": tags,
                "language": "",
                "priority": 0,
                "hash": make_content_hash(title, link, summary),
            }
        )

    return parsed_items


def extract_summary(entry: Any) -> str:
    raw_summary = entry.get("summary") or entry.get("description") or ""
    text = html_to_text(raw_summary)
    return safe_trim(normalize_text(text), 400)


def format_published(entry: Any) -> str:
    raw_value = (
        entry.get("published")
        or entry.get("updated")
        or entry.get("created")
        or ""
    )
    if not raw_value:
        return ""

    try:
        return parsedate_to_datetime(raw_value).isoformat()
    except Exception:
        return normalize_text(raw_value)


def extract_tags(entry: Any) -> list[str]:
    tags = entry.get("tags", [])
    cleaned = []
    for tag in tags:
        term = normalize_text(getattr(tag, "term", "") or tag.get("term", ""))
        if term:
            cleaned.append(term)
    return cleaned
