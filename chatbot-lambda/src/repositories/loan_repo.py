import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from src.db import get_db

if TYPE_CHECKING:
    from prisma.models import LoanRequest as LoanRequestRow
    from prisma.models import RepaymentSchedule
else:
    LoanRequestRow = Any
    RepaymentSchedule = Any

logger = logging.getLogger(__name__)


def create_loan_request(
    member_id: str,
    amount_usd: float,
    tenure_months: int,
    governance_lane: str,
    reason: str,
) -> LoanRequestRow:
    db = get_db()
    loan = db.loanrequest.create(
        data={
            "memberId": member_id,
            "amountUsd": amount_usd,
            "tenureMonths": tenure_months,
            "governanceLane": governance_lane,
            "reason": reason,
        }
    )
    logger.info("Loan request created id=%s member=%s amount=%.2f", loan.id, member_id, amount_usd)
    return loan


def generate_repayment_schedule(loan: LoanRequestRow) -> list[RepaymentSchedule]:
    """Create equal monthly repayment rows for an approved loan."""
    db = get_db()
    monthly = round(loan.amountUsd / loan.tenureMonths, 2)
    schedules: list[RepaymentSchedule] = []
    for i in range(1, loan.tenureMonths + 1):
        due = datetime.now(timezone.utc) + timedelta(days=30 * i)
        row = db.repaymentschedule.create(
            data={
                "loanRequestId": loan.id,
                "memberId": loan.memberId,
                "amountUsd": monthly,
                "dueOn": due,
            }
        )
        schedules.append(row)
    logger.info("Generated %d repayment rows for loan %s", len(schedules), loan.id)
    return schedules


def get_due_repayments(days_ahead: int = 3) -> list[dict[str, str]]:
    """Return repayments due within the next N days for linked Telegram members."""
    db = get_db()
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)
    rows = db.repaymentschedule.find_many(
        where={
            "status": "pending",
            "dueOn": {"lte": cutoff},
        },
        include={"member": True},
    )
    return [
        {
            "member_id": r.member.telegramChatId,
            "due_on": r.dueOn.strftime("%Y-%m-%d"),
            "amount_usd": str(r.amountUsd),
            "repayment_id": r.id,
        }
        for r in rows
        if r.member and r.member.telegramChatId
    ]


def get_pending_repayment_for_member(member_id: str, repayment_id: str) -> RepaymentSchedule | None:
    """Fetch a member repayment row that is still pending."""
    db = get_db()
    return db.repaymentschedule.find_first(
        where={
            "id": repayment_id,
            "memberId": member_id,
            "status": "pending",
        }
    )


def mark_repayment_paid(repayment_id: str) -> RepaymentSchedule:
    """Mark a repayment schedule row as settled."""
    db = get_db()
    row = db.repaymentschedule.update(
        where={"id": repayment_id},
        data={
            "status": "paid",
            "paidOn": datetime.now(timezone.utc),
        },
    )
    logger.info("Repayment marked paid id=%s", repayment_id)
    return row


def approve_loan(loan_id: str) -> LoanRequestRow:
    """Mark a loan request as approved."""
    db = get_db()
    loan = db.loanrequest.update(
        where={"id": loan_id},
        data={"status": "approved"},
    )
    logger.info("Loan approved id=%s", loan_id)
    return loan


def get_pool_state() -> dict[str, float]:
    """Compute aggregate pool balance from member contributions and outstanding loans."""
    db = get_db()
    members = db.member.find_many()
    total_balance = sum(m.contributionTotalUsd for m in members)

    active_loans = db.loanrequest.find_many(
        where={"status": {"in": ["pending", "approved"]}}
    )
    total_lent = sum(l.amountUsd for l in active_loans)
    return {"total_balance_usd": total_balance, "total_lent_out_usd": total_lent}
