import json
import logging
from typing import Any

# Configure root logger so all src.* modules emit to CloudWatch at INFO level.
logging.basicConfig(level=logging.INFO, force=True)

from src.config import settings  # noqa: E402
from src.handlers.telegram_webhook import handle_telegram_update  # noqa: E402

logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if not _is_valid_telegram_secret(event):
        logger.warning("Webhook request rejected: invalid or missing secret token")
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
            logger.error("Failed to parse request body as JSON")
            payload = {}
    else:
        payload = body or {}

    logger.info("Processing update_id=%s", payload.get("update_id"))
    result = handle_telegram_update(payload)
    logger.info("Update processed: ok=%s", result.get("ok"))
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
