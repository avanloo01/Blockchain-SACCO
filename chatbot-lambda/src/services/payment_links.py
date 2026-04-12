from src.config import settings
from src.services.payments import get_payment_provider


def build_direct_transfer_intent(amount_usd: float, member_id: str) -> dict[str, float | str]:
    provider = get_payment_provider()
    intent = provider.create_payment_intent(amount_usd=amount_usd, member_id=member_id)
    return {
        "member_id": member_id,
        "amount_usd": intent.amount_usd,
        "service_fee_usd": intent.service_fee_usd,
        "net_pool_amount_usd": intent.net_pool_amount_usd,
        "asset": intent.asset,
        "network": intent.network,
        "payment_url": intent.payment_url,
    }
