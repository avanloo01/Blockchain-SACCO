from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MemberProfile:
    member_id: str
    joined_on: date
    email_verified: bool
    phone_verified: bool
    contribution_total_usd: float
    repayment_on_time_ratio: float


@dataclass(frozen=True)
class PoolState:
    total_balance_usd: float
    total_lent_out_usd: float


@dataclass(frozen=True)
class LoanRequest:
    member_id: str
    amount_usd: float
    tenure_months: int
