from src.policies.loan_policy import evaluate_loan_request


def test_membership_age_guardrail() -> None:
    result = evaluate_loan_request(
        member_months=2,
        requested_amount_usd=50,
        pool_total_usd=1000,
        pool_total_lent_usd=100,
        risk_tier="low",
    )
    assert result["eligible"] is False


def test_vote_lane_threshold() -> None:
    result = evaluate_loan_request(
        member_months=6,
        requested_amount_usd=101,
        pool_total_usd=10000,
        pool_total_lent_usd=3000,
        risk_tier="medium",
    )
    assert result["eligible"] is True
    assert result["governance_lane"] == "vote"
