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


def run(
    stories: list[dict],
    country: str,
    target_date: date,
    total_sources: int,
    verified_count: int,
) -> str:
    """Генерирует Markdown-дайджест из проанализированных историй и сохраняет в reports/.

    Дайджест разделён на две части: верифицированные события (полный анализ по кластерам)
    и непроверенные сигналы (краткий список). Возвращает путь к сохранённому файлу.
    """
    print(f"[Reporter] Generating digest for {country} on {target_date}...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                country=country,
                date=target_date.isoformat(),
                total=total_sources,
                verified=verified_count,
                analyzed_stories_json=json.dumps(stories, ensure_ascii=False, indent=2),
            )
        }]
    )

    markdown = extract_text(response.content[0].text)

    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, f"{target_date.isoformat()}_{country}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"[Reporter] Saved: {file_path}")
    return file_path
