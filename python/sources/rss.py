import feedparser
from datetime import datetime
from models import Article


def fetch_rss(feeds: list[str], country: str) -> list[Article]:
    articles = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get("title", _domain(feed_url))
            for entry in feed.entries[:10]:
                content = entry.get("summary", entry.get("description", ""))
                articles.append(Article(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    source=source_name,
                    content=content[:600],
                    published_at=_parse_date(entry),
                    country=country,
                ))
        except Exception as e:
            print(f"[RSS] Error fetching {feed_url}: {e}")
    return articles


def _parse_date(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except Exception:
            pass
    return None


def _domain(url: str) -> str:
    try:
        return url.split("/")[2]
    except IndexError:
        return url
