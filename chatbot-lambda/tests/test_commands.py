from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.handlers.commands import dispatch_command


def _fake_member(**overrides):
    defaults = {
        "id": "mem-001",
        "telegramChatId": "123",
        "displayName": None,
        "joinedOn": datetime(2025, 12, 1, tzinfo=timezone.utc),
        "emailVerified": False,
        "phoneVerified": False,
        "contributionTotalUsd": 100.0,
        "repaymentOnTimeRatio": 1.0,
        "createdAt": datetime(2025, 12, 1, tzinfo=timezone.utc),
        "updatedAt": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


def test_start_command_shows_signup_link() -> None:
    message = dispatch_command(chat_id="123", text="/start")
    assert "sign up" in message.lower()
    assert "/signup" in message


def test_help_command() -> None:
    message = dispatch_command(chat_id="123", text="/help")
    assert "Use /contribute" in message
    assert "/status" in message


@patch("src.handlers.commands.get_member_by_chat_id", return_value=None)
def test_unregistered_user_gets_signup_prompt(_mock_member) -> None:
    message = dispatch_command(chat_id="999", text="/contribute 25")
    assert "sign up" in message.lower()


@patch("src.handlers.commands.create_billing_intent")
@patch("src.handlers.commands.get_member_by_chat_id")
def test_contribute_with_amount_includes_fee_breakdown(mock_member, _mock_billing) -> None:
    mock_member.return_value = _fake_member()
    message = dispatch_command(chat_id="123", text="/contribute 25")
    assert "Amount: 25.00 USD" in message
    assert "Fee:" in message
    assert "Net to pool:" in message


@patch("src.handlers.commands.generate_repayment_schedule")
@patch("src.handlers.commands.create_loan_request")
@patch("src.handlers.commands.get_pool_state", return_value={"total_balance_usd": 10000.0, "total_lent_out_usd": 5000.0})
@patch("src.handlers.commands.get_member_months", return_value=4)
@patch("src.handlers.commands.get_member_by_chat_id")
def test_loan_request_vote_lane_above_threshold(mock_member, _mm, _ps, mock_create, _rs) -> None:
    mock_member.return_value = _fake_member()
    mock_create.return_value = MagicMock(id="loan-1", amountUsd=101, tenureMonths=3, memberId="mem-001")
    message = dispatch_command(chat_id="123", text="/loan_request 101 3")
    assert "Lane: vote" in message


@patch("src.handlers.commands.generate_repayment_schedule")
@patch("src.handlers.commands.create_loan_request")
@patch("src.handlers.commands.get_pool_state", return_value={"total_balance_usd": 10000.0, "total_lent_out_usd": 5000.0})
@patch("src.handlers.commands.get_member_months", return_value=4)
@patch("src.handlers.commands.get_member_by_chat_id")
def test_loan_request_auto_lane_at_threshold(mock_member, _mm, _ps, mock_create, _rs) -> None:
    mock_member.return_value = _fake_member()
    mock_create.return_value = MagicMock(id="loan-2", amountUsd=100, tenureMonths=3, memberId="mem-001")
    message = dispatch_command(chat_id="123", text="/loan_request 100 3")
    assert "Lane: auto" in message


@patch("src.handlers.commands.get_member_months", return_value=4)
@patch("src.handlers.commands.get_member_by_chat_id")
def test_status_command(mock_member, _mm) -> None:
    mock_member.return_value = _fake_member(contributionTotalUsd=250.0)
    message = dispatch_command(chat_id="123", text="/status")
    assert "250.00 USD" in message
    assert "Months active:" in message
