"""
Analyst Agent — per-story parallel geostrategic and geopsychological analysis via Claude.
Tier 3: each article gets its own Claude call, run in pairs (rate-limit-safe).
"""
import json
import time
import functools
from concurrent.futures import ThreadPoolExecutor
import anthropic

from config import MODEL
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("analyst")
USER_PROMPT = load_user_prompt("analyst")

CONTENT_LIMIT = 1500   # per article; generous since each call handles only one story
TOP_N = 10             # analyze top-10 (parallel calls, no token competition)
MAX_TOKENS_PER_STORY = 4000   # one story doesn't need more; keeps rate-limit safe
MAX_WORKERS = 2        # 2 parallel calls × 4000 tokens = 8000/min (rate limit)


def _analyze_one(article: dict, country: str) -> dict | None:
    """Анализирует одну статью за один Claude-вызов. Возвращает AnalyzedStory или None."""
    a = dict(article)
    if len(a.get("content", "")) > CONTENT_LIMIT:
        a["content"] = a["content"][:CONTENT_LIMIT]

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS_PER_STORY,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": USER_PROMPT.format(
                        country=country,
                        articles_json=json.dumps([a], ensure_ascii=False, indent=2)
                    )
                }]
            )
            break
        except anthropic.RateLimitError:
            if attempt < 2:
                print(f"[Analyst] Rate limit hit, waiting 30s (attempt {attempt + 1}/3)...")
                time.sleep(30)
            else:
                raise

    result = extract_json(response.content[0].text)
    if isinstance(result, list):
        return result[0] if result else None
    if isinstance(result, dict):
        stories = result.get("stories", [])
        return stories[0] if stories else result
    return None


def run(articles: list[dict], country: str = "USA") -> list[dict]:
    """Анализирует топ-N статей (relevance_score >= 6) параллельными Claude-вызовами.

    Tier 3: каждая статья — отдельный вызов, MAX_WORKERS=2 для соблюдения rate limit.
    Возвращает список AnalyzedStory, отсортированных по убыванию relevance_score.
    """
    eligible = [
        a for a in articles
        if a.get("relevance_score", 0) >= 6
        and a.get("verification_status") != "DISPUTED"
    ]
    eligible = sorted(eligible, key=lambda a: a.get("relevance_score", 0), reverse=True)[:TOP_N]

    disputed_count = sum(1 for a in articles if a.get("verification_status") == "DISPUTED")
    if disputed_count:
        print(f"[Analyst] Skipped {disputed_count} DISPUTED articles (excluded from digest)")
    print(f"[Analyst] Analyzing {len(eligible)} articles ({MAX_WORKERS} parallel, {MAX_TOKENS_PER_STORY} tokens each)...")

    if not eligible:
        print("[Analyst] No eligible articles (relevance_score >= 6)")
        return []

    analyze_fn = functools.partial(_analyze_one, country=country)
    stories = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for story in ex.map(analyze_fn, eligible):
            if story:
                stories.append(story)

    print(f"[Analyst] Produced {len(stories)} analyzed stories")
    return stories
