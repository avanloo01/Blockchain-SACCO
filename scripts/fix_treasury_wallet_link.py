#!/usr/bin/env python3
"""Fix treasury wallet linkage in Crossmint.

When the SACCO treasury wallet has been accidentally linked to a member's
Crossmint user (instead of the SACCO's own Crossmint account), payments fail
with "Payment could not be completed" (HTTP 400) because Crossmint treats it as
a self-payment.

This script:
  1. Unlinks the treasury wallet from the wrong email (--from-email).
  2. Re-links the treasury wallet to the SACCO's Crossmint account (CROSSMINT_TREASURY_EMAIL).

Usage
-----
Export the required environment variables, then run::

    python scripts/fix_treasury_wallet_link.py --from-email wrong@example.com

Or inline::

    CROSSMINT_SERVER_API_KEY=sk_... \\
    CROSSMINT_WALLET_ADDRESS=<base58 address> \\
    CROSSMINT_TREASURY_EMAIL=treasury@yoursacco.com \\
    APP_ENV=staging \\  # or prod
    python scripts/fix_treasury_wallet_link.py --from-email wrong@example.com

Required environment variables
-------------------------------
CROSSMINT_SERVER_API_KEY   Server-side API key from the Crossmint dashboard.
CROSSMINT_WALLET_ADDRESS   The treasury Solana wallet address (base58).
CROSSMINT_TREASURY_EMAIL   Email of the SACCO's Crossmint account.

Optional environment variables
-------------------------------
APP_ENV                    "prod" targets crossmint.com; anything else uses
                           staging.crossmint.com (default: dev → staging).
CROSSMINT_TOKEN_LOCATOR    Token locator used to determine the chain when
                           (re-)linking. Defaults to the Solana devnet USDC
                           locator when APP_ENV != prod.
"""

from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Install it with:  pip install requests")
    sys.exit(1)

_PROD_BASE = "https://www.crossmint.com"
_STAGING_BASE = "https://staging.crossmint.com"
_WALLETS_API_VERSION = "2025-06-09"


def _api_base(app_env: str) -> str:
    return _PROD_BASE if app_env == "prod" else _STAGING_BASE


def _headers(api_key: str) -> dict[str, str]:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": api_key,
    }


def _wallet_url(base: str, email: str, wallet: str) -> str:
    return (
        f"{base}/api/{_WALLETS_API_VERSION}"
        f"/users/{quote(f'email:{email}', safe='')}"
        f"/linked-wallets/{quote(wallet, safe='')}"
    )


def unlink(base: str, api_key: str, email: str, wallet: str) -> None:
    url = _wallet_url(base, email, wallet)
    print(f"  DELETE {url}")
    resp = requests.delete(url, headers=_headers(api_key), timeout=15)
    if resp.status_code in (200, 204):
        print(f"  ✓ Unlinked wallet from {email}")
    elif resp.status_code == 404:
        print(f"  – Wallet was not linked to {email} (404 — nothing to do)")
    else:
        print(f"  ✗ Unexpected status {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)


def link(base: str, api_key: str, email: str, wallet: str, chain: str) -> None:
    url = _wallet_url(base, email, wallet)
    print(f"  PUT {url}")
    resp = requests.put(url, headers=_headers(api_key), json={"chain": chain}, timeout=15)
    if resp.status_code in (200, 201):
        print(f"  ✓ Linked wallet to {email}")
    elif resp.status_code == 409:
        # Verify it is now linked to the correct user.
        print("  409 — wallet already linked somewhere. Verifying …")
        get_resp = requests.get(url, headers=_headers(api_key), timeout=15)
        if get_resp.ok:
            print(f"  ✓ Wallet is already correctly linked to {email}")
        else:
            print(
                "  ✗ 409 but wallet is NOT linked to the treasury account. "
                "You may need to find and remove the existing link from the "
                "Crossmint dashboard (Settings → Wallets → Linked wallets)."
            )
            sys.exit(1)
    else:
        print(f"  ✗ Unexpected status {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unlink treasury wallet from wrong Crossmint user and re-link to treasury."
    )
    parser.add_argument(
        "--from-email",
        required=True,
        metavar="EMAIL",
        help="Email that the treasury wallet is currently (wrongly) linked to.",
    )
    args = parser.parse_args()

    api_key = os.getenv("CROSSMINT_SERVER_API_KEY", "")
    wallet = os.getenv("CROSSMINT_WALLET_ADDRESS", "") or os.getenv("SOLANA_TREASURY_ADDRESS", "")
    treasury_email = os.getenv("CROSSMINT_TREASURY_EMAIL", "")
    app_env = os.getenv("APP_ENV", "dev")
    token_locator = os.getenv("CROSSMINT_TOKEN_LOCATOR", "")
    if not token_locator:
        token_locator = (
            "solana:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            if app_env == "prod"
            else "solana:4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
        )
    chain = token_locator.split(":", 1)[0] if ":" in token_locator else "solana"

    errors: list[str] = []
    if not api_key:
        errors.append("CROSSMINT_SERVER_API_KEY is not set")
    if not wallet:
        errors.append("CROSSMINT_WALLET_ADDRESS (or SOLANA_TREASURY_ADDRESS) is not set")
    if not treasury_email:
        errors.append("CROSSMINT_TREASURY_EMAIL is not set")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        sys.exit(1)

    base = _api_base(app_env)
    from_email = args.from_email

    print(f"\nEnvironment : {app_env} → {base}")
    print(f"Wallet      : {wallet}")
    print(f"Chain       : {chain}")
    print(f"Unlink from : {from_email}")
    print(f"Link to     : {treasury_email}\n")

    if from_email == treasury_email:
        print("--from-email is the same as CROSSMINT_TREASURY_EMAIL; nothing to unlink.")
        print("Verifying current link …")
        url = _wallet_url(base, treasury_email, wallet)
        resp = requests.get(url, headers=_headers(api_key), timeout=15)
        if resp.ok:
            print("✓ Wallet is already correctly linked to the treasury account. No action needed.")
        else:
            print("Wallet is NOT linked to the treasury account. Re-linking …")
            link(base, api_key, treasury_email, wallet, chain)
        return

    print("Step 1 — unlink from wrong account")
    unlink(base, api_key, from_email, wallet)

    print("\nStep 2 — link to treasury account")
    link(base, api_key, treasury_email, wallet, chain)

    print("\nDone. You can now retry /contribute in Telegram.")


if __name__ == "__main__":
    main()
