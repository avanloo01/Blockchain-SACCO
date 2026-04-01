from src.config import settings


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
        "reason": "approved by policy checks",
    }
