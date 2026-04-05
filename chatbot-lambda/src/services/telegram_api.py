import requests

from src.config import settings


class TelegramApiError(RuntimeError):
    pass


def send_message(chat_id: str, text: str) -> dict:
    if not settings.telegram_bot_token:
        raise TelegramApiError("TELEGRAM_BOT_TOKEN is not configured")

    payload = _post("sendMessage", {"chat_id": chat_id, "text": text})
    return payload


def register_webhook(
    webhook_url: str,
    bot_token: str | None = None,
    secret_token: str | None = None,
) -> dict:
    request_payload = {
        "url": webhook_url,
        "allowed_updates": ["message"],
        "drop_pending_updates": False,
    }
    effective_secret = secret_token or settings.telegram_webhook_secret
    if effective_secret:
        request_payload["secret_token"] = effective_secret

    return _post("setWebhook", request_payload, bot_token=bot_token)


def get_webhook_info(bot_token: str | None = None) -> dict:
    return _get("getWebhookInfo", bot_token=bot_token)


def _bot_method_url(method: str, bot_token: str | None = None) -> str:
    token = bot_token or settings.telegram_bot_token
    if not token:
        raise TelegramApiError("TELEGRAM_BOT_TOKEN is not configured")
    return f"{settings.telegram_api_base}/bot{token}/{method}"


def _post(method: str, payload: dict, bot_token: str | None = None) -> dict:
    url = _bot_method_url(method, bot_token=bot_token)
    response = requests.post(url, json=payload, timeout=15)
    return _parse_response(response=response, method=method)


def _get(method: str, bot_token: str | None = None) -> dict:
    url = _bot_method_url(method, bot_token=bot_token)
    response = requests.get(url, timeout=15)
    return _parse_response(response=response, method=method)


def _parse_response(response: requests.Response, method: str) -> dict:
    if response.status_code >= 400:
        raise TelegramApiError(
            f"Telegram {method} failed with status {response.status_code}: "
            f"{response.text[:200]}"
        )

    payload = response.json()
    if not payload.get("ok"):
        raise TelegramApiError(f"Telegram API error on {method}: {payload}")

    return payload
