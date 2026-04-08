"""
Triage Agent — combined relevance scoring + verification in one Claude call.
Replaces filter_agent + verifier for the full pipeline.
"""
import json
import functools
from concurrent.futures import ThreadPoolExecutor
import anthropic

from config import MODEL, MAX_TOKENS
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("triage_agent")
USER_PROMPT_FULL = load_user_prompt("triage_agent", section="full")
USER_PROMPT_FAST = load_user_prompt("triage_agent", section="fast")

BATCH_SIZE = 25


def _triage_batch(batch: list[dict], verify: bool) -> list[dict]:
    """Обрабатывает один батч: scoring + (опционально) верификация."""
    prompt = USER_PROMPT_FULL if verify else USER_PROMPT_FAST
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": prompt.format(
                articles_json=json.dumps(batch, ensure_ascii=False, indent=2)
            )
        }]
    )
    return extract_json(response.content[0].text)


def run(articles: list[dict], verify: bool = True) -> list[dict]:
    """Оценивает релевантность и верифицирует статьи за один раунд Claude-вызовов.

    verify=True  — полный режим: scoring + verification (VERIFIED/UNVERIFIED/DISPUTED)
    verify=False — fast-режим: только scoring, verification_status=UNVERIFIED для всех
    Возвращает статьи с relevance_score >= 5, отсортированные по убыванию.
    """
    mode = "full" if verify else "fast"
    print(f"[Triage] Processing {len(articles)} articles ({mode} mode)...")

    by_url = {a.get("url", ""): a for a in articles}
    batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    if len(batches) > 1:
        print(f"[Triage] Split into {len(batches)} batches of up to {BATCH_SIZE}")

    triage_map: dict[str, dict] = {}
    batch_fn = functools.partial(_triage_batch, verify=verify)
    with ThreadPoolExecutor(max_workers=min(len(batches), 4)) as ex:
        for items in ex.map(batch_fn, batches):
            for item in items:
                url = item.get("url", "")
                if not url:
                    continue
                prev_score = triage_map.get(url, {}).get("relevance_score", 0)
                if item.get("relevance_score", 0) >= prev_score:
                    triage_map[url] = item

    result = []
    for url, article in by_url.items():
        verdict = triage_map.get(url)
        if verdict is None:
            continue  # relevance_score < 5 — отсеяна промптом
        merged = dict(article)
        merged["relevance_score"] = verdict.get("relevance_score", 0)
        if verify:
            merged["verification_status"] = verdict.get("verification_status", "UNVERIFIED")
            merged["source_count"] = verdict.get("source_count", 1)
            merged["verification_note"] = verdict.get("verification_note", "Не определён.")
        else:
            merged["verification_status"] = "UNVERIFIED"
            merged["source_count"] = 1
            merged["verification_note"] = "Verification skipped (fast mode)"
        result.append(merged)

    result.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)

    v_ok  = sum(1 for a in result if a.get("verification_status") == "VERIFIED")
    v_no  = sum(1 for a in result if a.get("verification_status") == "UNVERIFIED")
    v_dis = sum(1 for a in result if a.get("verification_status") == "DISPUTED")
    print(f"[Triage] {len(result)} articles kept — VERIFIED: {v_ok}, UNVERIFIED: {v_no}, DISPUTED: {v_dis}")
    return result
