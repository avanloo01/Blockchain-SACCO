"""Crossmint payment adapter.

Creates contribution checkout links by calling the Crossmint Orders API
server-side.  The returned orderId and clientSecret are embedded in the
checkout URL so the frontend can display the pre-created order for the
member to complete.  The orderId is also stored as the billing intent
idempotency key so the Telegram /verify command can look it up directly.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, urlencode

import requests

from src.config import settings
from src.services.payments.base import (
    PaymentIntent,
    PaymentProvider,
    PaymentStatus,
    SettlementResult,
)

logger = logging.getLogger(__name__)

_CROSSMINT_PROD_BASE = "https://www.crossmint.com"
_CROSSMINT_STAGING_BASE = "https://staging.crossmint.com"

# Crossmint API versions
_ORDERS_API_VERSION = "2022-06-09"
_WALLETS_API_VERSION = "2025-06-09"


def _read_error_message(response: requests.Response) -> str:
    fallback = f"Crossmint API error: {response.status_code} {response.reason}"
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return f"{fallback} - {text}" if text else fallback

    if not isinstance(payload, dict):
        return fallback

    parts: list[str] = []
    message = payload.get("message")
    if isinstance(message, str) and message:
        parts.append(message)
    error = payload.get("error")
    if isinstance(error, str) and error and error not in parts:
        parts.append(error)
    errors = payload.get("errors")
    if isinstance(errors, list):
        for item in errors:
            if isinstance(item, str) and item and item not in parts:
                parts.append(item)

    if not parts:
        return fallback
    return f"{fallback} - {' | '.join(parts)}"


def _format_usd(amount_usd: float) -> str:
    return f"{amount_usd:.2f}"


class CrossmintProvider(PaymentProvider):
    """Crossmint headless checkout provider for USDC contribution flows."""

    def _api_base(self) -> str:
        if settings.app_env == "prod":
            return _CROSSMINT_PROD_BASE
        return _CROSSMINT_STAGING_BASE

    def _headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": settings.crossmint_server_api_key,
        }

    def _build_checkout_url(self, *, order_id: str, client_secret: str) -> str:
        base_url = settings.website_url.rstrip("/")
        params = urlencode({"orderId": order_id, "clientSecret": client_secret})
        return f"{base_url}/checkout/crossmint?{params}"

    def _link_wallet(
        self,
        *,
        user_email: str,
        wallet_address: str,
        chain: str,
    ) -> None:
        """Link an external wallet to a Crossmint user.

        Required by the Crossmint Onramp API before creating an order for an
        external (non-Crossmint) wallet.  Safe to call repeatedly for the same
        user/wallet pair.
        """
        user_locator = quote(f"email:{user_email}", safe="")
        wallet_encoded = quote(wallet_address, safe="")
        url = (
            f"{self._api_base()}/api/{_WALLETS_API_VERSION}"
            f"/users/{user_locator}/linked-wallets/{wallet_encoded}"
        )
        try:
            response = requests.put(
                url,
                headers=self._headers(),
                json={"chain": chain},
                timeout=15,
            )
            if response.status_code == 409:
                # Wallet is already linked to a Crossmint user — that is fine;
                # it means a previous setup call succeeded.  Log and continue.
                logger.info(
                    "Treasury wallet already linked to a Crossmint user (409); proceeding."
                )
                return
            if not response.ok:
                raise ValueError(_read_error_message(response))
        except requests.RequestException as exc:
            raise ValueError(f"Crossmint API error linking wallet: {exc}") from exc

    def create_payment_intent(
        self,
        amount_usd: float,
        member_id: str,
        idempotency_key: str | None = None,
        receipt_email: str | None = None,
    ) -> PaymentIntent:
        """Create a Crossmint order server-side and return a checkout link.

        Calls the Crossmint Orders API to obtain an orderId and clientSecret,
        then builds a URL pointing to the embedded checkout page so the member
        can complete payment.  The orderId is used as the billing intent
        idempotency key so /verify can look it up directly.
        """
        api_key = settings.crossmint_server_api_key
        if not api_key:
            raise ValueError("CROSSMINT_SERVER_API_KEY is not configured")

        treasury = settings.crossmint_wallet_address
        if not treasury:
            raise ValueError("CROSSMINT_WALLET_ADDRESS is not configured")

        if not receipt_email:
            raise ValueError("Member is missing an email address. Cannot create Crossmint order.")

        token_locator = settings.crossmint_token_locator
        fee_usd = round(amount_usd * settings.service_fee_percent / 100.0, 2)
        net_pool = round(amount_usd - fee_usd, 2)

        chain = token_locator.split(":", 1)[0] if ":" in token_locator else "solana"
        # Attempt to link the treasury wallet.  If the wallet is already linked
        # to any Crossmint user (HTTP 409), that is fine — the order can still
        # be fulfilled.  The recipient.walletAddress field in the order payload
        # is what Crossmint uses to route funds; the link step is only needed
        # the very first time Crossmint sees an external wallet.
        self._link_wallet(
            user_email=receipt_email,
            wallet_address=treasury,
            chain=chain,
        )

        payload: dict[str, Any] = {
            "lineItems": [
                {
                    "tokenLocator": token_locator,
                    "executionParameters": {
                        "mode": "exact-in",
                        "amount": _format_usd(amount_usd),
                        "slippageBps": settings.crossmint_slippage_bps,
                    },
                }
            ],
            "recipient": {"walletAddress": treasury},
            "payment": {"method": "card", "receiptEmail": receipt_email},
        }

        extra_headers: dict[str, str] = {}
        if idempotency_key:
            extra_headers["Idempotency-Key"] = idempotency_key

        try:
            response = requests.post(
                f"{self._api_base()}/api/{_ORDERS_API_VERSION}/orders",
                headers={**self._headers(), **extra_headers},
                json=payload,
                timeout=15,
            )
            if not response.ok:
                raise ValueError(_read_error_message(response))
            data = response.json()
        except requests.RequestException as exc:
            raise ValueError(f"Crossmint API error: {exc}") from exc

        order_id: str = data["order"]["orderId"]
        client_secret: str = data["clientSecret"]

        payment_url = self._build_checkout_url(
            order_id=order_id,
            client_secret=client_secret,
        )

        return PaymentIntent(
            intent_id=order_id,
            member_id=member_id,
            amount_usd=amount_usd,
            service_fee_usd=fee_usd,
            net_pool_amount_usd=net_pool,
            asset="USDC",
            network=token_locator.split(":", 1)[0] if token_locator else "solana",
            status=PaymentStatus.PENDING,
            recipient_address=treasury,
            memo=None,
            payment_url=payment_url,
        )

    def verify_payment_settlement(
        self,
        intent_id: str,
        tx_signature: str,
    ) -> SettlementResult:
        del tx_signature

        api_key = settings.crossmint_server_api_key
        if not api_key:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error="CROSSMINT_SERVER_API_KEY is not configured",
            )

        order_id = quote(intent_id, safe="")
        try:
            response = requests.get(
                f"{self._api_base()}/api/{_ORDERS_API_VERSION}/orders/{order_id}",
                headers={
                    "accept": "application/json",
                    "x-api-key": api_key,
                },
                timeout=15,
            )
            response.raise_for_status()
            order = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("Crossmint API error verifying %s: %s", intent_id, exc)
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error=str(exc),
            )

        if not isinstance(order, dict):
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error="Crossmint verification returned an unexpected payload",
            )

        payment = order.get("payment") if isinstance(order.get("payment"), dict) else {}
        line_items = order.get("lineItems") if isinstance(order.get("lineItems"), list) else []
        first_line_item = line_items[0] if line_items and isinstance(line_items[0], dict) else {}
        delivery = first_line_item.get("delivery") if isinstance(first_line_item.get("delivery"), dict) else {}

        phase = str(order.get("phase", "")).lower()
        payment_status = str(payment.get("status", "")).lower()
        delivery_status = str(delivery.get("status", "")).lower()
        delivery_tx = delivery.get("txId") if isinstance(delivery.get("txId"), str) else None
        refunded = payment.get("refunded") if isinstance(payment.get("refunded"), dict) else None

        if phase == "completed" or delivery_status == "completed":
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.CONFIRMED,
                tx_signature=delivery_tx or intent_id,
            )

        if refunded is not None:
            refund_amount = refunded.get("amount")
            refund_currency = refunded.get("currency")
            refund_detail = ""
            if isinstance(refund_amount, str) and isinstance(refund_currency, str):
                refund_detail = f" ({refund_amount} {refund_currency})"
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                tx_signature=delivery_tx or intent_id,
                error=f"Crossmint payment was refunded{refund_detail}",
            )

        if delivery_status == "failed" or payment_status in {"failed", "failed-kyc"}:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                tx_signature=delivery_tx or intent_id,
                error=f"Crossmint order status: {payment_status or delivery_status}",
            )

        return SettlementResult(
            intent_id=intent_id,
            status=PaymentStatus.PENDING,
            tx_signature=delivery_tx or intent_id,
        )