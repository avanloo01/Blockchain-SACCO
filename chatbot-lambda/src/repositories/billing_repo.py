import logging

from prisma.models import BillingIntent

from src.db import get_db

logger = logging.getLogger(__name__)


def create_billing_intent(
    member_id: str,
    amount_usd: float,
    service_fee_usd: float,
    net_pool_amount_usd: float,
    idempotency_key: str | None = None,
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
