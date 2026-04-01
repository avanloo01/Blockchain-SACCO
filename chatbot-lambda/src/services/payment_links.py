from src.config import settings


def build_direct_transfer_intent(amount_usd: float, member_id: str) -> dict[str, float | str]:
    fee_usd = round(amount_usd * settings.service_fee_percent / 100.0, 2)
    net_pool_amount_usd = round(amount_usd - fee_usd, 2)
    return {
        "member_id": member_id,
        "amount_usd": amount_usd,
        "service_fee_usd": fee_usd,
        "net_pool_amount_usd": net_pool_amount_usd,
        "asset": "USDC",
        "network": "Solana",
    }
