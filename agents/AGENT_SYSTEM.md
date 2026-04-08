# NewsProject: Техническая спецификация системы агентов

Этот документ — справочник разработчика: схемы данных, паттерны реализации, конфигурация источников. Для обзора архитектуры и редакционных концепций — см. `CLAUDE.md` в корне проекта. Для промптов каждого агента — см. отдельные `.md` файлы в этой папке.

---

## Пайплайн и инструменты оркестратора

```
Orchestrator (main.py)
│
├── [tool] collect_news(country, date)        → Collector Agent
├── [tool] filter_news(articles)              → Filter Agent
├── [tool] verify_news(articles)              → Verifier Agent
├── [tool] analyze_news(articles)             → Analyst Agent
└── [tool] generate_report(stories, country, date) → Reporter Agent
                                                   └── reports/YYYY-MM-DD_{COUNTRY}.md
```

Каждый `tool` — вызов соответствующего Python-модуля, который делает собственный запрос к Claude API.

---

## Модели данных — `models.py`

```python
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class Article(BaseModel):
    title: str
    url: str
    source: str                           # Reuters, AP, NYT, и т.д.
    content: str = ""                     # сниппет или полный текст
    published_at: Optional[datetime] = None
    country: str = "USA"
    relevance_score: float = 0.0          # 0–10, заполняет Filter Agent
    verification_status: str = "PENDING"  # VERIFIED / UNVERIFIED / DISPUTED
    source_count: int = 1                 # сколько источников подтверждают
    verification_note: str = ""           # обоснование статуса от Verifier


class Scenario(BaseModel):
    description: str
    probability: str  # "высокая" / "средняя" / "низкая"


class AnalyzedStory(BaseModel):
    article: Article
    what_happened: str
    interests: str
    power_shift: str
    psychological_dimension: str          # механизм воздействия, нарративы, целевая аудитория
    scenarios: list[Scenario]
    cluster: str  # P1/P2/A1/A2/E1/E2/I1/I2 — см. agents/paei_model.md


class Report(BaseModel):
    date: date
    country: str
    stories: list[AnalyzedStory]
    total_sources: int = 0
    verified_count: int = 0
    file_path: str = ""
```

---

## Конфигурация источников — `config.py`

```python
COUNTRIES = {
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
        "newsapi_query": "US foreign policy OR sanctions OR trade war OR geopolitics",
        "newsapi_country": "us",
        "search_queries": [
            "US foreign policy today",
            "USA geopolitics latest",
            "American sanctions trade war",
            "US information operations narratives",
        ],
        "telegram_channels": [],  # добавить при необходимости
    },
    # Шаблон для добавления страны:
    # "UK": {
    #     "rss_feeds": [...],
    #     "newsapi_query": "...",
    #     "newsapi_country": "gb",
    #     "search_queries": [...],
    #     "telegram_channels": [],
    # }
}
```

Добавить страну = добавить блок в `COUNTRIES`. Код агентов не меняется.

---

## Паттерн реализации агента

Каждый субагент реализован по одному паттерну:

```python
import anthropic
import json
from models import Article  # нужные модели

client = anthropic.Anthropic()

SYSTEM_PROMPT = """..."""  # содержимое из agents/<agent>.md


def run(input_data: list[dict]) -> list[dict]:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                articles_json=json.dumps(input_data, ensure_ascii=False, indent=2)
            )
        }]
    )
    return json.loads(response.content[0].text)
```

---

## Паттерн оркестратора (tool_use)

```python
tools = [
    {
        "name": "collect_news",
        "description": "Собирает сырые новости из RSS, NewsAPI и веб-поиска",
        "input_schema": {
            "type": "object",
            "properties": {
                "country": {"type": "string"},
                "date": {"type": "string"}
            },
            "required": ["country", "date"]
        }
    },
    # ... остальные инструменты
]

tool_handlers = {
    "collect_news": collector.run,
    "filter_news": filter_agent.run,
    "verify_news": verifier.run,
    "analyze_news": analyst.run,
    "generate_report": reporter.run,
}
```

---

## Файловая структура

```
NewsProject/
├── CLAUDE.md                        # Гид для Claude Code
├── run.bat                          # Точка запуска (Windows)
├── requirements.txt
├── .env                             # API ключи (не в git)
├── .env.example
├── agents/                          # Промпты агентов (только .md)
│   ├── AGENT_SYSTEM.md              # Этот файл: техспецификация
│   ├── orchestrator.md
│   ├── collector.md
│   ├── filter_agent.md
│   ├── verifier.md
│   ├── analyst.md
│   └── reporter.md
├── python/                          # Весь Python-код
│   ├── main.py                      # Оркестратор + точка входа
│   ├── config.py                    # Конфигурация источников и стран
│   ├── models.py                    # Pydantic-модели
│   ├── utils.py                     # Утилиты (extract_json и др.)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── collector.py
│   │   ├── filter_agent.py
│   │   ├── verifier.py
│   │   ├── analyst.py
│   │   └── reporter.py
│   └── sources/
│       ├── __init__.py
│       ├── rss.py                   # feedparser
│       ├── newsapi_source.py        # newsapi-python
│       ├── web_search.py            # tavily-python
│       └── telegram_source.py      # telethon (опционально)
└── reports/                         # Выходные .md файлы
```

---

## Пороги и правила пайплайна

| Агент | Правило |
|-------|---------|
| Filter | Порог по умолчанию: `relevance_score ≥ 5`. Строгий: `≥ 7`. Широкий (дефицит новостей): `≥ 4` |
| Verifier | `VERIFIED` только при 3+ независимых источниках |
| Analyst | Анализировать только статьи с `relevance_score ≥ 6` и `verification_status != DISPUTED`. DISPUTED — исключить. Возвращает JSON с полями `stories` и `state_diagnosis` (диагноз по 8 измерениям PAEI×Jung). |
| Reporter | Дайджест в 3 части: VERIFIED — полный анализ по 8 кластерам; UNVERIFIED — краткий список "На радаре"; Диагноз состояния государства — таблица 8 измерений + дисбалансы + вывод. DISPUTED не включается. Максимум 10 историй, топ по `relevance_score` |

---

## Запуск

Первый раз — создать окружение и установить зависимости:

```bash
D:/Projects/Python/python.exe -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Запуск через `run.bat` (Windows, без активации venv):

```bash
run.bat --country USA
run.bat --country USA --fast
run.bat --country USA --topic "торговые тарифы"
```

Или с активацией venv напрямую:

```bash
source .venv/Scripts/activate
python python/main.py --country USA --fast
```

Выход: `reports/YYYY-MM-DD_USA.md`
