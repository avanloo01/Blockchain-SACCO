from src.policies.loan_policy import evaluate_loan_request
from src.services.payment_links import build_direct_transfer_intent


def dispatch_command(chat_id: str, text: str) -> str:
    _ = chat_id
    parts = text.split()
    command = parts[0].lower() if parts else ""

    if text.startswith("/start"):
        return (
            "Welcome to Blockchain SACCO. Commands: /contribute [amount], "
            "/loan_request [amount] [tenure_months], /help."
        )

    if command == "/help":
        return (
            "Use /contribute 25 to get a USDC transfer intent. "
            "Use /loan_request 120 3 to request a 3-month loan."
        )

    if command == "/contribute":
        amount_usd = _parse_positive_float(parts[1] if len(parts) > 1 else None, default=20.0)
        if amount_usd <= 0:
            return "Invalid amount. Example: /contribute 25"
        intent = build_direct_transfer_intent(amount_usd=amount_usd, member_id=chat_id)
        return (
            "Contribution intent created. "
            f"Amount: {intent['amount_usd']:.2f} USD, "
            f"Fee: {intent['service_fee_usd']:.2f} USD, "
            f"Net to pool: {intent['net_pool_amount_usd']:.2f} USD, "
            "Asset: USDC on Solana."
        )

    if command == "/loan_request":
        amount_usd = _parse_positive_float(parts[1] if len(parts) > 1 else None, default=120.0)
        tenure_months = _parse_positive_int(parts[2] if len(parts) > 2 else None, default=3)
        if amount_usd <= 0 or tenure_months <= 0:
            return "Invalid loan request. Example: /loan_request 120 3"
        decision = evaluate_loan_request(
            member_months=4,
            requested_amount_usd=amount_usd,
            pool_total_usd=10000.0,
            pool_total_lent_usd=5000.0,
            risk_tier="medium",
        )
        if not decision["eligible"]:
            return f"Loan request declined: {decision['reason']}"
        return (
            f"Loan request submitted for {amount_usd:.2f} USD over {tenure_months} months. "
            f"Lane: {decision['governance_lane']}. "
            f"Max approval: {decision['max_loan_usd']:.2f} USD"
        )

    return "Unknown command. Supported: /start, /help, /contribute, /loan_request."


def _parse_positive_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return -1.0


def _parse_positive_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return -1
