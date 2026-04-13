"""MoonPay payment adapter.

Generates MoonPay on-ramp widget URLs so members can buy crypto via fiat.
Verification queries the MoonPay REST API for transaction status.
"""

import logging
import uuid
from urllib.parse import urlencode

import requests

from src.config import settings
from src.services.payments.base import (
    PaymentIntent,
    PaymentProvider,
    PaymentStatus,
    SettlementResult,
)

logger = logging.getLogger(__name__)

_MOONPAY_WIDGET_BASE = "https://buy.moonpay.com"
_MOONPAY_SANDBOX_WIDGET_BASE = "https://buy-sandbox.moonpay.com"
_MOONPAY_API_BASE = "https://api.moonpay.com/v1"


class MoonpayProvider(PaymentProvider):
    """MoonPay fiat-to-crypto on-ramp payment provider."""

    def _widget_base(self) -> str:
        if settings.app_env == "prod":
            return _MOONPAY_WIDGET_BASE
        return _MOONPAY_SANDBOX_WIDGET_BASE

    def create_payment_intent(
        self,
        amount_usd: float,
        member_id: str,
        idempotency_key: str | None = None,
    ) -> PaymentIntent:
        api_key = settings.moonpay_api_key
        if not api_key:
            raise ValueError("MOONPAY_API_KEY is not configured")

        treasury = settings.moonpay_wallet_address
        if not treasury:
            raise ValueError("MOONPAY_WALLET_ADDRESS is not configured")

        fee_usd = round(amount_usd * settings.service_fee_percent / 100.0, 2)
        net_pool = round(amount_usd - fee_usd, 2)
        intent_id = idempotency_key or str(uuid.uuid4())

        params = {
            "apiKey": api_key,
            "currencyCode": settings.moonpay_currency_code,
            "walletAddress": treasury,
            "baseCurrencyCode": "usd",
            "baseCurrencyAmount": amount_usd,
            "externalTransactionId": intent_id,
            "externalCustomerId": member_id,
            "lockAmount": "true",
        }
        payment_url = f"{self._widget_base()}?{urlencode(params)}"

        return PaymentIntent(
            intent_id=intent_id,
            member_id=member_id,
            amount_usd=amount_usd,
            service_fee_usd=fee_usd,
            net_pool_amount_usd=net_pool,
            asset=settings.moonpay_currency_code.upper(),
            network=settings.moonpay_network,
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
        api_key = settings.moonpay_secret_key
        if not api_key:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error="MOONPAY_SECRET_KEY is not configured",
            )

        url = f"{_MOONPAY_API_BASE}/transactions/ext/{tx_signature}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Api-Key {api_key}",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("MoonPay API error verifying %s: %s", tx_signature, exc)
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error=str(exc),
            )

        # The external ID endpoint returns an array; take the first match.
        if isinstance(data, list):
            if not data:
                return SettlementResult(
                    intent_id=intent_id,
                    status=PaymentStatus.PENDING,
                    tx_signature=tx_signature,
                )
            order = data[0]
        else:
            order = data

        moonpay_status = order.get("status", "").lower()

        if moonpay_status == "completed":
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.CONFIRMED,
                tx_signature=tx_signature,
                settled_amount=order.get("quoteCurrencyAmount"),
            )
        elif moonpay_status in ("waitingpayment", "pending", "waitingauthorization"):
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.PENDING,
                tx_signature=tx_signature,
            )
        elif moonpay_status == "failed":
            failure_reason = order.get("failureReason", "unknown")
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                tx_signature=tx_signature,
                error=f"MoonPay transaction status: failed ({failure_reason})",
            )
        else:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.PENDING,
                tx_signature=tx_signature,
            )
