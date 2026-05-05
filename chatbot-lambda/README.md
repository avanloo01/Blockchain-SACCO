# Chatbot Lambda Service

Python AWS Lambda service for Telegram SACCO operations.

## Architecture Decisions Locked

- Contribution checkout: Crossmint card checkout delivering USDC to the SACCO treasury wallet.
- Embedded wallet option: Circle Programmable Wallets.
- Governance threshold: loans above 100 USD go to on-chain vote lane.
- Pool liquidity safety: total lent amount cannot exceed 60% of pool.
- Profit model: transparent service fee on transactions.

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
4. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`, `CROSSMINT_SERVER_API_KEY`, and the treasury wallet settings.
	- Set `CROSSMINT_RECIPIENT_EMAIL` to the SACCO treasury email address (e.g. `arthurvl@duck.com`) for Crossmint checkout.
	- Keep `SOLANA_TREASURY_ADDRESS` for direct Solana transfer flows.
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

## Next Implementation Steps

- Wire PostgreSQL (or Supabase Postgres) repositories.
- Integrate Telegram sendMessage API in command responses.
- Add webhook-driven payment confirmation for hosted checkout.
- Add on-chain governance proposal and vote tracking.
