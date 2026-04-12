from src.config import settings
from src.services.payments.base import PaymentProvider
from src.services.payments.solana_testnet import SolanaTestnetProvider
from src.services.payments.transak import TransakProvider

_PROVIDERS: dict[str, type[PaymentProvider]] = {
    "solana_testnet": SolanaTestnetProvider,
    "transak": TransakProvider,
}

_instance: PaymentProvider | None = None


def get_payment_provider() -> PaymentProvider:
    """Return a configured payment provider based on PAYMENT_PROVIDER setting."""
    global _instance
    if _instance is not None:
        return _instance

    provider_key = settings.payment_provider
    cls = _PROVIDERS.get(provider_key)
    if cls is None:
        raise ValueError(
            f"Unknown payment provider '{provider_key}'. "
            f"Available: {', '.join(_PROVIDERS)}"
        )
    _instance = cls()
    return _instance
