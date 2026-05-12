# Chatbot Lambda Service

Python AWS Lambda service for Telegram SACCO operations.

## Architecture Decisions Locked

- Contribution checkout: Crossmint card checkout delivering USDC to the SACCO treasury wallet.
- Member wallets: members supply their own non-custodial Solana wallet address (via website signup or `/wallet` command). No embedded or custodial wallets.
- Governance threshold: loans above 100 USD go to on-chain vote lane; votes are anchored as signed Solana Memo transactions.
- Pool liquidity safety: total lent amount cannot exceed 60% of pool.
- Profit model: transparent service fee (default 1%) on each contribution.

## Folder Structure

- `src/app.py`: Telegram webhook Lambda entrypoint.
- `src/scheduled.py`: EventBridge scheduled handlers.
- `src/handlers`: Telegram update and command routing.
- `src/policies`: Risk and policy checks.
- `src/services`: Payment intent and campaign logic.
- `src/repositories`: Data access placeholders.
- `tests`: Unit tests for policy rules.
- `template.yaml`: AWS SAM deployment template.

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:
	- `pip install -r requirements.txt`
3. Generate the Prisma client:
	- `python3 -m prisma generate --schema prisma/schema.prisma`
4. Copy `.env.example` to `.env` and populate the required variables:
	- `TELEGRAM_BOT_TOKEN` — Telegram bot token from @BotFather.
	- `CROSSMINT_SERVER_API_KEY` — Crossmint server-side API key.
	- `CROSSMINT_WALLET_ADDRESS` — Crossmint-managed SACCO treasury wallet address.
	- `CROSSMINT_TREASURY_EMAIL` — email of the Crossmint account that owns the treasury wallet.
	- `SOLANA_TREASURY_ADDRESS` — raw Solana treasury wallet address (used for direct disbursements).
	- `SOLANA_TREASURY_PRIVATE_KEY` — base58 private key of the treasury wallet for signing disbursements.
	- `SOLANA_USDC_MINT` — USDC mint address for direct disbursements (dev default: SPL Token Faucet USDC-Dev).
	- `DATABASE_URL` / `DIRECT_URL` — Supabase PostgreSQL connection strings.
5. Run tests:
	- `pytest`

## Deployment Note

- `template.yaml` currently includes a fixed `TELEGRAM_BOT_TOKEN` value for quick setup.
- For production, move the token to Secrets Manager or deployment-time parameters.

## Webhook Registration

- Register webhook:
	- `python3 scripts/register_webhook.py --webhook-url https://your-api-id.execute-api.region.amazonaws.com/Prod/telegram/webhook --show-info`
- Register webhook with a one-off token (without storing it locally):
	- `python3 scripts/register_webhook.py --webhook-url https://your-api-id.execute-api.region.amazonaws.com/Prod/telegram/webhook --bot-token "$TELEGRAM_BOT_TOKEN" --show-info`
- Optional secret header:
	- Set `TELEGRAM_WEBHOOK_SECRET` in environment/template and Telegram will include `X-Telegram-Bot-Api-Secret-Token`.

## Lambda Functions

Four Lambda functions are deployed via `template.yaml`:

| Function | Handler | Trigger |
|---|---|---|
| `TelegramWebhookFunction` | `src.app.lambda_handler` | API Gateway POST `/telegram/webhook` |
| `MonthlyContributionFunction` | `src.scheduled.monthly_contribution_handler` | EventBridge cron — 1st of month at 07:00 UTC |
| `RepaymentReminderFunction` | `src.scheduled.repayment_reminder_handler` | EventBridge cron — daily at 07:00 UTC |
| `PaymentReconciliationFunction` | `src.scheduled.payment_reconciliation_handler` | EventBridge cron — daily at 06:00 UTC |

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and signup prompt |
| `/help` | List all available commands |
| `/status` | Membership summary (months active, contributions, wallet) |
| `/wallet <address>` | Save or update your Solana wallet address for loan payouts |
| `/contribute [amount]` | Start a USDC contribution via Crossmint checkout (default 20 USD) |
| `/verify <intent_id>` | Confirm a completed Crossmint payment |
| `/loan <amount> <months>` | Request a loan (evaluated against policy + pool state) |
| `/loan_status` | View status of your most recent loan request |
| `/repay` | Get a payment link for the next due installment |
| `/proposals` | List active governance proposals |
| `/vote <loan_id> yes\|no` | Cast an on-chain governance vote (Solana Memo transaction) |
