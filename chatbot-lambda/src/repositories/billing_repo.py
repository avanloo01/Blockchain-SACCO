def create_billing_intent(member_id: str, amount_usd: float) -> dict[str, str | float]:
    return {
        "intent_id": "bill_001",
        "member_id": member_id,
        "amount_usd": amount_usd,
        "status": "pending",
    }
