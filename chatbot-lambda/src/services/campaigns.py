import logging

from src.repositories.loan_repo import get_due_repayments
from src.repositories.member_repo import get_active_member_ids

logger = logging.getLogger(__name__)


def build_monthly_contribution_messages() -> list[dict[str, str]]:
    """Fan out contribution reminder messages to all members."""
    member_chat_ids = get_active_member_ids()
    messages = [
        {
            "member_id": cid,
            "message": "Your monthly contribution is due. Tap /contribute to pay with USDC.",
        }
        for cid in member_chat_ids
    ]
    logger.info("Built %d contribution reminder messages", len(messages))
    return messages


def build_repayment_messages() -> list[dict[str, str]]:
    """Build reminder messages for repayments due within 3 days."""
    due = get_due_repayments(days_ahead=3)
    messages = [
        {
            "member_id": r["member_id"],
            "message": f"Reminder: your loan repayment of {r['amount_usd']} USD is due on {r['due_on']}.",
        }
        for r in due
    ]
    logger.info("Built %d repayment reminder messages", len(messages))
    return messages
