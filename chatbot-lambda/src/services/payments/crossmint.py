"""Crossmint payment adapter.

Creates contribution checkout links and verifies settlement by polling the
Crossmint headless order API. Orders are created server-side via the Crossmint
Orders API; the returned orderId and clientSecret are embedded in the checkout
URL so the frontend can display the pre-configured embedded checkout.
"""

from __future__ import annotations

import logging
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

    def create_payment_intent(
        self,
        amount_usd: float,
        member_id: str,
        idempotency_key: str | None = None,
        receipt_email: str | None = None,
    ) -> PaymentIntent:
        """Create a server-side Crossmint order and return a checkout link.

        The Crossmint order is created via the Crossmint Orders API.  The
        returned orderId is stored as the billing intent idempotency key so
        the Telegram /verify command can look it up directly.  The clientSecret
        is embedded in the checkout URL so the embedded checkout component can
        display the pre-configured order without re-specifying line items.
        """
        api_key = settings.crossmint_server_api_key
        if not api_key:
            raise ValueError("CROSSMINT_SERVER_API_KEY is not configured")

        treasury = settings.crossmint_wallet_address
        if not treasury:
            raise ValueError("CROSSMINT_WALLET_ADDRESS is not configured")

        if not receipt_email:
            raise ValueError(
                "Crossmint checkout requires a member with a verified email; "
                "this member is missing an email address"
            )

        token_locator = settings.crossmint_token_locator
        fee_usd = round(amount_usd * settings.service_fee_percent / 100.0, 2)
        net_pool = round(amount_usd - fee_usd, 2)

        payload = {
            "lineItems": [
                {
                    "tokenLocator": token_locator,
                    "executionParameters": {
                        "mode": "exact-in",
                        "amount": _format_usd(amount_usd),
                        "maxSlippageBps": settings.crossmint_slippage_bps,
                    },
                }
            ],
            "recipient": {"walletAddress": treasury},
            "payment": {"receiptEmail": receipt_email},
        }

        try:
            response = requests.post(
                f"{self._api_base()}/api/2022-06-09/orders",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if not response.ok:
                raise ValueError(_read_error_message(response))
            data = response.json()
        except requests.RequestException as exc:
            raise ValueError(f"Crossmint API error: {exc}") from exc

        client_secret: str = data.get("clientSecret") or ""
        if not client_secret:
            raise ValueError("Crossmint API response is missing clientSecret")

        order_data = data.get("order") if isinstance(data.get("order"), dict) else {}
        order_id: str = order_data.get("orderId") or ""
        if not order_id:
            raise ValueError("Crossmint API response is missing orderId")

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
            recipient_address=treasury or None,
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
                f"{self._api_base()}/api/2022-06-09/orders/{order_id}",
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