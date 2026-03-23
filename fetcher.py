"""
Fetches and deduplicates articles from configured RSS feeds.
Returns the N most recent articles across all feeds.
"""

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from config import FEEDS, LOOKBACK_DAYS, MAX_ARTICLES

logger = logging.getLogger(__name__)


def _parse_date(entry) -> datetime:
    """Best-effort parse of an RSS entry's published date."""
    for field in ("published", "updated"):
        raw = entry.get(field)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _fetch_feed(feed_cfg: dict) -> list[dict]:
    """Parse a single RSS feed and return a list of article dicts."""
    articles = []
    try:
        parsed = feedparser.parse(feed_cfg["url"])
        for entry in parsed.entries:
            link = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            if not link or not title:
                continue
            summary = entry.get("summary", entry.get("description", "")).strip()
            articles.append(
                {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published": _parse_date(entry),
                    "source": feed_cfg["name"],
                }
            )
    except Exception as exc:
        logger.warning("Failed to fetch feed %s: %s", feed_cfg["name"], exc)
    return articles


def _fetch_full_text(url: str) -> str:
    """Attempt to fetch the full article body from a URL."""
    try:
        resp = httpx.get(url, timeout=8, follow_redirects=True,
                         headers={"User-Agent": "FintechTracker/1.0"})
        resp.raise_for_status()
        import re
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000]
    except Exception:
        return ""


def fetch_articles() -> list[dict]:
    """
    Fetch articles from all configured RSS feeds.
    Deduplicates by URL, sorts newest-first, returns top MAX_ARTICLES.
    """
    seen_urls: set[str] = set()
    all_articles: list[dict] = []

    for feed_cfg in FEEDS:
        for article in _fetch_feed(feed_cfg):
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                all_articles.append(article)

    # Sort newest first, then filter to past LOOKBACK_DAYS days
    all_articles.sort(key=lambda a: a["published"], reverse=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    all_articles = [a for a in all_articles if a["published"] >= cutoff]
    top = all_articles[:MAX_ARTICLES]

    # Try to enrich with full text (best-effort)
    for article in top:
        full_text = _fetch_full_text(article["url"])
        article["article_text"] = full_text or article["summary"]

    return top
