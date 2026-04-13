from src.config import settings

# Interest rate constants (APR)
_BASE_RATE = 8.0
_RISK_PREMIUM = {"low": 0.0, "medium": 4.0}
_LOYALTY_DISCOUNT_PER_YEAR = 0.5
_LOYALTY_DISCOUNT_CAP = 3.0
_MIN_APR = 3.0
_MAX_APR = 15.0


def _calculate_interest_rate(risk_tier: str, member_months: int) -> float:
    """Base rate + risk premium - loyalty discount, clamped to [MIN_APR, MAX_APR]."""
    premium = _RISK_PREMIUM.get(risk_tier, 0.0)
    loyalty = min(member_months / 12 * _LOYALTY_DISCOUNT_PER_YEAR, _LOYALTY_DISCOUNT_CAP)
    rate = _BASE_RATE + premium - loyalty
    return round(max(_MIN_APR, min(_MAX_APR, rate)), 2)


def evaluate_loan_request(
    member_months: int,
    requested_amount_usd: float,
    pool_total_usd: float,
    pool_total_lent_usd: float,
    risk_tier: str,
) -> dict[str, float | str | bool]:
    if member_months < 3:
        return {"eligible": False, "reason": "minimum membership is 3 months"}

    utilization_percent_after = ((pool_total_lent_usd + requested_amount_usd) / pool_total_usd) * 100
    if utilization_percent_after > settings.pool_utilization_cap_percent:
        return {"eligible": False, "reason": "pool utilization cap would be exceeded"}

    if risk_tier not in {"low", "medium"}:
        return {"eligible": False, "reason": "risk tier not eligible for MVP"}

    lane = "vote" if requested_amount_usd > settings.governance_threshold_usd else "auto"
    return {
        "eligible": True,
        "governance_lane": lane,
        "max_loan_usd": requested_amount_usd,
        "interest_rate_apr": _calculate_interest_rate(risk_tier, member_months),
        "reason": "approved by policy checks",
    }
