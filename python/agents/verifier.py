"""
Verifier Agent — cross-source fact verification via Claude.
"""
import json
from concurrent.futures import ThreadPoolExecutor
import anthropic

from config import MODEL, MAX_TOKENS
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("verifier")
USER_PROMPT = load_user_prompt("verifier")


BATCH_SIZE = 20


def _verify_batch(batch: list[dict]) -> list[dict]:
    """Верифицирует один батч статей через Claude.

    Claude возвращает только {url, verification_status, source_count, verification_note}.
    """
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
    """Кросс-верифицирует статьи через Claude (батчами по BATCH_SIZE).

    Claude возвращает только {url, verification_status, source_count, verification_note}.
    Python мёрджит эти поля обратно в полные статьи.
    """
    print(f"[Verifier] Verifying {len(articles)} articles...")

    by_url = {a.get("url", ""): a for a in articles}

    batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    if len(batches) > 1:
        print(f"[Verifier] Split into {len(batches)} batches of up to {BATCH_SIZE}")

    verdicts: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(batches), 4)) as ex:
        for items in ex.map(_verify_batch, batches):
            for item in items:
                url = item.get("url", "")
                if url:
                    verdicts[url] = item

    # Merge verdicts back into full articles
    result = []
    for url, article in by_url.items():
        merged = dict(article)
        verdict = verdicts.get(url, {})
        merged["verification_status"] = verdict.get("verification_status", "UNVERIFIED")
        merged["source_count"] = verdict.get("source_count", 1)
        merged["verification_note"] = verdict.get("verification_note", "Статус не определён верификатором.")
        result.append(merged)

    verified = sum(1 for a in result if a.get("verification_status") == "VERIFIED")
    unverified = sum(1 for a in result if a.get("verification_status") == "UNVERIFIED")
    disputed = sum(1 for a in result if a.get("verification_status") == "DISPUTED")
    print(f"[Verifier] VERIFIED: {verified}, UNVERIFIED: {unverified}, DISPUTED: {disputed}")

    return result
