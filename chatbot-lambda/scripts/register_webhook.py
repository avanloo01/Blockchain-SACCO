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
        "--show-info",
        action="store_true",
        help="Fetch webhook info after registration",
    )
    args = parser.parse_args()

    result = register_webhook(webhook_url=args.webhook_url)
    print("setWebhook response:")
    print(json.dumps(result, indent=2))

    if args.show_info:
        info = get_webhook_info()
        print("getWebhookInfo response:")
        print(json.dumps(info, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
