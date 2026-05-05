import logging
from typing import Any

from src.handlers.commands import dispatch_command
from src.repositories.member_repo import (
    MemberLinkAmbiguousError,
    MemberLinkConflictError,
    MemberLinkNotFoundError,
    get_member_by_chat_id,
    link_member_by_phone,
)
from src.repositories.message_repo import record_delivery
from src.services.telegram_api import TelegramApiError, send_message

logger = logging.getLogger(__name__)

_CONTACT_REQUEST_MARKUP = {
    "keyboard": [[{"text": "Share phone number", "request_contact": True}]],
    "one_time_keyboard": True,
    "resize_keyboard": True,
}
_REMOVE_KEYBOARD_MARKUP = {"remove_keyboard": True}


def handle_telegram_update(update: dict[str, Any]) -> dict[str, Any]:
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    update_id = update.get("update_id")

    if chat_id is None:
        logger.info("Ignoring update_id=%s (no chat_id)", update_id)
        return {"ok": True, "ignored": True, "update_id": update_id}

    chat_id_str = str(chat_id)
    contact = message.get("contact") or {}
    if contact:
        return _handle_contact_message(
            update_id=update_id,
            chat_id=chat_id_str,
            contact=contact,
        )

    text = (message.get("text") or "").strip()
    if not text:
        logger.info("Ignoring update_id=%s (no text or contact)", update_id)
        return {"ok": True, "ignored": True, "update_id": update_id}

    logger.info("Dispatching command for chat_id=%s text=%s", chat_id_str, text[:60])
    try:
        response_text = dispatch_command(chat_id=chat_id_str, text=text)
    except Exception:
        logger.exception("Command handling failed for chat_id=%s text=%s", chat_id_str, text[:60])
        response_text = (
            "Something went wrong while processing that command. "
            "Please try again in a moment."
        )

    reply_markup = None
    if get_member_by_chat_id(telegram_chat_id=chat_id_str) is None:
        reply_markup = _CONTACT_REQUEST_MARKUP

    return _send_reply(
        update_id=update_id,
        chat_id=chat_id_str,
        response_text=response_text,
        reply_markup=reply_markup,
    )


def _handle_contact_message(
    update_id: Any,
    chat_id: str,
    contact: dict[str, Any],
) -> dict[str, Any]:
    contact_user_id = contact.get("user_id")
    if contact_user_id is not None and str(contact_user_id) != chat_id:
        return _send_reply(
            update_id=update_id,
            chat_id=chat_id,
            response_text="Please share your own Telegram phone number using the button below.",
            reply_markup=_CONTACT_REQUEST_MARKUP,
        )

    phone_number = contact.get("phone_number")
    try:
        member = link_member_by_phone(telegram_chat_id=chat_id, phone=phone_number or "")
    except MemberLinkNotFoundError:
        return _send_reply(
            update_id=update_id,
            chat_id=chat_id,
            response_text=(
                "I could not find a signup with that phone number. "
                "Sign up on the website with the same number, then try again."
            ),
            reply_markup=_CONTACT_REQUEST_MARKUP,
        )
    except MemberLinkAmbiguousError:
        return _send_reply(
            update_id=update_id,
            chat_id=chat_id,
            response_text=(
                "I found multiple SACCO accounts with that phone number. "
                "Please contact support to resolve the duplicate signup."
            ),
            reply_markup=_CONTACT_REQUEST_MARKUP,
        )
    except MemberLinkConflictError as exc:
        return _send_reply(
            update_id=update_id,
            chat_id=chat_id,
            response_text=str(exc),
            reply_markup=_CONTACT_REQUEST_MARKUP,
        )

    response_text = (
        f"Your Telegram account is now linked to {member.phone or phone_number}.\n\n"
        "Use /help to see available commands."
    )
    return _send_reply(
        update_id=update_id,
        chat_id=chat_id,
        response_text=response_text,
        reply_markup=_REMOVE_KEYBOARD_MARKUP,
    )


def _send_reply(
    update_id: Any,
    chat_id: str,
    response_text: str,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        send_result = send_message(
            chat_id=chat_id,
            text=response_text,
            reply_markup=reply_markup,
        )
    except TelegramApiError as exc:
        logger.error("Telegram API error for chat_id=%s: %s", chat_id, exc)
        return {
            "ok": False,
            "update_id": update_id,
            "chat_id": chat_id,
            "error": str(exc),
        }

    msg_id = send_result.get("result", {}).get("message_id")
    logger.info("Reply sent to chat_id=%s message_id=%s", chat_id, msg_id)

    # Track delivery in DB (only if member exists)
    try:
        member = get_member_by_chat_id(telegram_chat_id=chat_id)
        if member:
            record_delivery(
                member_id=member.id,
                campaign="webhook_reply",
                message_text=response_text[:500],
                telegram_msg_id=str(msg_id) if msg_id else None,
            )
    except Exception:
        logger.exception("Failed to record message delivery for chat_id=%s", chat_id)

    return {
        "ok": True,
        "update_id": update_id,
        "chat_id": chat_id,
        "response": response_text,
        "telegram_message_id": msg_id,
    }
