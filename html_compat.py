from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

from utils import normalize_text


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


class FeedLinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "link":
            return

        attributes = {key.lower(): value for key, value in attrs}
        rel = (attributes.get("rel") or "").lower()
        feed_type = (attributes.get("type") or "").lower()
        href = (attributes.get("href") or "").strip()
        if "alternate" in rel and href and feed_type in {
            "application/rss+xml",
            "application/atom+xml",
            "application/xml",
            "text/xml",
        }:
            self.links.append(urljoin(self.base_url, href))


def html_to_text(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value or "")
    parser.close()
    return normalize_text(" ".join(parser.parts))


def discover_feed_links(html: str, base_url: str) -> list[str]:
    parser = FeedLinkParser(base_url)
    parser.feed(html or "")
    parser.close()
    return parser.links
