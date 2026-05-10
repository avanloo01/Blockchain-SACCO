#!/usr/bin/env python3
"""Fix treasury wallet linkage in Crossmint after a wallet address change.

When the SACCO rotates its treasury wallet (i.e. a new Solana address replaces
the old one), the old address must be unlinked from the SACCO's Crossmint
account and the new address linked in its place.  The email address of the
Crossmint account does NOT change.

This script:
  1. Unlinks the old wallet address (--old-wallet) from the treasury Crossmint
     account (CROSSMINT_TREASURY_EMAIL).
  2. Links the new wallet address (CROSSMINT_WALLET_ADDRESS) to the same
     treasury Crossmint account.

Usage
-----
Export the required environment variables, then run::

    python scripts/fix_treasury_wallet_link.py --old-wallet <OLD_BASE58_ADDRESS>

Or inline::

    CROSSMINT_SERVER_API_KEY=sk_... \\
    CROSSMINT_WALLET_ADDRESS=<new base58 address> \\
    CROSSMINT_TREASURY_EMAIL=treasury@yoursacco.com \\
    APP_ENV=staging \\  # or prod
    python scripts/fix_treasury_wallet_link.py --old-wallet <OLD_BASE58_ADDRESS>

Required environment variables
-------------------------------
CROSSMINT_SERVER_API_KEY   Server-side API key from the Crossmint dashboard.
CROSSMINT_WALLET_ADDRESS   The *new* treasury Solana wallet address (base58).
                           This is the value stored in the GitHub secret.
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
        description=(
            "Unlink the old treasury wallet address from the Crossmint account "
            "and link the new wallet address (CROSSMINT_WALLET_ADDRESS) in its place."
        )
    )
    parser.add_argument(
        "--old-wallet",
        required=True,
        metavar="ADDRESS",
        help="Old treasury wallet address (base58) to unlink from the Crossmint account.",
    )
    args = parser.parse_args()

    api_key = os.getenv("CROSSMINT_SERVER_API_KEY", "")
    new_wallet = os.getenv("CROSSMINT_WALLET_ADDRESS", "")
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
    if not new_wallet:
        errors.append("CROSSMINT_WALLET_ADDRESS is not set")
    if not treasury_email:
        errors.append("CROSSMINT_TREASURY_EMAIL is not set")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        sys.exit(1)

    old_wallet = args.old_wallet
    base = _api_base(app_env)

    print(f"\nEnvironment  : {app_env} → {base}")
    print(f"Treasury email: {treasury_email}")
    print(f"Chain        : {chain}")
    print(f"Old wallet   : {old_wallet}")
    print(f"New wallet   : {new_wallet}\n")

    if old_wallet == new_wallet:
        print("--old-wallet is the same as CROSSMINT_WALLET_ADDRESS; nothing to swap.")
        print("Verifying current link …")
        url = _wallet_url(base, treasury_email, new_wallet)
        resp = requests.get(url, headers=_headers(api_key), timeout=15)
        if resp.ok:
            print("✓ Wallet is already correctly linked to the treasury account. No action needed.")
        else:
            print("Wallet is NOT linked to the treasury account. Linking …")
            link(base, api_key, treasury_email, new_wallet, chain)
        return

    print("Step 1 — unlink old wallet from treasury account")
    unlink(base, api_key, treasury_email, old_wallet)

    print("\nStep 2 — link new wallet to treasury account")
    link(base, api_key, treasury_email, new_wallet, chain)

    print("\nDone. You can now retry /contribute in Telegram.")


if __name__ == "__main__":
    main()
