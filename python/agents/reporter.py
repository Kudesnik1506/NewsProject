"""
Reporter Agent — assembles the final Markdown digest via Claude and saves it.
"""
import json
import os
from datetime import date
import anthropic

from config import MODEL, MAX_TOKENS
from utils import extract_text, load_prompt, load_user_prompt

client = anthropic.Anthropic()

SYSTEM_PROMPT = load_prompt("reporter")
USER_PROMPT = load_user_prompt("reporter")


REPORTER_MAX_TOKENS = 16000


def run(
    stories: list[dict],
    state_diagnosis: dict | None,
    country: str,
    target_date: date,
    total_sources: int,
    verified_count: int,
    date_from: date | None = None,
) -> str:
    """Генерирует Markdown-дайджест из проанализированных историй и сохраняет в reports/.

    Дайджест разделён на три части: верифицированные события, непроверенные сигналы,
    диагноз состояния государства. При date_from < target_date переключается в режим ПЕРИОД
    (динамика и тренды вместо перечня фактов). Возвращает путь к сохранённому файлу.
    """
    if date_from and date_from < target_date:
        days = (target_date - date_from).days + 1
        period_label = f"{date_from.isoformat()} / {target_date.isoformat()}"
        file_stem = f"{date_from.isoformat()}_{target_date.isoformat()}_{country}"
        mode = f"ПЕРИОД ({days} дней) — показывай динамику и тренды, объединяй истории по темам"
        print(f"[Reporter] Generating digest for {country} {period_label}...")
    else:
        period_label = target_date.isoformat()
        file_stem = f"{target_date.isoformat()}_{country}"
        mode = "ДЕНЬ — показывай каждое событие отдельно, полный формат по кластерам"
        print(f"[Reporter] Generating digest for {country} on {target_date}...")

    full_data = {"stories": stories, "state_diagnosis": state_diagnosis}

    response = client.messages.create(
        model=MODEL,
        max_tokens=REPORTER_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                country=country,
                date=period_label,
                mode=mode,
                total=total_sources,
                verified=verified_count,
                analyzed_stories_json=json.dumps(full_data, ensure_ascii=False, indent=2),
            )
        }]
    )

    markdown = extract_text(response.content[0].text)

    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, f"{file_stem}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"[Reporter] Saved: {file_path}")
    return file_path
