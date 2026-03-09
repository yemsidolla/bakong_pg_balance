"""Scheduled job: fetch balance, compare to thresholds, send Telegram alert if low."""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings

# Cambodia (UTC+7)
CAMBODIA_TZ = ZoneInfo("Asia/Phnom_Penh")
from app.services.bakong import get_auth_token, get_balance_inquiry
from app.services.telegram import send_telegram_message

logger = logging.getLogger(__name__)


def _parse_amounts(total_amounts: dict[str, str] | None) -> tuple[float, float]:
    """Extract usd#nbc and khr#nbc as floats. Returns (usd, khr)."""
    if not total_amounts:
        return 0.0, 0.0
    usd = float(total_amounts.get("usd#nbc", 0) or 0)
    khr = float(total_amounts.get("khr#nbc", 0) or 0)
    return usd, khr


async def run_balance_check() -> None:
    """Async workflow: auth -> get balance -> notification every run -> alert if low."""
    try:
        token = await get_auth_token()
        summary = await get_balance_inquiry(token)
    except Exception as e:
        logger.exception("Failed to fetch balance")
        if settings.telegram_bot_token and settings.telegram_chat_id:
            await send_telegram_message(f"⚠️ Balance check failed: {e}")
        return

    total_amounts = summary.get("totalAmounts") or {}
    total_account = summary.get("totalAccount", 0)
    usd, khr = _parse_amounts(total_amounts)
    label = settings.balance_label
    ts = datetime.now(CAMBODIA_TZ).isoformat(timespec="milliseconds")

    # 1. Notification: send current balance to notification chat on every run
    if settings.telegram_chat_id_notification:
        notification_msg = (
            f"At query timestamp: {ts}\n"
            f"{label} Balance - KHR: {khr:,.2f}, USD: {usd:,.2f}"
        )
        await send_telegram_message(notification_msg, settings.telegram_chat_id_notification)

    # 2. Alert: send to alert chat only when balance is low
    low_usd = usd < settings.threshold_usd
    low_khr = khr < settings.threshold_khr

    if low_usd or low_khr:
        shortage_khr = max(0, settings.threshold_khr - khr) if low_khr else 0
        shortage_usd = max(0, settings.threshold_usd - usd) if low_usd else 0
        msg_parts = [
            f"⚠️ BALANCE STILL LOW (Check #{total_account})",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"⏰ Timestamp: {ts}",
            "",
        ]
        if low_khr:
            msg_parts.extend([
                f"🔴 {label} KHR: {khr:,.2f}",
                f"   Threshold: {settings.threshold_khr:,.2f}",
                f"   Shortage: {shortage_khr:,.2f}",
                "",
            ])
        if low_usd:
            msg_parts.extend([
                f"🔴 {label} USD: {usd:,.2f}",
                f"   Threshold: {settings.threshold_usd:,.2f}",
                f"   Shortage: {shortage_usd:,.2f}",
                "",
            ])
        msg_parts.extend([
            "📊 All Balances:",
            f"   {label} - KHR: {khr:,.2f}",
            f"   {label} - USD: {usd:,.2f}",
        ])
        msg = "\n".join(msg_parts)
        sent = await send_telegram_message(msg)  # uses telegram_chat_id (alert)
        if sent:
            logger.info("Low balance alert sent via Telegram")
        else:
            logger.warning("Could not send Telegram alert (check token/chat_id)")
    else:
        logger.info("Balance OK: usd=%.2f khr=%.2f", usd, khr)


def scheduled_balance_check() -> None:
    """Sync entrypoint for APScheduler: runs async run_balance_check()."""
    asyncio.run(run_balance_check())
