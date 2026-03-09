"""Send messages via Telegram Bot API."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_telegram_message(text: str, chat_id: str | None = None) -> bool:
    """Send a message to a Telegram chat. If chat_id is None, uses alert chat_id. Returns True on success."""
    target = chat_id or settings.telegram_chat_id
    if not settings.telegram_bot_token or not target:
        return False
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": target, "text": text},
        )
        if not r.is_success:
            logger.warning(
                "Telegram sendMessage failed %s: %s",
                r.status_code,
                r.text,
            )
        return r.is_success
