import logging

from src.config import settings
from src.policies.loan_policy import evaluate_loan_request
from src.repositories.billing_repo import (
    create_billing_intent,
    get_billing_intent_by_idempotency_key,
    mark_billing_settled,
)
from src.repositories.governance_repo import cast_vote, get_vote_tally, list_open_vote_loans
from src.repositories.loan_repo import (
    approve_loan,
    create_loan_request,
    generate_repayment_schedule,
    get_pool_state,
)
from src.repositories.member_repo import add_contribution, get_member_by_chat_id, get_member_months, update_wallet_address
from src.services.payments import get_payment_provider
from src.services.payments.base import PaymentStatus
from src.services.solana_disburse import disburse_usdc

logger = logging.getLogger(__name__)

_SIGNUP_PROMPT = (
    "You need to sign up first. "
    f"Register at {settings.website_url}/signup using the same phone number as your Telegram account, "
    "then come back here and tap Share phone number to link your Telegram account."
)


def _verify_usage() -> str:
    if settings.payment_provider == "crossmint":
        return "Usage: /verify <intent_id>"
    return "Usage: /verify <intent_id> <tx_signature>"


def _verify_follow_up(intent_id: str) -> str:
    if settings.payment_provider == "crossmint":
        return f"\nAfter completing checkout, verify with:\n/verify {intent_id}"
    return f"\nAfter sending, verify with:\n/verify {intent_id} <tx_signature>"


