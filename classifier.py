from __future__ import annotations

from collections import defaultdict
from typing import Any

from config import CATEGORIES, GENERAL_CATEGORY, SUMMARY_TOP_ITEMS


def classify_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []

    for index, item in enumerate(items):
        category = classify_item(item)
        enriched = dict(item)
        enriched["category"] = category
        base_text = enriched.get("content") or enriched.get("summary", "")
        enriched["ai_summary"] = summarize(base_text) if index < SUMMARY_TOP_ITEMS else summarize(enriched.get("summary", ""))
        classified.append(enriched)

    return classified


def classify_item(item: dict[str, Any]) -> str:
    explicit_category = item.get("source_category") or item.get("category")
    if explicit_category:
        return explicit_category

    text = " ".join(
        [
            item.get("title", ""),
            item.get("summary", ""),
            item.get("content", ""),
            " ".join(item.get("tags", [])),
            item.get("source_name", "") or item.get("source", ""),
        ]
    ).lower()

    best_category = GENERAL_CATEGORY
    best_score = 0

    for category, keywords in CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category


def summarize(text: str) -> str:
    return text.strip()


def group_by_category(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[item.get("category", GENERAL_CATEGORY)].append(item)
    return dict(grouped)
