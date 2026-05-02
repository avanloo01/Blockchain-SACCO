from unittest.mock import MagicMock, patch

from src.repositories.member_repo import MemberLinkNotFoundError, link_member_by_phone


def _fake_member(**overrides):
    member = MagicMock()
    defaults = {
        "id": "mem-1",
        "phone": "+254 700 000000",
        "telegramChatId": None,
        "phoneVerified": False,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(member, key, value)
    return member


@patch("src.repositories.member_repo.get_db")
def test_link_member_by_phone_matches_country_code_variants(mock_get_db) -> None:
    db = MagicMock()
    mock_get_db.return_value = db
    db.member.find_unique.return_value = None
    db.member.find_many.return_value = [_fake_member(phone="0700 000000")]
    updated_member = _fake_member(phone="0700 000000", telegramChatId="123", phoneVerified=True)
    db.member.update.return_value = updated_member

    member = link_member_by_phone(telegram_chat_id="123", phone="+254700000000")

    assert member.telegramChatId == "123"
    assert member.phoneVerified is True
    db.member.update.assert_called_once_with(
        where={"id": "mem-1"},
        data={"telegramChatId": "123", "phoneVerified": True},
    )


@patch("src.repositories.member_repo.get_db")
def test_link_member_by_phone_raises_when_signup_missing(mock_get_db) -> None:
    db = MagicMock()
    mock_get_db.return_value = db
    db.member.find_unique.return_value = None
    db.member.find_many.return_value = []

    try:
        link_member_by_phone(telegram_chat_id="123", phone="+254700000000")
        assert False, "Expected MemberLinkNotFoundError"
    except MemberLinkNotFoundError:
        pass