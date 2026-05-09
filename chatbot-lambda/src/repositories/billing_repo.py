import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from src.db import get_db

if TYPE_CHECKING:
    from prisma.models import BillingIntent
else:
    BillingIntent = Any

logger = logging.getLogger(__name__)


def create_billing_intent(
    member_id: str,
    amount_usd: float,
    service_fee_usd: float,
    net_pool_amount_usd: float,
    idempotency_key: str | None = None,
    recipient_address: str | None = None,
    memo: str | None = None,
    payment_url: str | None = None,
    network: str = "solana_devnet",
) -> BillingIntent:
    """Persist a new billing intent. Idempotency key prevents duplicates."""
    db = get_db()
    if idempotency_key:
        existing = db.billingintent.find_unique(where={"idempotencyKey": idempotency_key})
        if existing is not None:
            logger.info("Duplicate billing intent idempotency_key=%s", idempotency_key)
            return existing

    intent = db.billingintent.create(
        data={
            "memberId": member_id,
            "amountUsd": amount_usd,
            "serviceFeeUsd": service_fee_usd,
            "netPoolAmountUsd": net_pool_amount_usd,
            "idempotencyKey": idempotency_key,
            "recipientAddress": recipient_address,
            "memo": memo,
            "paymentUrl": payment_url,
            "network": network,
        }
    )
    logger.info("Billing intent created id=%s member=%s amount=%.2f", intent.id, member_id, amount_usd)
    return intent


def update_billing_status(intent_id: str, status: str) -> BillingIntent:
    db = get_db()
    return db.billingintent.update(
        where={"id": intent_id},
        data={"status": status},
    )


def mark_billing_settled(intent_id: str, tx_signature: str) -> BillingIntent:
    """Mark a billing intent as confirmed after on-chain settlement."""
    db = get_db()
    return db.billingintent.update(
        where={"id": intent_id},
        data={
            "status": "confirmed",
            "txSignature": tx_signature,
            "settledAt": datetime.now(timezone.utc),
        },
    )


def get_pending_billing_intents() -> list[BillingIntent]:
    """Return all billing intents still awaiting settlement."""
    db = get_db()
    return db.billingintent.find_many(
        where={"status": "pending"},
        order={"createdAt": "asc"},
        include={"member": True},
    )


def get_billing_intent_by_idempotency_key(key: str) -> BillingIntent | None:
    db = get_db()
    return db.billingintent.find_unique(where={"idempotencyKey": key})


def get_billing_intent_by_memo(memo: str) -> BillingIntent | None:
    """Return the most recent pending billing intent with the given memo value."""
    db = get_db()
    return db.billingintent.find_first(
        where={"memo": memo, "status": "pending"},
        order={"createdAt": "desc"},
    )


def link_crossmint_order_id(idempotency_key: str, crossmint_order_id: str) -> bool:
    """Store the live Crossmint orderId in the memo column so /verify can look it up.

    Returns True if the record was found and updated, False otherwise.
    """
    db = get_db()
    existing = db.billingintent.find_unique(where={"idempotencyKey": idempotency_key})
    if existing is None:
        logger.warning("link_crossmint_order_id: no billing intent for key=%s", idempotency_key)
        return False
    db.billingintent.update(
        where={"id": existing.id},
        data={"memo": crossmint_order_id},
    )
    logger.info(
        "Linked Crossmint orderId=%s to billing intent id=%s", crossmint_order_id, existing.id
    )
    return True
