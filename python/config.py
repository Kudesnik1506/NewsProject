"""
Конфигурация пайплайна: параметры модели и источники данных по странам.

Добавить новую страну = добавить блок в COUNTRIES, код агентов менять не нужно.
"""
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000

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
    "RUS": {
        "rss_feeds": [
            # Государственные/официальные источники
            "https://tass.com/rss/v2.xml",               # ТАСС (English)
            "https://www.rt.com/rss/",                    # RT (English)
            "https://ria.ru/export/rss2/archive/index.xml",  # РИА Новости
            "https://iz.ru/export/rss/all_exportfeed.xml",   # Известия
            # Деловые и аналитические
            "https://www.kommersant.ru/RSS/main.xml",     # Коммерсантъ
            "https://rbc.ru/rss/news",                    # РБК
            # Независимые (для баланса)
            "https://meduza.io/rss/en/all",               # Meduza (English)
            "https://www.themoscowtimes.com/rss",         # Moscow Times
        ],
        "newsapi_query": (
            "Putin OR Kremlin OR Russian government OR Путин OR Кремль "
            "OR российская экономика OR российская армия OR МИД России "
            "OR Russian domestic policy OR Госдума OR Russian foreign ministry"
        ),
        "newsapi_country": "ru",
        "search_queries": [
            "Кремль официальное заявление сегодня",
            "Путин решение внутренняя политика",
            "Россия экономика санкции импортозамещение",
            "российская армия военная операция официально",
            "МИД Россия дипломатия переговоры заявление",
        ],
        "telegram_channels": [],
    },
    "BRA": {
        "rss_feeds": [
            "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
            "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml",
            "https://agenciabrasil.ebc.com.br/rss/internacional/feed.xml",
            "https://feeds.folha.uol.com.br/mundo/rss091.xml",
            "https://feeds.folha.uol.com.br/poder/rss091.xml",
            "https://www.valor.com.br/rss/mundo",
            "https://feeds.reuters.com/reuters/topNews",
            "https://www.aljazeera.com/xml/rss/all.xml",
        ],
        "newsapi_query": (
            "Lula OR Brazil government OR Brazil foreign policy OR BRICS "
            "OR Brazil economy OR Brasilia OR Brazil diplomacy "
            "OR Amazon deforestation OR Brazil sanctions OR Petrobras"
        ),
        "newsapi_country": "br",
        "search_queries": [
            "Brazil Lula government official statement today",
            "Brazil foreign policy BRICS diplomacy latest",
            "Brazil economy trade sanctions geopolitics",
            "Brazil Amazon sovereignty international",
            "Brazil military security official announcement",
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
