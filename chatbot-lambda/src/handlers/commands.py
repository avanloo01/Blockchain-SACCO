import logging

from src.config import settings
from src.policies.loan_policy import evaluate_loan_request
from src.repositories.billing_repo import create_billing_intent
from src.repositories.loan_repo import (
    create_loan_request,
    generate_repayment_schedule,
    get_pool_state,
)
from src.repositories.member_repo import get_member_by_chat_id, get_member_months
from src.services.payment_links import build_direct_transfer_intent

logger = logging.getLogger(__name__)

_SIGNUP_PROMPT = (
    "You need to sign up first. "
    f"Register at {settings.website_url}/signup and link your Telegram account."
)


def dispatch_command(chat_id: str, text: str) -> str:
    parts = text.split()
    command = parts[0].lower() if parts else ""

    if text.startswith("/start"):
        return (
            f"Welcome to Blockchain SACCO!\n\n"
            f"To get started, sign up at {settings.website_url}/signup "
            f"and link your Telegram account.\n\n"
            f"Once registered, use /help to see available commands."
        )

    if command == "/help":
        return (
            "Use /contribute 25 to get a USDC transfer intent. "
            "Use /loan_request 120 3 to request a 3-month loan. "
            "Use /status to view your membership summary."
        )

    # All commands below require an existing member account
    member = get_member_by_chat_id(telegram_chat_id=chat_id)
    if member is None:
        return _SIGNUP_PROMPT

    if command == "/status":
        months = get_member_months(member)
        return (
            f"Member since: {member.joinedOn.strftime('%Y-%m-%d')}\n"
            f"Months active: {months}\n"
            f"Total contributed: {member.contributionTotalUsd:.2f} USD\n"
            f"Repayment on-time ratio: {member.repaymentOnTimeRatio:.0%}"
        )

    if command == "/contribute":
        amount_usd = _parse_positive_float(parts[1] if len(parts) > 1 else None, default=20.0)
        if amount_usd <= 0:
            return "Invalid amount. Example: /contribute 25"
        intent = build_direct_transfer_intent(amount_usd=amount_usd, member_id=chat_id)
        create_billing_intent(
            member_id=member.id,
            amount_usd=intent["amount_usd"],
            service_fee_usd=intent["service_fee_usd"],
            net_pool_amount_usd=intent["net_pool_amount_usd"],
            idempotency_key=None,
        )
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

        member_months = get_member_months(member)
        pool = get_pool_state()

        decision = evaluate_loan_request(
            member_months=member_months,
            requested_amount_usd=amount_usd,
            pool_total_usd=max(pool["total_balance_usd"], 1.0),
            pool_total_lent_usd=pool["total_lent_out_usd"],
            risk_tier="medium",
        )
        if not decision["eligible"]:
            return f"Loan request declined: {decision['reason']}"

        loan = create_loan_request(
            member_id=member.id,
            amount_usd=amount_usd,
            tenure_months=tenure_months,
            governance_lane=decision["governance_lane"],
            reason=decision["reason"],
        )
        if decision["governance_lane"] == "auto":
            generate_repayment_schedule(loan)

        return (
            f"Loan request submitted for {amount_usd:.2f} USD over {tenure_months} months. "
            f"Lane: {decision['governance_lane']}. "
            f"Max approval: {decision['max_loan_usd']:.2f} USD"
        )

    return "Unknown command. Supported: /start, /help, /status, /contribute, /loan_request."


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
