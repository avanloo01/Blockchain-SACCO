import requests

from src.config import settings


class TelegramApiError(RuntimeError):
    pass


def send_message(chat_id: str, text: str) -> dict:
    if not settings.telegram_bot_token:
        raise TelegramApiError("TELEGRAM_BOT_TOKEN is not configured")

    url = (
        f"{settings.telegram_api_base}/bot"
        f"{settings.telegram_bot_token}/sendMessage"
    )
    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )

    if response.status_code >= 400:
        raise TelegramApiError(
            f"Telegram sendMessage failed with status {response.status_code}: "
            f"{response.text[:200]}"
        )

    payload = response.json()
    if not payload.get("ok"):
        raise TelegramApiError(f"Telegram API error: {payload}")

    return payload
