from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    telegram_api_base: str = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    website_url: str = os.getenv("WEBSITE_URL", "https://blockchainsacco.com")
    governance_threshold_usd: float = float(os.getenv("GOVERNANCE_THRESHOLD_USD", "100"))
    pool_utilization_cap_percent: float = float(os.getenv("POOL_UTILIZATION_CAP_PERCENT", "60"))
    service_fee_percent: float = float(os.getenv("SERVICE_FEE_PERCENT", "1.0"))
    payment_provider: str = os.getenv("PAYMENT_PROVIDER", "transak")
    solana_treasury_address: str = os.getenv("SOLANA_TREASURY_ADDRESS", "")
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    transak_api_key: str = os.getenv("TRANSAK_API_KEY", "")
    transak_wallet_address: str = os.getenv("TRANSAK_WALLET_ADDRESS", "") or os.getenv("SOLANA_TREASURY_ADDRESS", "")
    transak_crypto_currency: str = os.getenv("TRANSAK_CRYPTO_CURRENCY", "USDC")
    transak_network: str = os.getenv("TRANSAK_NETWORK", "solana")


settings = Settings()
