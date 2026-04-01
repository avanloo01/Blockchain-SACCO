import json
from typing import Any

from src.handlers.telegram_webhook import handle_telegram_update


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
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
