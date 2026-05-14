"""
scraper.py — Respectful web scraper with noise filtering
"""

from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/2.0; +https://github.com/research-agent)"
}
DELAY      = 1.0   # seconds between requests
TIMEOUT    = 15    # request timeout
MAX_CHARS  = 50_000

_NOISE_TAGS = ["script", "style", "nav", "footer", "header", "form",
               "noscript", "aside", "advertisement", "figure"]
_CONTENT_TAGS = ["p", "h1", "h2", "h3", "h4", "h5", "h6",
                 "li", "blockquote", "article", "section", "main"]


class WebScraper:
    def __init__(self):
        self._last_request = 0.0

    def scrape(self, url: str) -> list[Document]:
        self._rate_limit()
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else urlparse(url).netloc

        # Remove noise
        for tag in soup(_NOISE_TAGS):
            tag.decompose()

        # Extract meaningful content
        parts = []
        for tag in soup.find_all(_CONTENT_TAGS):
            text = tag.get_text(" ", strip=True)
            if len(text) > 40:
                parts.append(text)

        content = "\n\n".join(parts)

        # Fallback: body text
        if len(content) < 200:
            body = soup.find("body")
            content = body.get_text(" ", strip=True) if body else soup.get_text(" ", strip=True)

        content = content[:MAX_CHARS]

        if not content.strip():
            logger.warning(f"No content extracted from {url}")
            return []

        logger.info(f"Successfully scraped {len(content)} chars from {url}")
        return [Document(
            page_content=content,
            metadata={
                "source": url,
                "title": title,
                "source_type": "web",
                "url": url,
            }
        )]

    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < DELAY:
            time.sleep(DELAY - elapsed)
        self._last_request = time.time()
