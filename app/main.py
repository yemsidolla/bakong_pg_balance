"""FastAPI app with async workflow and APScheduler for balance-check cron."""

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.config import settings
from app.jobs.balance_check import run_balance_check, scheduled_balance_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _parse_cron(expr: str) -> dict[str, str | int]:
    """Parse 'min hour day month dow' into CronTrigger kwargs."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return {"minute": "0", "hour": "*", "day": "*", "month": "*", "day_of_week": "*"}
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scheduler on startup, shut down on shutdown."""
    cron = _parse_cron(settings.balance_check_cron)
    scheduler.add_job(
        scheduled_balance_check,
        trigger=CronTrigger(**cron),
        id="balance_check",
    )
    scheduler.start()
    logger.info("Scheduler started with cron: %s", settings.balance_check_cron)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Balance Alert Service",
    description="Checks Bakong balance and sends Telegram alerts when low.",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for Docker/load balancers."""
    return {"status": "ok"}


@app.post("/check-balance")
async def trigger_balance_check() -> dict[str, str]:
    """Manually trigger a balance check (async)."""
    await run_balance_check()
    return {"status": "check completed"}
