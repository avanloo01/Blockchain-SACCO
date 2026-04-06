import logging
from datetime import datetime, timezone

from prisma.models import Member

from src.db import get_db

logger = logging.getLogger(__name__)


def get_or_create_member(telegram_chat_id: str, display_name: str | None = None) -> Member:
    """Find a member by Telegram chat ID, or create one if not found."""
    db = get_db()
    member = db.member.find_unique(where={"telegramChatId": telegram_chat_id})
    if member is not None:
        return member
    member = db.member.create(
        data={
            "telegramChatId": telegram_chat_id,
            "displayName": display_name,
        }
    )
    logger.info("Created new member id=%s chat_id=%s", member.id, telegram_chat_id)
    return member


def get_member_by_chat_id(telegram_chat_id: str) -> Member | None:
    db = get_db()
    return db.member.find_unique(where={"telegramChatId": telegram_chat_id})


def get_active_member_ids() -> list[str]:
    """Return Telegram chat IDs for all members."""
    db = get_db()
    members = db.member.find_many()
    return [m.telegramChatId for m in members]


def get_member_months(member: Member) -> int:
    """Number of full months since the member joined."""
    now = datetime.now(timezone.utc)
    joined = member.joinedOn.replace(tzinfo=timezone.utc) if member.joinedOn.tzinfo is None else member.joinedOn
    delta = now - joined
    return max(delta.days // 30, 0)


def add_contribution(telegram_chat_id: str, amount_usd: float) -> Member:
    """Increment a member's contribution total."""
    db = get_db()
    return db.member.update(
        where={"telegramChatId": telegram_chat_id},
        data={"contributionTotalUsd": {"increment": amount_usd}},
    )
