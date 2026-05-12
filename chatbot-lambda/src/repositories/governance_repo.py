import logging

from src.db import get_db

logger = logging.getLogger(__name__)


def list_open_vote_loans(limit: int = 10) -> list[dict[str, str | float]]:
    """Return pending loan requests currently in the vote lane."""
    db = get_db()
    rows = db.loanrequest.find_many(
        where={"governanceLane": "vote", "status": "pending"},
        order={"createdAt": "desc"},
        take=limit,
    )
    return [
        {
            "loan_id": r.id,
            "amount_usd": r.amountUsd,
            "tenure_months": r.tenureMonths,
            "created_on": r.createdAt.strftime("%Y-%m-%d"),
        }
        for r in rows
    ]


def cast_vote(loan_id: str, member_id: str, vote: str, tx_signature: str | None = None) -> None:
    """Create or update a member vote for a given governance loan."""
    db = get_db()
    existing = db.governancevote.find_first(
        where={"loanRequestId": loan_id, "memberId": member_id}
    )
    if existing is None:
        db.governancevote.create(
            data={
                "loanRequestId": loan_id,
                "memberId": member_id,
                "vote": vote,
                "txSignature": tx_signature,
            }
        )
        logger.info("Governance vote created loan=%s member=%s vote=%s tx=%s", loan_id, member_id, vote, tx_signature)
        return

    db.governancevote.update(
        where={"id": existing.id},
        data={"vote": vote, "txSignature": tx_signature},
    )
    logger.info("Governance vote updated loan=%s member=%s vote=%s tx=%s", loan_id, member_id, vote, tx_signature)


def get_vote_tally(loan_id: str) -> dict[str, int]:
    db = get_db()
    votes = db.governancevote.find_many(where={"loanRequestId": loan_id})
    yes = sum(1 for v in votes if v.vote == "yes")
    no = sum(1 for v in votes if v.vote == "no")
    return {"yes": yes, "no": no, "total": len(votes)}
