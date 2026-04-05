import os
from models import Article


def fetch_web_search(queries: list[str], country: str) -> list[Article]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("[WebSearch] TAVILY_API_KEY not set, skipping.")
        return []

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
    except ImportError:
        print("[WebSearch] tavily-python not installed, skipping.")
        return []

    articles = []
    for query in queries:
        try:
            results = client.search(query=query, max_results=5, search_depth="basic")
            for item in results.get("results", []):
                url = item.get("url", "")
                articles.append(Article(
                    title=item.get("title", "").strip(),
                    url=url,
                    source=_domain(url),
                    content=(item.get("content") or "")[:600],
                    published_at=None,
                    country=country,
                ))
        except Exception as e:
            print(f"[WebSearch] Error for '{query}': {e}")
    return articles


def _domain(url: str) -> str:
    try:
        return url.split("/")[2]
    except IndexError:
        return url
