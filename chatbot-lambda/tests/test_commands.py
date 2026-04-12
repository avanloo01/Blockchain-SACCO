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
    assert "/contribute" in message
    assert "/verify" in message
    assert "/proposals" in message
    assert "/vote" in message
    assert "/status" in message


@patch("src.handlers.commands.get_member_by_chat_id", return_value=None)
def test_unregistered_user_gets_signup_prompt(_mock_member) -> None:
    message = dispatch_command(chat_id="999", text="/contribute 25")
    assert "sign up" in message.lower()


@patch("src.handlers.commands.create_billing_intent")
@patch("src.handlers.commands.get_payment_provider")
@patch("src.handlers.commands.get_member_by_chat_id")
def test_contribute_with_amount_includes_fee_breakdown(mock_member, mock_provider, _mock_billing) -> None:
    mock_member.return_value = _fake_member()
    from src.services.payments.base import PaymentIntent, PaymentStatus
    mock_provider.return_value.create_payment_intent.return_value = PaymentIntent(
        intent_id="test-intent",
        member_id="123",
        amount_usd=25.0,
        service_fee_usd=0.25,
        net_pool_amount_usd=24.75,
        asset="USDC",
        network="solana_devnet",
        status=PaymentStatus.PENDING,
        recipient_address="TreasuryABC",
        memo="sacco:test-intent",
        payment_url="solana:TreasuryABC?amount=25.0",
    )
    message = dispatch_command(chat_id="123", text="/contribute 25")
    assert "25.00 USDC" in message
    assert "Fee:" in message
    assert "Net to pool:" in message
    assert "TreasuryABC" in message
    assert "/verify" in message


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


@patch("src.handlers.commands.list_open_vote_loans")
@patch("src.handlers.commands.get_member_by_chat_id")
def test_proposals_command(mock_member, mock_proposals) -> None:
    mock_member.return_value = _fake_member()
    mock_proposals.return_value = [
        {
            "loan_id": "loan-12345678",
            "amount_usd": 150.0,
            "tenure_months": 4,
            "created_on": "2026-04-07",
        }
    ]
    message = dispatch_command(chat_id="123", text="/proposals")
    assert "Active governance proposals" in message
    assert "loan-123" in message
    assert "Vote with" in message


@patch("src.handlers.commands.get_vote_tally")
@patch("src.handlers.commands.cast_vote")
@patch("src.handlers.commands.get_member_by_chat_id")
def test_vote_command_records_vote(mock_member, _cast_vote, mock_tally) -> None:
    mock_member.return_value = _fake_member(id="mem-001")
    mock_tally.return_value = {"yes": 2, "no": 1, "total": 3}
    message = dispatch_command(chat_id="123", text="/vote loan-1 yes")
    assert "Vote recorded: YES" in message
    assert "Yes: 2" in message


@patch("src.handlers.commands.get_member_by_chat_id")
def test_vote_command_rejects_invalid_choice(mock_member) -> None:
    mock_member.return_value = _fake_member(id="mem-001")
    message = dispatch_command(chat_id="123", text="/vote loan-1 maybe")
    assert "Invalid vote" in message
