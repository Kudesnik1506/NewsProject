from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class Article(BaseModel):
    title: str
    url: str
    source: str
    content: str = ""
    published_at: Optional[datetime] = None
    country: str = "USA"
    relevance_score: float = 0.0
    verification_status: str = "PENDING"  # VERIFIED / UNVERIFIED / DISPUTED
    source_count: int = 1
    verification_note: str = ""


class Scenario(BaseModel):
    description: str
    probability: str  # "высокая" / "средняя" / "низкая"


class AnalyzedStory(BaseModel):
    article: Article
    what_happened: str
    interests: str
    power_shift: str
    psychological_dimension: str
    scenarios: list[Scenario]
    cluster: str  # геополитика / торговля / военное / дипломатия / экономика / геопсихология


class Report(BaseModel):
    date: date
    country: str
    stories: list[AnalyzedStory]
    total_sources: int = 0
    verified_count: int = 0
    file_path: str = ""