def dispatch_command(chat_id: str, text: str) -> str:
    parts = text.split()
    command = parts[0].lower() if parts else ""

    if text.startswith("/start"):
        member = get_member_by_chat_id(telegram_chat_id=chat_id)
        if member is not None:
            return (
                "Welcome back to Blockchain SACCO!\n\n"
                "Your Telegram account is linked.\n\n"
                "Use /help to see available commands."
            )
        return (
            f"Welcome to Blockchain SACCO!\n\n"
            f"First, sign up at {settings.website_url}/signup using the same phone number "
            f"you use on Telegram.\n"
            f"Then tap Share phone number here so I can link your Telegram account.\n\n"
            f"Once registered, use /help to see available commands."
        )

    if command == "/help":
        return (
            "Use /contribute 25 to start a USDC contribution.\n"
            f"Use {_verify_usage().replace('Usage: ', '')} to confirm a payment.\n"
            "Use /loan_request 120 3 to request a 3-month loan.\n"
            "Use /wallet <address> to save your Solana wallet for loan payouts.\n"
            "Use /proposals to list active governance proposals.\n"
            "Use /vote <loan_id> yes|no to cast your governance vote.\n"
            "Use /status to view your membership summary."
        )

    # All commands below require an existing member account
    member = get_member_by_chat_id(telegram_chat_id=chat_id)
    if member is None:
        return _SIGNUP_PROMPT

    if command == "/status":
        months = get_member_months(member)
        wallet = getattr(member, "walletAddress", None) or "not set"
        return (
            f"Member since: {member.joinedOn.strftime('%Y-%m-%d')}\n"
            f"Months active: {months}\n"
            f"Total contributed: {member.contributionTotalUsd:.2f} USD\n"
            f"Repayment on-time ratio: {member.repaymentOnTimeRatio:.0%}\n"
            f"Wallet: {wallet}"
        )

    if command == "/wallet":
        if len(parts) < 2:
            wallet = getattr(member, "walletAddress", None)
            if wallet:
                return f"Your current wallet: {wallet}\nTo update: /wallet <new_solana_address>"
            return (
                "No wallet address set.\n"
                "Send your Solana wallet address so loans can be paid out to you:\n"
                "/wallet <your_solana_address>"
            )
        raw_address = parts[1]
        try:
            from solders.pubkey import Pubkey  # noqa: PLC0415
            Pubkey.from_string(raw_address)
        except Exception:
            return (
                "That doesn't look like a valid Solana address.\n"
                "Please send a base58 Solana wallet address.\n"
                "Example: /wallet 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
            )
        update_wallet_address(member.id, raw_address)
        return f"Wallet saved: {raw_address}\nLoan disbursements will be sent here."

    if command == "/contribute":
        amount_usd = _parse_positive_float(parts[1] if len(parts) > 1 else None, default=20.0)
        if amount_usd <= 0:
            return "Invalid amount. Example: /contribute 25"

        receipt_email = getattr(member, "email", None)
        if not isinstance(receipt_email, str):
            receipt_email = None

        try:
            provider = get_payment_provider()
            intent = provider.create_payment_intent(
                amount_usd=amount_usd,
                member_id=member.id,
                receipt_email=receipt_email,
            )
        except Exception as exc:
            logger.exception("Failed to create payment intent for chat_id=%s", chat_id)
            return f"Could not start the payment right now: {exc}"

        create_billing_intent(
            member_id=member.id,
            amount_usd=intent.amount_usd,
            service_fee_usd=intent.service_fee_usd,
            net_pool_amount_usd=intent.net_pool_amount_usd,
            idempotency_key=intent.intent_id,
            recipient_address=intent.recipient_address,
            memo=intent.memo,
            payment_url=intent.payment_url,
            network=intent.network,
        )

        lines = [
            "Contribution intent created.",
            f"Amount: {intent.amount_usd:.2f} USDC",
            f"Fee: {intent.service_fee_usd:.2f} USDC",
            f"Net to pool: {intent.net_pool_amount_usd:.2f} USDC",
            f"Network: {intent.network}",
            f"Send to: {intent.recipient_address}",
        ]
        if intent.memo:
            lines.append(f"Memo: {intent.memo}")
        if intent.payment_url:
            lines.append(f"Payment link: {intent.payment_url}")
        lines.append(_verify_follow_up(intent.intent_id))
        return "\n".join(lines)

    if command == "/verify":
        requires_reference = settings.payment_provider != "crossmint"
        if len(parts) < 2 or (requires_reference and len(parts) < 3):
            return _verify_usage()
        intent_id = parts[1]
        tx_signature = parts[2] if len(parts) > 2 else intent_id

        billing = get_billing_intent_by_idempotency_key(intent_id)
        if billing is None or billing.memberId != member.id:
            return "Payment intent not found. Check the intent ID from your /contribute message."
        if billing.status == "confirmed":
            return "This payment has already been confirmed."

        # For the Crossmint provider the intent_id IS the Crossmint orderId
        # (the order is created server-side when /contribute runs).
        if settings.payment_provider == "crossmint":
            tx_signature = intent_id

        provider = get_payment_provider()
        result = provider.verify_payment_settlement(
            intent_id=tx_signature, tx_signature=tx_signature
        )

        if result.status == PaymentStatus.CONFIRMED:
            confirmation_reference = result.tx_signature or tx_signature or intent_id
            mark_billing_settled(
                intent_id=billing.id,
                tx_signature=confirmation_reference,
            )
            add_contribution(
                telegram_chat_id=chat_id,
                amount_usd=billing.netPoolAmountUsd,
            )
            preview = (
                f"{confirmation_reference[:16]}..."
                if len(confirmation_reference) > 16
                else confirmation_reference
            )
            return (
                f"Payment confirmed! Reference: {preview}\n"
                f"{billing.netPoolAmountUsd:.2f} USDC credited to your contribution balance."
            )
        elif result.status == PaymentStatus.PENDING:
            return "Payment found but not yet finalized. Please try again in a minute."
        else:
            return f"Verification failed: {result.error or 'transaction error on-chain'}"

    if command == "/loan_request":
        amount_usd = _parse_positive_float(parts[1] if len(parts) > 1 else None, default=120.0)
        tenure_months = _parse_positive_int(parts[2] if len(parts) > 2 else None, default=3)
        if amount_usd <= 0 or tenure_months <= 0:
            return "Invalid loan request. Example: /loan_request 120 3"

        member_months = get_member_months(member)
        pool = get_pool_state()

        decision = evaluate_loan_request(
            member_months=member_months,
            requested_amount_usd=amount_usd,
            pool_total_usd=max(pool["total_balance_usd"], 1.0),
            pool_total_lent_usd=pool["total_lent_out_usd"],
            risk_tier="medium",
        )
        if not decision["eligible"]:
            return f"Loan request declined: {decision['reason']}"

        if decision["governance_lane"] == "auto":
            wallet = getattr(member, "walletAddress", None)
            if not wallet:
                return (
                    f"You are eligible for a {amount_usd:.2f} USD loan over {tenure_months} months!\n"
                    f"Before I can send the funds, please share your Solana wallet address:\n"
                    f"/wallet <your_solana_address>\n\n"
                    f"Then re-run: /loan_request {amount_usd:.0f} {tenure_months}"
                )
            loan = create_loan_request(
                member_id=member.id,
                amount_usd=amount_usd,
                tenure_months=tenure_months,
                governance_lane=decision["governance_lane"],
                reason=decision["reason"],
            )
            generate_repayment_schedule(loan)
            token_locator = settings.crossmint_token_locator
            mint_address = token_locator.split(":", 1)[1] if ":" in token_locator else token_locator
            disburse_result = disburse_usdc(
                recipient_wallet=wallet,
                amount_usd=amount_usd,
                mint_address=mint_address,
            )
            if disburse_result.error:
                logger.error(
                    "Loan disbursement failed loan_id=%s member=%s error=%s",
                    loan.id,
                    member.id,
                    disburse_result.error,
                )
                return (
                    f"Loan approved for {amount_usd:.2f} USD over {tenure_months} months, "
                    f"but the on-chain transfer failed: {disburse_result.error}\n"
                    f"Please contact support with loan ID: {loan.id[:8]}"
                )
            approve_loan(loan.id)
            sig = disburse_result.tx_signature
            sig_preview = f"{sig[:16]}..." if len(sig) > 16 else sig
            return (
                f"Loan approved and {amount_usd:.2f} USDC sent to your wallet!\n"
                f"Transaction: {sig_preview}\n"
                f"Repayments start in 30 days ({tenure_months} x {amount_usd / tenure_months:.2f} USD/month)."
            )

        # Governance lane — submitted for community vote, no immediate disbursement.
        loan = create_loan_request(
            member_id=member.id,
            amount_usd=amount_usd,
            tenure_months=tenure_months,
            governance_lane=decision["governance_lane"],
            reason=decision["reason"],
        )
        return (
            f"Loan request submitted for {amount_usd:.2f} USD over {tenure_months} months. "
            f"Lane: {decision['governance_lane']}. "
            f"Max approval: {decision['max_loan_usd']:.2f} USD"
        )

    if command == "/proposals":
        proposals = list_open_vote_loans(limit=8)
        if not proposals:
            return "No active governance proposals right now."

        lines = ["Active governance proposals:"]
        for p in proposals:
            lines.append(
                f"- {p['loan_id'][:8]} | {p['amount_usd']:.2f} USD | {int(p['tenure_months'])}mo | {p['created_on']}"
            )
        lines.append("\nVote with: /vote <loan_id> yes|no")
        return "\n".join(lines)

    if command == "/vote":
        if len(parts) < 3:
            return "Usage: /vote <loan_id> yes|no"
        loan_id = parts[1]
        choice = parts[2].lower()
        if choice not in {"yes", "no"}:
            return "Invalid vote. Use yes or no. Example: /vote <loan_id> yes"

        cast_vote(loan_id=loan_id, member_id=member.id, vote=choice)
        tally = get_vote_tally(loan_id=loan_id)
        return (
            f"Vote recorded: {choice.upper()} for loan {loan_id[:8]}...\n"
            f"Current tally -> Yes: {tally['yes']} | No: {tally['no']} | Total: {tally['total']}"
        )

    return "Unknown command. Supported: /start, /help, /status, /wallet, /contribute, /verify, /loan_request, /proposals, /vote."


def _parse_positive_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return -1.0


def _parse_positive_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return -1
