from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from xml.etree import ElementTree as ET


def parse_feed(content: bytes) -> Any:
    try:
        import feedparser  # type: ignore

        return feedparser.parse(content)
    except ModuleNotFoundError:
        return SimpleNamespace(entries=parse_feed_entries_fallback(content))


def parse_feed_entries_fallback(content: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    tag = strip_namespace(root.tag)
    if tag == "rss":
        return parse_rss(root)
    if tag == "feed":
        return parse_atom(root)
    return []


def parse_rss(root: ET.Element) -> list[dict[str, Any]]:
    channel = root.find("channel")
    if channel is None:
        return []

    entries = []
    for item in channel.findall("item"):
        entries.append(
            {
                "title": find_text(item, "title"),
                "link": find_text(item, "link"),
                "summary": find_text(item, "description"),
                "description": find_text(item, "description"),
                "published": find_text(item, "pubDate"),
                "author": find_text(item, "author"),
                "tags": [{"term": category.text or ""} for category in item.findall("category")],
            }
        )
    return entries


def parse_atom(root: ET.Element) -> list[dict[str, Any]]:
    entries = []
    for entry in root.findall(ns_tag("entry")):
        link = ""
        for candidate in entry.findall(ns_tag("link")):
            href = candidate.attrib.get("href", "")
            rel = candidate.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                link = href
                break

        entries.append(
            {
                "title": find_text(entry, ns_tag("title")),
                "link": link,
                "summary": find_text(entry, ns_tag("summary")),
                "description": find_text(entry, ns_tag("summary")),
                "published": find_text(entry, ns_tag("published")) or find_text(entry, ns_tag("updated")),
                "updated": find_text(entry, ns_tag("updated")),
                "author": find_nested_text(entry, ns_tag("author"), ns_tag("name")),
                "tags": [{"term": category.attrib.get("term", "")} for category in entry.findall(ns_tag("category"))],
            }
        )
    return entries


def ns_tag(name: str) -> str:
    return f"{{http://www.w3.org/2005/Atom}}{name}"


def strip_namespace(value: str) -> str:
    return value.split("}", 1)[-1]


def find_text(element: ET.Element, tag: str) -> str:
    found = element.find(tag)
    return (found.text or "").strip() if found is not None and found.text else ""


def find_nested_text(element: ET.Element, parent_tag: str, child_tag: str) -> str:
    parent = element.find(parent_tag)
    if parent is None:
        return ""
    return find_text(parent, child_tag)
