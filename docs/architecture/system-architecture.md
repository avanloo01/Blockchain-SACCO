# System Architecture (Broad)

## Product Scope

The platform has two interfaces:

1. Telegram bot for operational SACCO actions:
- Monthly contribution reminders with payment links.
- Loan request workflow and repayment nudges.
- Private-only communication.

2. Web app for trust and onboarding:
- Signup and profile setup.
- Wallet connect (non-custodial + embedded option).
- Transparency dashboard (public aggregates + private member details).

## Core Principles

- On-chain source of truth for fund movement and loan state.
- Off-chain services for UX, notifications, scoring, and indexing.
- Privacy by design: personal member data off-chain and access-controlled.
- Liquidity safety: protocol limits to avoid pool insolvency.

## Logical Components

1. Identity and Membership Service (off-chain):
- Stores member profile, phone/email verification status.
- Tracks join date and membership state.
- Maintains link between user account and wallet(s).

2. Contribution and Payment Service (off-chain + on-chain):
- Creates monthly billing intents.
- Produces stablecoin payment links and references.
- Verifies on-chain transfer completion.

3. Solana Pool Program (on-chain):
- Vault account for pooled funds.
- Contribution records and loan state transitions.
- Enforces hard lending and liquidity constraints.

4. Risk and Scoring Service (off-chain, deterministic):
- Computes borrower eligibility and limit proposals.
- Inputs: membership duration, contribution history, repayment speed.
- Produces a transparent score and recommendation snapshot.

5. Governance Service (hybrid):
- Auto-approval lane for low-risk, low-size loans.
- Community vote lane for larger loans.
- Multi-sig admin emergency controls for abuse and incident response.

6. Notification and Scheduling Service:
- Monthly reminder campaigns.
- Repayment due reminders and escalation notifications.
- Telegram delivery tracking and retries.

7. Analytics (MVP: direct DB aggregation):
- Pool metrics (balance, utilization, repayment rate) aggregated server-side from PostgreSQL.
- No separate chain indexer in MVP; on-chain vote signatures stored in `governance_votes.tx_signature`.

## Suggested Deployment Topology

- AWS: chatbot Lambda (webhook + 3 EventBridge-scheduled functions), SAM deployment.
- Vercel: website UI + serverless API routes.
- Solana devnet: treasury wallet for USDC contributions and loan disbursements; Memo program for on-chain governance votes.
- Data:
  - PostgreSQL (Supabase) for all operational state.

## Data Ownership

- On-chain:
  - Pool balance and all transfers.
  - Loan lifecycle state.
  - Governance vote outcomes (if on-chain voting is enabled).

- Off-chain:
  - PII (email, phone), notification preferences.
  - Risk feature snapshots and scoring audit logs.
  - Telegram metadata and delivery receipts.

## Security Baseline

- Use custodial treasury only with strict multi-sig controls.
- Sign all webhook payloads and reject replay attacks.
- Separate public API, admin API, and worker roles with least privilege IAM.
- Encrypt PII at rest and in transit.
- Keep private keys in managed KMS/HSM workflows, never in code.

## Open Decisions (for next iteration)

- Advanced risk scoring (contribution consistency, repayment speed, debt exposure) to replace the current simple `risk_tier` input.
- SQS dead-letter queue and retry worker for failed scheduled jobs.
- Solana mainnet migration (config-only switch once testnet pilot acceptance criteria are met).
- Region-specific compliance flows for Sub-Saharan launch.

## Wallet Strategy

- Members supply their own non-custodial Solana wallet address during website signup or via `/wallet` in the bot.
- No embedded or custodial wallets in MVP.
- Loans are disbursed directly from the SACCO treasury wallet to the member's saved address via SPL token transfer.
- The SACCO treasury uses a separate Crossmint-managed wallet for receiving card checkout payments.
