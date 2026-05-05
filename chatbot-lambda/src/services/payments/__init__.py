from src.config import settings
from src.services.payments.base import PaymentProvider

_PROVIDER_IMPORTS: dict[str, tuple[str, str]] = {
    "solana_testnet": ("src.services.payments.solana_testnet", "SolanaTestnetProvider"),
    "crossmint": ("src.services.payments.crossmint", "CrossmintProvider"),
}

_instance: PaymentProvider | None = None


def get_payment_provider() -> PaymentProvider:
    """Return a configured payment provider based on PAYMENT_PROVIDER setting."""
    global _instance
    if _instance is not None:
        return _instance

    provider_key = settings.payment_provider
    target = _PROVIDER_IMPORTS.get(provider_key)
    if target is None:
        raise ValueError(
            f"Unknown payment provider '{provider_key}'. "
            f"Available: {', '.join(_PROVIDER_IMPORTS)}"
        )
    module_name, class_name = target
    module = __import__(module_name, fromlist=[class_name])
    cls = getattr(module, class_name)
    _instance = cls()
    return _instance
