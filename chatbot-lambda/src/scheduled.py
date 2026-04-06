import logging
from typing import Any

from src.repositories.member_repo import get_member_by_chat_id
from src.repositories.message_repo import record_delivery
from src.services.campaigns import build_monthly_contribution_messages, build_repayment_messages
from src.services.telegram_api import TelegramApiError, send_message

logger = logging.getLogger(__name__)


def monthly_contribution_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    messages = build_monthly_contribution_messages()
    sent = 0
    for msg in messages:
        try:
            result = send_message(chat_id=msg["member_id"], text=msg["message"])
            msg_id = result.get("result", {}).get("message_id")
            member = get_member_by_chat_id(msg["member_id"])
            if member:
                record_delivery(
                    member_id=member.id,
                    campaign="monthly_contribution",
                    message_text=msg["message"],
                    telegram_msg_id=str(msg_id) if msg_id else None,
                )
            sent += 1
        except TelegramApiError:
            logger.exception("Failed to send contribution reminder to %s", msg["member_id"])
    return {
        "status": "ok",
        "campaign": "monthly_contribution",
        "queued_messages": len(messages),
        "sent_messages": sent,
    }


def repayment_reminder_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    messages = build_repayment_messages()
    sent = 0
    for msg in messages:
        try:
            result = send_message(chat_id=msg["member_id"], text=msg["message"])
            msg_id = result.get("result", {}).get("message_id")
            member = get_member_by_chat_id(msg["member_id"])
            if member:
                record_delivery(
                    member_id=member.id,
                    campaign="repayment_reminder",
                    message_text=msg["message"],
                    telegram_msg_id=str(msg_id) if msg_id else None,
                )
            sent += 1
        except TelegramApiError:
            logger.exception("Failed to send repayment reminder to %s", msg["member_id"])
    return {
        "status": "ok",
        "campaign": "repayment_reminder",
        "queued_messages": len(messages),
        "sent_messages": sent,
    }
