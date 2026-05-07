# Telegram Chatbot Architecture (AWS Lambda + Python)

## Responsibilities

- Member authentication bootstrap (phone/email link checks).
- Monthly contribution reminder and payment intent creation.
- Loan request capture and status updates.
- Repayment reminders and delinquency messaging.

## AWS Components

1. API Gateway + Lambda webhook:
- Receives Telegram updates.
- Verifies source and routes command handlers.

2. Lambda command handlers:
- `/start`, `/profile`, `/contribute`, `/loan`, `/loan_status`, `/repay`.

3. EventBridge schedules:
- Monthly billing cycle trigger.
- Daily repayment reminder checks.

4. SQS queue + worker Lambda:
- Async delivery of high-volume reminders.
- Retry and dead letter queue handling.

5. PostgreSQL (Supabase) tables:
- `members`
- `billing_intents`
- `loan_requests`
- `repayment_schedules`
- `message_delivery`

6. Secrets Manager + KMS:
- Telegram bot token.
- Service API credentials.

## Command Flow Example: Monthly Contribution

1. EventBridge triggers monthly cycle.
2. Billing Lambda creates payment intent for each active member.
3. Payment intent includes amount, due date, and reference ID.
4. Bot sends private Telegram message with payment link.
5. Payment watcher confirms on-chain settlement and updates intent state.
6. Bot confirms contribution receipt to the member.

## Command Flow Example: Loan Request

1. Member sends `/loan` with amount and tenure.
2. Bot checks minimum membership age (>= 3 months).
3. Risk service computes score and recommended limit.
4. Policy engine validates pool utilization cap (total lent <= 60% of pool).
5. If low risk and loan amount is <= 100 USD, auto-approve and disburse.
6. If loan amount is > 100 USD, submit to on-chain community vote and notify member of pending status.

## Telegram UX Guidelines

- Keep interaction mostly button-driven with clear next actions.
- Every money action should include explicit amount, fee (if any), due date.
- Provide transaction and loan IDs for support and audit.
- Default to private chat only, as requested.

## Failure and Recovery

- Duplicate update handling using Telegram update ID idempotency key.
- Payment confirmation retries with exponential backoff.
- Human review queue for ambiguous transfer matches.
- Circuit breaker to pause disbursements if risk systems are unavailable.

## Payment Profit Policy (MVP)

- Use direct stablecoin transfer payment intents.
- Add a transparent service fee per contribution or repayment action.
- Record fee and net pool amount separately in ledger events.
- Show fee disclosure in Telegram before transaction confirmation.
