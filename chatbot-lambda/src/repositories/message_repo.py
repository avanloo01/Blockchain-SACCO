import logging
from typing import TYPE_CHECKING, Any

from src.db import get_db

if TYPE_CHECKING:
    from prisma.models import MessageDelivery
else:
    MessageDelivery = Any

logger = logging.getLogger(__name__)


def record_delivery(
    member_id: str,
    campaign: str,
    message_text: str,
    telegram_msg_id: str | None = None,
    status: str = "sent",
) -> MessageDelivery:
    db = get_db()
    row = db.messagedelivery.create(
        data={
            "memberId": member_id,
            "campaign": campaign,
            "messageText": message_text,
            "telegramMsgId": telegram_msg_id,
            "status": status,
        }
    )
    logger.info("Message delivery recorded id=%s campaign=%s member=%s", row.id, campaign, member_id)
    return row
