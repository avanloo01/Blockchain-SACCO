import logging
from typing import Any

from src.handlers.commands import dispatch_command
from src.services.telegram_api import TelegramApiError, send_message

logger = logging.getLogger(__name__)


def handle_telegram_update(update: dict[str, Any]) -> dict[str, Any]:
    message = update.get("message", {})
    text = (message.get("text") or "").strip()
    chat_id = message.get("chat", {}).get("id")
    update_id = update.get("update_id")

    if not text or chat_id is None:
        logger.info("Ignoring update_id=%s (no text or chat_id)", update_id)
        return {"ok": True, "ignored": True, "update_id": update_id}

    chat_id_str = str(chat_id)
    logger.info("Dispatching command for chat_id=%s text=%s", chat_id_str, text[:60])
    response_text = dispatch_command(chat_id=chat_id_str, text=text)

    try:
        send_result = send_message(chat_id=chat_id_str, text=response_text)
    except TelegramApiError as exc:
        logger.error("Telegram API error for chat_id=%s: %s", chat_id_str, exc)
        return {
            "ok": False,
            "update_id": update_id,
            "chat_id": chat_id_str,
            "error": str(exc),
        }

    msg_id = send_result.get("result", {}).get("message_id")
    logger.info("Reply sent to chat_id=%s message_id=%s", chat_id_str, msg_id)
    return {
        "ok": True,
        "update_id": update_id,
        "chat_id": chat_id_str,
        "response": response_text,
        "telegram_message_id": msg_id,
    }
