import requests

from src.config import settings


class TelegramApiError(RuntimeError):
    pass


def send_message(chat_id: str, text: str) -> dict:
    if not settings.telegram_bot_token:
        raise TelegramApiError("TELEGRAM_BOT_TOKEN is not configured")

    payload = _post("sendMessage", {"chat_id": chat_id, "text": text})
    return payload


def register_webhook(webhook_url: str) -> dict:
    request_payload = {
        "url": webhook_url,
        "allowed_updates": ["message"],
        "drop_pending_updates": False,
    }
    if settings.telegram_webhook_secret:
        request_payload["secret_token"] = settings.telegram_webhook_secret

    return _post("setWebhook", request_payload)


def get_webhook_info() -> dict:
    return _get("getWebhookInfo")


def _bot_method_url(method: str) -> str:
    if not settings.telegram_bot_token:
        raise TelegramApiError("TELEGRAM_BOT_TOKEN is not configured")
    return f"{settings.telegram_api_base}/bot{settings.telegram_bot_token}/{method}"


def _post(method: str, payload: dict) -> dict:
    url = _bot_method_url(method)
    response = requests.post(url, json=payload, timeout=15)
    return _parse_response(response=response, method=method)


def _get(method: str) -> dict:
    url = _bot_method_url(method)
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
