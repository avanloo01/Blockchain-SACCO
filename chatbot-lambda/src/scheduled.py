from typing import Any

from src.services.campaigns import build_monthly_contribution_messages, build_repayment_messages


def monthly_contribution_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    messages = build_monthly_contribution_messages()
    return {
        "status": "ok",
        "campaign": "monthly_contribution",
        "queued_messages": len(messages),
    }


def repayment_reminder_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    messages = build_repayment_messages()
    return {
        "status": "ok",
        "campaign": "repayment_reminder",
        "queued_messages": len(messages),
    }
