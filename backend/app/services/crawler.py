"""Simple website crawler — fetches pages and ingests as HTML documents."""

from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger("kb.crawler")

MAX_PAGES = 50


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = data.strip()
            if text:
                self._parts.append(text)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._parts)).strip()


def _same_domain(base: str, url: str) -> bool:
    return urlparse(base).netloc == urlparse(url).netloc


def crawl_site(start_url: str, max_depth: int = 1) -> list[tuple[str, str]]:
    """Return list of (url, plain_text) for crawled pages."""
    visited: set[str] = set()
    results: list[tuple[str, str]] = []
    queue: list[tuple[str, int]] = [(start_url, 0)]

    while queue and len(results) < MAX_PAGES:
        url, depth = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            req = Request(url, headers={"User-Agent": "tfKBPortalCrawler/1.0"})
            with urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    continue
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Crawl failed for %s: %s", url, exc)
            continue

        parser = _TextExtractor()
        parser.feed(html)
        text = parser.text()
        if text:
            results.append((url, text))

        if depth >= max_depth:
            continue

        for href in re.findall(r'href=["\']([^"\']+)["\']', html, re.I):
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            next_url = urljoin(url, href)
            if _same_domain(start_url, next_url) and next_url not in visited:
                queue.append((next_url, depth + 1))

    return results
