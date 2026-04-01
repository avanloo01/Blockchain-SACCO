from typing import Any

from src.handlers.commands import dispatch_command
from src.services.telegram_api import TelegramApiError, send_message


def handle_telegram_update(update: dict[str, Any]) -> dict[str, Any]:
    message = update.get("message", {})
    text = (message.get("text") or "").strip()
    chat_id = message.get("chat", {}).get("id")
    update_id = update.get("update_id")

    if not text or chat_id is None:
        return {"ok": True, "ignored": True, "update_id": update_id}

    chat_id_str = str(chat_id)
    response_text = dispatch_command(chat_id=chat_id_str, text=text)

    try:
        send_result = send_message(chat_id=chat_id_str, text=response_text)
    except TelegramApiError as exc:
        return {
            "ok": False,
            "update_id": update_id,
            "chat_id": chat_id_str,
            "error": str(exc),
        }

    return {
        "ok": True,
        "update_id": update_id,
        "chat_id": chat_id_str,
        "response": response_text,
        "telegram_message_id": send_result.get("result", {}).get("message_id"),
    }
