"""
Verifier Agent — cross-source fact verification via Claude.
"""
import json
import anthropic

from config import MODEL, MAX_TOKENS
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("verifier")
USER_PROMPT = load_user_prompt("verifier")


def run(articles: list[dict]) -> list[dict]:
    print(f"[Verifier] Verifying {len(articles)} articles...")

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

    verified = sum(1 for a in result if a.get("verification_status") == "VERIFIED")
    unverified = sum(1 for a in result if a.get("verification_status") == "UNVERIFIED")
    disputed = sum(1 for a in result if a.get("verification_status") == "DISPUTED")
    print(f"[Verifier] VERIFIED: {verified}, UNVERIFIED: {unverified}, DISPUTED: {disputed}")

    return result
