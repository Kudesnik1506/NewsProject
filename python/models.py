"""
Pydantic-модели данных, общие для всех агентов пайплайна.

Данные передаются между агентами как plain dict (model_dump). Модели используются
для валидации и документирования типов на границах сбора и анализа.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class Article(BaseModel):
    """Одна новостная статья, проходящая через пайплайн.

    Заполняется Collector, оценивается Filter, верифицируется Verifier.
    """

    title: str
    url: str
    source: str
    content: str = ""
    published_at: Optional[datetime] = None
    country: str = "USA"
    relevance_score: float = 0.0          # 0–10, assigned by Filter
    verification_status: str = "PENDING"  # VERIFIED / UNVERIFIED / DISPUTED
    source_count: int = 1                 # number of independent sources confirming the event
    verification_note: str = ""           # one-sentence rationale from Verifier


class Scenario(BaseModel):
    """Один возможный сценарий развития событий, формируемый Analyst."""

    description: str
    probability: str  # "высокая" / "средняя" / "низкая"


class AnalyzedStory(BaseModel):
    """Полный анализ одной статьи по редакционной формуле 5 вопросов, результат работы Analyst."""

    article: Article
    what_happened: str           # факты: кто, что, когда, где
    interests: str               # ключевые игроки и их мотивации
    power_shift: str             # конкретные сдвиги в балансе сил
    psychological_dimension: str # механизм воздействия, целевая аудитория, нарративы
    scenarios: list[Scenario]
    cluster: str  # геополитика / торговля / военное / дипломатия / экономика / геопсихология


class Report(BaseModel):
    """Итог запуска пайплайна — метаданные вокруг сгенерированного дайджеста."""

    date: date
    country: str
    stories: list[AnalyzedStory]
    total_sources: int = 0   # количество статей до фильтрации
    verified_count: int = 0  # статьи со статусом VERIFIED
    file_path: str = ""      # путь к сохранённому Markdown-дайджесту
