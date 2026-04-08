"""
Collector Agent — aggregates raw articles from all sources.
No Claude call needed: pure data collection and normalization.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from config import COUNTRIES
from models import Article
from sources.rss import fetch_rss
from sources.newsapi_source import fetch_newsapi
from sources.web_search import fetch_web_search
from sources.telegram_source import fetch_telegram


def run(country: str, target_date: date, date_from: date | None = None) -> list[dict]:
    """Собирает сырые статьи из всех настроенных источников для указанной страны и даты (или диапазона).

    date_from задаёт начало диапазона для NewsAPI (по умолчанию = target_date).
    Источники запускаются параллельно (ThreadPoolExecutor).
    Вызовы Claude не выполняются — только сбор и нормализация данных.
    Возвращает список словарей Article.
    """
    cfg = COUNTRIES.get(country)
    if not cfg:
        raise ValueError(f"Country '{country}' not found in config.py")

    if date_from and date_from < target_date:
        print(f"[Collector] Fetching news for {country} from {date_from} to {target_date}...")
    else:
        print(f"[Collector] Fetching news for {country} on {target_date}...")

    tasks = {
        "RSS":        lambda: fetch_rss(cfg["rss_feeds"], country),
        "NewsAPI":    lambda: fetch_newsapi(cfg["newsapi_query"], target_date, country, date_from=date_from),
        "Web search": lambda: fetch_web_search(cfg["search_queries"], country),
    }
    if cfg.get("telegram_channels"):
        tasks["Telegram"] = lambda: fetch_telegram(cfg["telegram_channels"], country)

    articles: list[Article] = []
    with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
        futures = {ex.submit(fn): name for name, fn in tasks.items()}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                result = fut.result()
                print(f"[Collector] {name}: {len(result)} articles")
                articles.extend(result)
            except Exception as e:
                print(f"[Collector] {name} failed: {e}")

    # Remove articles with no title or url
    articles = [a for a in articles if a.title and a.url]

    print(f"[Collector] Total collected: {len(articles)} articles")
    return [a.model_dump(mode="json") for a in articles]
