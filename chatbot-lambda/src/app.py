import json
from typing import Any

from src.config import settings
from src.handlers.telegram_webhook import handle_telegram_update


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if not _is_valid_telegram_secret(event):
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": "unauthorized"}),
        }

    body = event.get("body")
    if isinstance(body, str):
        try:
            payload = json.loads(body or "{}")
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = body or {}

    result = handle_telegram_update(payload)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result),
    }


def _is_valid_telegram_secret(event: dict[str, Any]) -> bool:
    expected = settings.telegram_webhook_secret
    if not expected:
        return True

    headers = event.get("headers") or {}
    provided = headers.get("X-Telegram-Bot-Api-Secret-Token") or headers.get(
        "x-telegram-bot-api-secret-token"
    )
    return provided == expected
