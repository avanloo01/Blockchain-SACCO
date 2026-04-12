"""Transak payment adapter.

Generates Transak widget URLs so members can pay via fiat or crypto.
Verification queries the Transak REST API for order status.
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

_TRANSAK_WIDGET_BASE = "https://global.transak.com"
_TRANSAK_API_BASE = "https://api.transak.com/api/v2"


class TransakProvider(PaymentProvider):
    """Transak fiat/crypto on-ramp payment provider."""

    def create_payment_intent(
        self,
        amount_usd: float,
        member_id: str,
        idempotency_key: str | None = None,
    ) -> PaymentIntent:
        api_key = settings.transak_api_key
        if not api_key:
            raise ValueError("TRANSAK_API_KEY is not configured")

        treasury = settings.transak_wallet_address
        if not treasury:
            raise ValueError("TRANSAK_WALLET_ADDRESS is not configured")

        fee_usd = round(amount_usd * settings.service_fee_percent / 100.0, 2)
        net_pool = round(amount_usd - fee_usd, 2)
        intent_id = idempotency_key or str(uuid.uuid4())

        params = {
            "apiKey": api_key,
            "cryptoCurrencyCode": settings.transak_crypto_currency,
            "network": settings.transak_network,
            "walletAddress": treasury,
            "fiatAmount": amount_usd,
            "fiatCurrency": "USD",
            "disableWalletAddressForm": "true",
            "partnerOrderId": intent_id,
        }
        payment_url = f"{_TRANSAK_WIDGET_BASE}?{urlencode(params)}"

        return PaymentIntent(
            intent_id=intent_id,
            member_id=member_id,
            amount_usd=amount_usd,
            service_fee_usd=fee_usd,
            net_pool_amount_usd=net_pool,
            asset=settings.transak_crypto_currency,
            network=settings.transak_network,
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
        api_key = settings.transak_api_key
        if not api_key:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error="TRANSAK_API_KEY is not configured",
            )

        url = f"{_TRANSAK_API_BASE}/order/{tx_signature}"
        headers = {"accept": "application/json"}
        params = {"partnerAPISecret": api_key}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("Transak API error verifying %s: %s", tx_signature, exc)
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error=str(exc),
            )

        order = data.get("response", {})
        transak_status = order.get("status", "").upper()

        if transak_status == "COMPLETED":
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.CONFIRMED,
                tx_signature=tx_signature,
            )
        elif transak_status in ("PENDING_DELIVERY_FROM_TRANSAK", "PROCESSING", "PENDING"):
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.PENDING,
                tx_signature=tx_signature,
            )
        elif transak_status in ("FAILED", "REFUNDED", "CANCELLED", "EXPIRED"):
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                tx_signature=tx_signature,
                error=f"Transak order status: {transak_status}",
            )
        else:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.PENDING,
                tx_signature=tx_signature,
            )
