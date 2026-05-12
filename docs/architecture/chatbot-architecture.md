# Telegram Chatbot Architecture (AWS Lambda + Python)

## Responsibilities

- Member authentication bootstrap (phone/email link checks).
- Monthly contribution reminder and payment intent creation.
- Loan request capture and status updates.
- Repayment reminders and delinquency messaging.

## AWS Components

1. API Gateway + Lambda webhook:
- Receives Telegram updates.
- Verifies webhook secret header and per-chat-id rate limit.
- Rejects stale updates (message date older than 60 seconds).
- Routes to command handlers.

2. Lambda command handlers (`TelegramWebhookFunction`):
- `/start`, `/help`, `/status`, `/wallet`, `/contribute`, `/verify`, `/loan`, `/loan_status`, `/repay`, `/proposals`, `/vote`.

3. EventBridge schedules:
- Monthly billing cycle trigger — 1st of month at 07:00 UTC (`MonthlyContributionFunction`).
- Daily repayment reminder checks — daily at 07:00 UTC (`RepaymentReminderFunction`).
- Daily payment reconciliation — daily at 06:00 UTC (`PaymentReconciliationFunction`).

4. PostgreSQL (Supabase) tables via Prisma ORM:
- `members`
- `billing_intents`
- `loan_requests`
- `repayment_schedules`
- `message_delivery`
- `governance_votes`

5. Secrets Manager + KMS:
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

- All contributions go through Crossmint card checkout (USDC delivered to treasury wallet) or direct Solana USDC transfer.
- A transparent service fee (default 1% of contribution amount) is deducted; net-to-pool and fee amounts are recorded separately on each `billing_intent`.
- Loan disbursements are sent directly from the treasury wallet to the member's saved Solana address via SPL token transfer.
- Fee disclosure is shown in the Telegram message before the member proceeds to checkout.
