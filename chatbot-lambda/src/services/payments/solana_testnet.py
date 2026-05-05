"""Solana devnet/testnet USDC payment adapter.

Builds a transfer intent with the SACCO treasury wallet address so the
member can send USDC on Solana devnet. Verification queries the Solana
JSON-RPC endpoint to confirm the transaction signature.
"""

import logging
import uuid

import requests

from src.config import settings
from src.services.payments.base import (
    PaymentIntent,
    PaymentProvider,
    PaymentStatus,
    SettlementResult,
)

logger = logging.getLogger(__name__)

# Solana devnet USDC mint (SPL token used on devnet for testing).
_DEVNET_USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"


class SolanaTestnetProvider(PaymentProvider):
    """Solana devnet/testnet USDC transfer intent provider."""

    def create_payment_intent(
        self,
        amount_usd: float,
        member_id: str,
        idempotency_key: str | None = None,
        receipt_email: str | None = None,
    ) -> PaymentIntent:
        del receipt_email
        fee_usd = round(amount_usd * settings.service_fee_percent / 100.0, 2)
        net_pool = round(amount_usd - fee_usd, 2)
        intent_id = idempotency_key or str(uuid.uuid4())

        treasury = settings.solana_treasury_address
        if not treasury:
            raise ValueError("SOLANA_TREASURY_ADDRESS is not configured")

        memo = f"sacco:{intent_id}"

        # Build a Solana Pay URL for easy wallet integration.
        # Spec: https://docs.solanapay.com/spec#transfer-request
        payment_url = (
            f"solana:{treasury}"
            f"?amount={amount_usd}"
            f"&spl-token={_DEVNET_USDC_MINT}"
            f"&reference={intent_id}"
            f"&memo={memo}"
        )

        return PaymentIntent(
            intent_id=intent_id,
            member_id=member_id,
            amount_usd=amount_usd,
            service_fee_usd=fee_usd,
            net_pool_amount_usd=net_pool,
            asset="USDC",
            network="solana_devnet",
            status=PaymentStatus.PENDING,
            recipient_address=treasury,
            memo=memo,
            payment_url=payment_url,
        )

    def verify_payment_settlement(
        self,
        intent_id: str,
        tx_signature: str,
    ) -> SettlementResult:
        rpc_url = settings.solana_rpc_url
        if not rpc_url:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error="SOLANA_RPC_URL is not configured",
            )

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                tx_signature,
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
            ],
        }

        try:
            resp = requests.post(rpc_url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("Solana RPC error verifying %s: %s", tx_signature, exc)
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error=str(exc),
            )

        result = data.get("result")
        if result is None:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.PENDING,
                tx_signature=tx_signature,
            )

        meta = result.get("meta", {})
        if meta.get("err") is not None:
            return SettlementResult(
                intent_id=intent_id,
                status=PaymentStatus.FAILED,
                tx_signature=tx_signature,
                error=str(meta["err"]),
            )

        return SettlementResult(
            intent_id=intent_id,
            status=PaymentStatus.CONFIRMED,
            tx_signature=tx_signature,
        )
