"""
Telegram source via Telethon.

Requires manual auth on first run:
    python -c "from sources.telegram_source import auth; auth()"

Set in .env:
    TELEGRAM_API_ID=...
    TELEGRAM_API_HASH=...
    TELEGRAM_PHONE=...
"""
import os
from models import Article


def fetch_telegram(channels: list[str], country: str, limit: int = 10) -> list[Article]:
    if not channels:
        return []

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        print("[Telegram] TELEGRAM_API_ID / TELEGRAM_API_HASH not set, skipping.")
        return []

    try:
        from telethon.sync import TelegramClient
    except ImportError:
        print("[Telegram] telethon not installed, skipping.")
        return []

    articles = []
    with TelegramClient("news_session", int(api_id), api_hash) as client:
        for channel in channels:
            try:
                for message in client.iter_messages(channel, limit=limit):
                    if not message.text:
                        continue
                    articles.append(Article(
                        title=message.text[:100],
                        url=f"https://t.me/{channel.lstrip('@')}/{message.id}",
                        source=channel,
                        content=message.text[:600],
                        published_at=message.date,
                        country=country,
                    ))
            except Exception as e:
                print(f"[Telegram] Error reading {channel}: {e}")
    return articles


def auth():
    """Run once interactively to create a session file."""
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")
    from telethon.sync import TelegramClient
    with TelegramClient("news_session", int(api_id), api_hash) as client:
        client.start(phone=phone)
        print("Auth successful. Session saved.")
