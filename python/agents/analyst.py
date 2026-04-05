"""
Analyst Agent — geostrategic and geopsychological analysis via Claude.
"""
import json
import anthropic

from config import MODEL
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("analyst")
USER_PROMPT = load_user_prompt("analyst")


def run(articles: list[dict]) -> list[dict]:
    """Анализирует топ-10 статей (relevance_score >= 6) через Claude по формуле 5 вопросов.

    Возвращает список словарей AnalyzedStory с геостратегическим
    и геопсихологическим разбором каждой истории.
    """
    eligible = [
        a for a in articles
        if a.get("relevance_score", 0) >= 6
        and a.get("verification_status") != "DISPUTED"
    ]
    eligible = sorted(eligible, key=lambda a: a.get("relevance_score", 0), reverse=True)[:10]
    disputed_count = sum(1 for a in articles if a.get("verification_status") == "DISPUTED")
    if disputed_count:
        print(f"[Analyst] Skipped {disputed_count} DISPUTED articles (excluded from digest)")
    print(f"[Analyst] Analyzing {len(eligible)} articles (of {len(articles)} total, top-10)...")

    if not eligible:
        print("[Analyst] No eligible articles (relevance_score >= 6)")
        return []

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                articles_json=json.dumps(eligible, ensure_ascii=False, indent=2)
            )
        }]
    )

    result = extract_json(response.content[0].text)
    print(f"[Analyst] Produced {len(result)} analyzed stories")
    return result
