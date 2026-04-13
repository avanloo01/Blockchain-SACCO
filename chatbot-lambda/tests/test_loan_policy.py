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


def test_interest_rate_low_risk_new_member() -> None:
    result = evaluate_loan_request(
        member_months=3,
        requested_amount_usd=50,
        pool_total_usd=10000,
        pool_total_lent_usd=1000,
        risk_tier="low",
    )
    assert result["eligible"] is True
    # Base 8.0 + 0.0 premium - 0.125 loyalty (3 months) = 7.88
    assert result["interest_rate_apr"] == 7.88


def test_interest_rate_medium_risk_veteran() -> None:
    result = evaluate_loan_request(
        member_months=72,
        requested_amount_usd=50,
        pool_total_usd=10000,
        pool_total_lent_usd=1000,
        risk_tier="medium",
    )
    assert result["eligible"] is True
    # Base 8.0 + 4.0 premium - 3.0 loyalty (capped) = 9.0
    assert result["interest_rate_apr"] == 9.0


def test_interest_rate_low_risk_veteran() -> None:
    result = evaluate_loan_request(
        member_months=72,
        requested_amount_usd=50,
        pool_total_usd=10000,
        pool_total_lent_usd=1000,
        risk_tier="low",
    )
    assert result["eligible"] is True
    # Base 8.0 + 0.0 premium - 3.0 loyalty (capped) = 5.0
    assert result["interest_rate_apr"] == 5.0
