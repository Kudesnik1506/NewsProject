"""
Filter Agent — deduplication, relevance scoring, and editorial filtering via Claude.
"""
import json
from concurrent.futures import ThreadPoolExecutor
import anthropic

from config import MODEL, MAX_TOKENS
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("filter_agent")
USER_PROMPT = load_user_prompt("filter_agent")


FILTER_BATCH_SIZE = 50


def _score_batch(batch: list[dict]) -> list[dict]:
    """Скорит и фильтрует один батч статей через Claude."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                articles_json=json.dumps(batch, ensure_ascii=False, indent=2)
            )
        }]
    )
    return extract_json(response.content[0].text)


def run(articles: list[dict]) -> list[dict]:
    """Фильтрует и оценивает статьи через Claude (батчами по FILTER_BATCH_SIZE).

    Claude возвращает только {url, relevance_score} — минимальный вывод.
    Python мёрджит scores с исходными статьями, затем дедупликация по URL.
    Возвращает только статьи с relevance_score >= 5, отсортированные по убыванию оценки.
    """
    print(f"[Filter] Processing {len(articles)} articles...")

    # Index original articles by URL for fast merge
    by_url = {a.get("url", ""): a for a in articles}

    batches = [articles[i:i + FILTER_BATCH_SIZE] for i in range(0, len(articles), FILTER_BATCH_SIZE)]
    if len(batches) > 1:
        print(f"[Filter] Split into {len(batches)} batches of up to {FILTER_BATCH_SIZE}")

    # Collect {url, relevance_score} pairs from all batches (in parallel)
    scored_map: dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=min(len(batches), 4)) as ex:
        for pairs in ex.map(_score_batch, batches):
            for item in pairs:
                url = item.get("url", "")
                score = float(item.get("relevance_score", 0))
                # Keep highest score if same URL appears in multiple batches
                if url not in scored_map or score > scored_map[url]:
                    scored_map[url] = score

    # Merge scores back into full article dicts
    result = []
    for url, score in scored_map.items():
        if url in by_url:
            article = dict(by_url[url])
            article["relevance_score"] = score
            result.append(article)

    result.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)
    print(f"[Filter] Filtered to {len(result)} articles")
    return result
