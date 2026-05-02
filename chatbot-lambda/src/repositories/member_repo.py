import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from src.db import get_db

if TYPE_CHECKING:
    from prisma.models import Member
else:
    Member = Any

logger = logging.getLogger(__name__)


class MemberLinkError(RuntimeError):
    pass


class MemberLinkNotFoundError(MemberLinkError):
    pass


class MemberLinkConflictError(MemberLinkError):
    pass


class MemberLinkAmbiguousError(MemberLinkError):
    pass


def normalize_phone_number(phone: str | None) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def _phone_numbers_match(left: str | None, right: str | None) -> bool:
    left_digits = normalize_phone_number(left)
    right_digits = normalize_phone_number(right)
    if not left_digits or not right_digits:
        return False
    if left_digits == right_digits:
        return True
    return len(left_digits) >= 9 and len(right_digits) >= 9 and left_digits[-9:] == right_digits[-9:]


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


def link_member_by_phone(telegram_chat_id: str, phone: str) -> Member:
    db = get_db()
    normalized_phone = normalize_phone_number(phone)
    if not normalized_phone:
        raise MemberLinkConflictError("No phone number was provided.")

    existing_chat_member = db.member.find_unique(where={"telegramChatId": telegram_chat_id})
    matches = [m for m in db.member.find_many() if _phone_numbers_match(m.phone, normalized_phone)]

    if not matches:
        raise MemberLinkNotFoundError("No signup found for that phone number.")

    unique_matches = {member.id: member for member in matches}
    if len(unique_matches) > 1:
        raise MemberLinkAmbiguousError("Multiple accounts matched that phone number.")

    member = next(iter(unique_matches.values()))

    if existing_chat_member is not None and existing_chat_member.id != member.id:
        raise MemberLinkConflictError(
            "This Telegram account is already linked to another SACCO member."
        )

    if member.telegramChatId and member.telegramChatId != telegram_chat_id:
        raise MemberLinkConflictError(
            "That phone number is already linked to another Telegram account."
        )

    if member.telegramChatId == telegram_chat_id and member.phoneVerified:
        return member

    return db.member.update(
        where={"id": member.id},
        data={
            "telegramChatId": telegram_chat_id,
            "phoneVerified": True,
        },
    )


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
