from src.handlers.commands import dispatch_command


def test_help_command() -> None:
    message = dispatch_command(chat_id="member_001", text="/help")
    assert "Use /contribute" in message


def test_contribute_with_amount_includes_fee_breakdown() -> None:
    message = dispatch_command(chat_id="member_001", text="/contribute 25")
    assert "Amount: 25.00 USD" in message
    assert "Fee:" in message
    assert "Net to pool:" in message


def test_loan_request_vote_lane_above_threshold() -> None:
    message = dispatch_command(chat_id="member_001", text="/loan_request 101 3")
    assert "Lane: vote" in message


def test_loan_request_auto_lane_at_threshold() -> None:
    message = dispatch_command(chat_id="member_001", text="/loan_request 100 3")
    assert "Lane: auto" in message
