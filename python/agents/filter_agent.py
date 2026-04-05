"""
Filter Agent — deduplication, relevance scoring, and editorial filtering via Claude.
"""
import json
import anthropic

from config import MODEL, MAX_TOKENS
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("filter_agent")
USER_PROMPT = load_user_prompt("filter_agent")


def run(articles: list[dict]) -> list[dict]:
    """Фильтрует и оценивает статьи через Claude.

    Возвращает только статьи с relevance_score >= 5, дедуплицированные
    и отсортированные по убыванию оценки.
    """
    print(f"[Filter] Processing {len(articles)} articles...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                articles_json=json.dumps(articles, ensure_ascii=False, indent=2)
            )
        }]
    )

    result = extract_json(response.content[0].text)
    print(f"[Filter] Filtered to {len(result)} articles")
    return result
