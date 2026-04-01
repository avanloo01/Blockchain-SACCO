import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.telegram_api import get_webhook_info, register_webhook  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Register Telegram webhook")
    parser.add_argument("--webhook-url", required=True, help="Public HTTPS webhook URL")
    parser.add_argument(
        "--bot-token",
        default="",
        help="Telegram bot token (overrides TELEGRAM_BOT_TOKEN for this command only)",
    )
    parser.add_argument(
        "--show-info",
        action="store_true",
        help="Fetch webhook info after registration",
    )
    args = parser.parse_args()

    token_override = args.bot_token.strip() or None

    result = register_webhook(webhook_url=args.webhook_url, bot_token=token_override)
    print("setWebhook response:")
    print(json.dumps(result, indent=2))

    if args.show_info:
        info = get_webhook_info(bot_token=token_override)
        print("getWebhookInfo response:")
        print(json.dumps(info, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
