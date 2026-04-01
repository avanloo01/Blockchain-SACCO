from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    telegram_api_base: str = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    governance_threshold_usd: float = float(os.getenv("GOVERNANCE_THRESHOLD_USD", "100"))
    pool_utilization_cap_percent: float = float(os.getenv("POOL_UTILIZATION_CAP_PERCENT", "60"))
    service_fee_percent: float = float(os.getenv("SERVICE_FEE_PERCENT", "1.0"))


settings = Settings()
