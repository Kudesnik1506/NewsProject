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
            "US foreign policy OR sanctions OR trade war OR geopolitics "
            "OR information operations OR propaganda OR NATO OR Ukraine"
        ),
        "newsapi_country": "us",
        "search_queries": [
            "US foreign policy today",
            "USA geopolitics latest news",
            "American sanctions trade war",
            "US information operations narratives propaganda",
            "White House State Department Pentagon announcement",
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
