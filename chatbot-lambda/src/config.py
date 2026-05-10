from dataclasses import dataclass
import os


def _default_crossmint_token_locator(app_env: str) -> str:
    if app_env == "prod":
        return "solana:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    return "solana:4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"


def _default_solana_usdc_mint(app_env: str) -> str:
    """Mint address used when disbursing loans directly from the treasury wallet.

    Prod: Circle's mainnet USDC.
    Dev:  SPL Token Faucet USDC-Dev (https://spl-token-faucet.com/?token-name=USDC-Dev).
    """
    if app_env == "prod":
        return "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    return "Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr"


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
    payment_provider: str = os.getenv("PAYMENT_PROVIDER", "crossmint")
    solana_treasury_address: str = os.getenv("SOLANA_TREASURY_ADDRESS", "")
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    crossmint_server_api_key: str = os.getenv("CROSSMINT_SERVER_API_KEY", "")
    crossmint_wallet_address: str = os.getenv("CROSSMINT_WALLET_ADDRESS", "") or os.getenv("SOLANA_TREASURY_ADDRESS", "")
    # Email of the SACCO's Crossmint account.  The treasury wallet is linked to
    # this account, NOT to individual members.  Must match the account that owns
    # CROSSMINT_WALLET_ADDRESS in the Crossmint dashboard.
    crossmint_treasury_email: str = os.getenv("CROSSMINT_TREASURY_EMAIL", "")
    crossmint_token_locator: str = os.getenv("CROSSMINT_TOKEN_LOCATOR") or _default_crossmint_token_locator(
        os.getenv("APP_ENV", "dev")
    )
    crossmint_slippage_bps: int = int(os.getenv("CROSSMINT_SLIPPAGE_BPS", "500"))
    solana_treasury_private_key: str = os.getenv("SOLANA_TREASURY_PRIVATE_KEY", "")
    solana_usdc_mint: str = os.getenv("SOLANA_USDC_MINT") or _default_solana_usdc_mint(
        os.getenv("APP_ENV", "dev")
    )


settings = Settings()
