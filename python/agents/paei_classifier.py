"""
PAEI Classifier Agent — state health diagnosis via PAEI×Jung model.
"""
import json
import anthropic

from config import MODEL
from utils import extract_json, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("paei_classifier")
USER_PROMPT = load_user_prompt("paei_classifier")


def run(stories: list[dict], country: str = "USA") -> dict | None:
    """Диагностирует баланс государства по 8 измерениям PAEI×Jung.

    Принимает список проанализированных историй с полем cluster.
    Возвращает state_diagnosis: cluster_load, dominant, deficit, imbalances, summary.
    """
    if not stories:
        print("[PAEI Classifier] No stories — skipping diagnosis")
        return None

    print(f"[PAEI Classifier] Diagnosing {len(stories)} stories for {country}...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                country=country,
                analyzed_stories_json=json.dumps(stories, ensure_ascii=False, indent=2)
            )
        }]
    )

    result = extract_json(response.content[0].text)
    dominant = result.get("dominant", [])
    deficit = result.get("deficit", [])
    print(f"[PAEI Classifier] Dominant: {dominant}, Deficit: {deficit}")
    return result
