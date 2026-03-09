"""Load configuration from .env using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Bakong API
    bakong_base_url: str = "http://10.169.111.11"
    bakong_username: str = ""
    bakong_password: str = ""
    # Balance inquiry code (e.g. BONGKHPPXXX) in path .../balance-inquiry/fast-core/{code}
    balance_inquiry_code: str = "BONGKHPPXXX"

    # Balance label shown in Telegram (e.g. BLCB, BLBK)
    balance_label: str = "BLCB"

    # Balance thresholds (alert when below these)
    threshold_usd: float = 10_000.0
    threshold_khr: float = 1_000_000.0

    # Telegram: alert chat (low balance), notification chat (balance every run)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""  # alert when balance is low
    telegram_chat_id_notification: str = ""  # balance summary on every run

    # Scheduler: cron "minute hour day month day_of_week" (every 5 min)
    balance_check_cron: str = "*/5 * * * *"


settings = Settings()
