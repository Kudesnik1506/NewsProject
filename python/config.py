"""
Конфигурация пайплайна: параметры модели и источники данных по странам.

Добавить новую страну = добавить блок в COUNTRIES, код агентов менять не нужно.
"""
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8096

COUNTRIES: dict[str, dict] = {
    "USA": {
        "rss_feeds": [
            "https://feeds.reuters.com/reuters/topNews",
            "https://feeds.apnews.com/rss/apf-topnews",
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://feeds.washingtonpost.com/rss/world",
            "https://www.politico.com/rss/politicopicks.xml",
            "https://feeds.bloomberg.com/politics/news.rss",
            "https://thehill.com/feed/",
            "http://rss.cnn.com/rss/cnn_topstories.rss",
        ],
        "newsapi_query": (
            "White House OR State Department OR Pentagon OR NATO "
            "OR US sanctions OR US foreign policy OR US military "
            "OR geopolitics OR trade war OR information war"
        ),
        "newsapi_country": "us",
        "search_queries": [
            "White House official statement today",
            "State Department Pentagon announcement geopolitics",
            "US government narrative information operations",
            "American foreign policy position official",
            "USA propaganda narrative allies adversaries",
        ],
        "telegram_channels": [],
    },
    # Template for adding new country:
    # "UK": {
    #     "rss_feeds": ["https://feeds.bbci.co.uk/news/world/rss.xml", ...],
    #     "newsapi_query": "UK foreign policy OR Brexit OR ...",
    #     "newsapi_country": "gb",
    #     "search_queries": ["UK geopolitics ...", ...],
    #     "telegram_channels": [],
    # },
}
