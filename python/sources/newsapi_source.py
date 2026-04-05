"""Источник данных NewsAPI. Требует переменную окружения NEWSAPI_KEY."""
import os
from datetime import date, datetime
from newsapi import NewsApiClient
from models import Article


def fetch_newsapi(query: str, target_date: date, country: str) -> list[Article]:
    """Получает статьи из NewsAPI по запросу и дате. Возвращает [] если ключ не задан."""
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print("[NewsAPI] NEWSAPI_KEY not set, skipping.")
        return []

    client = NewsApiClient(api_key=api_key)
    try:
        response = client.get_everything(
            q=query,
            language="en",
            from_param=target_date.isoformat(),
            to=target_date.isoformat(),
            sort_by="relevancy",
            page_size=30,
        )
        articles = []
        for item in response.get("articles", []):
            articles.append(Article(
                title=(item.get("title") or "").strip(),
                url=item.get("url") or "",
                source=(item.get("source") or {}).get("name") or "",
                content=(item.get("description") or "")[:600],
                published_at=_parse_date(item.get("publishedAt")),
                country=country,
            ))
        return articles
    except Exception as e:
        print(f"[NewsAPI] Error: {e}")
        return []


def _parse_date(date_str: str | None) -> datetime | None:
    """Разбирает строку даты ISO 8601 в объект datetime."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None
