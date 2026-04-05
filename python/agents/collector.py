"""
Collector Agent — aggregates raw articles from all sources.
No Claude call needed: pure data collection and normalization.
"""
from datetime import date

from config import COUNTRIES
from models import Article
from sources.rss import fetch_rss
from sources.newsapi_source import fetch_newsapi
from sources.web_search import fetch_web_search
from sources.telegram_source import fetch_telegram


def run(country: str, target_date: date) -> list[dict]:
    """Собирает сырые статьи из всех настроенных источников для указанной страны и даты.

    Вызовы Claude не выполняются — только сбор и нормализация данных.
    Возвращает список словарей Article.
    """
    cfg = COUNTRIES.get(country)
    if not cfg:
        raise ValueError(f"Country '{country}' not found in config.py")

    print(f"[Collector] Fetching news for {country} on {target_date}...")
    articles: list[Article] = []

    # RSS
    rss_articles = fetch_rss(cfg["rss_feeds"], country)
    print(f"[Collector] RSS: {len(rss_articles)} articles")
    articles.extend(rss_articles)

    # NewsAPI
    newsapi_articles = fetch_newsapi(cfg["newsapi_query"], target_date, country)
    print(f"[Collector] NewsAPI: {len(newsapi_articles)} articles")
    articles.extend(newsapi_articles)

    # Web search
    web_articles = fetch_web_search(cfg["search_queries"], country)
    print(f"[Collector] Web search: {len(web_articles)} articles")
    articles.extend(web_articles)

    # Telegram (optional)
    if cfg.get("telegram_channels"):
        tg_articles = fetch_telegram(cfg["telegram_channels"], country)
        print(f"[Collector] Telegram: {len(tg_articles)} articles")
        articles.extend(tg_articles)

    # Remove articles with no title or url
    articles = [a for a in articles if a.title and a.url]

    print(f"[Collector] Total collected: {len(articles)} articles")
    return [a.model_dump(mode="json") for a in articles]
