def build_monthly_contribution_messages() -> list[dict[str, str]]:
    # Placeholder for DB-backed member scan and message fan-out.
    return [
        {
            "member_id": "member_001",
            "message": "Your April contribution is due. Tap to pay with USDC.",
        }
    ]


def build_repayment_messages() -> list[dict[str, str]]:
    return [
        {
            "member_id": "member_001",
            "message": "Reminder: your loan repayment is due in 2 days.",
        }
    ]
