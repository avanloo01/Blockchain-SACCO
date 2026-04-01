# Chatbot Lambda Service

Python AWS Lambda service for Telegram SACCO operations.

## Architecture Decisions Locked

- Chain and settlement: Solana + direct USDC transfer intents.
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
3. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`.
3. Run tests:
	- `pytest`

## Deployment Note

- `template.yaml` expects `TelegramBotToken` as a SAM parameter.
- Example deploy flag: `--parameter-overrides TelegramBotToken=your_token_here`

## Next Implementation Steps

- Wire PostgreSQL (or Supabase Postgres) repositories.
- Integrate Telegram sendMessage API in command responses.
- Add Solana transfer verification service.
- Add on-chain governance proposal and vote tracking.
