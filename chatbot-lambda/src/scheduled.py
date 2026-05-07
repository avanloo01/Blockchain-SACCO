import logging
from typing import Any

from src.repositories.billing_repo import get_pending_billing_intents, mark_billing_settled
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


def payment_reconciliation_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Check pending billing intents that have a tx_signature for on-chain confirmation.

    This handles the case where a member submitted a tx_signature via /verify
    but the transaction was still pending at verification time, as well as
    any intents that may have been missed.
    """
    from src.repositories.loan_repo import mark_repayment_paid
    from src.repositories.member_repo import add_contribution_by_member_id
    from src.config import settings
    from src.services.payments import get_payment_provider
    from src.services.payments.base import PaymentStatus

    pending = get_pending_billing_intents()
    provider = get_payment_provider()
    confirmed = 0
    failed = 0

    for intent in pending:
        if settings.payment_provider != "crossmint" and not intent.txSignature:
            continue

        verification_reference = intent.txSignature or intent.idempotencyKey or intent.id

        try:
            result = provider.verify_payment_settlement(
                intent_id=intent.idempotencyKey or intent.id,
                tx_signature=verification_reference,
            )
        except Exception:
            logger.exception("Reconciliation error for intent %s", intent.id)
            continue

        if result.status == PaymentStatus.CONFIRMED:
            mark_billing_settled(
                intent_id=intent.id,
                tx_signature=result.tx_signature or verification_reference,
            )
            member = intent.member if intent.member else None
            memo = intent.memo if isinstance(intent.memo, str) else ""
            if memo.startswith("repay:"):
                repayment_id = memo.split(":", 1)[1].strip()
                if repayment_id:
                    mark_repayment_paid(repayment_id)
            elif member:
                add_contribution_by_member_id(
                    member_id=member.id,
                    amount_usd=intent.netPoolAmountUsd,
                )
            if member and member.telegramChatId:
                try:
                    send_message(
                        chat_id=member.telegramChatId,
                        text=(
                            f"Your contribution of {intent.netPoolAmountUsd:.2f} USDC "
                            f"has been confirmed on-chain."
                        ),
                    )
                except TelegramApiError:
                    logger.exception("Failed to notify member %s of settlement", member.id)
            confirmed += 1
        elif result.status == PaymentStatus.FAILED:
            failed += 1

    logger.info("Reconciliation complete: confirmed=%d failed=%d", confirmed, failed)
    return {
        "status": "ok",
        "checked": len(
            [
                i
                for i in pending
                if settings.payment_provider == "crossmint" or i.txSignature
            ]
        ),
        "confirmed": confirmed,
        "failed": failed,
    }
