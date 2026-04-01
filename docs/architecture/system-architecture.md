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

7. Indexer and Analytics Service:
- Reads Solana events and stores query-friendly snapshots.
- Feeds website dashboard and bot account summaries.

## Suggested Deployment Topology

- AWS: chatbot APIs, schedulers, worker queues, risk jobs, webhook handlers.
- Vercel: website UI + light API routes.
- Solana: smart contract program + treasury vault accounts.
- Data:
  - PostgreSQL for operational state.
  - S3 for immutable report snapshots.
  - Optional Postgres (later) for analytics and governance history.

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

- Embedded wallet provider is Circle Programmable Wallets, while still supporting non-custodial Solana wallets.
- Governance threshold is fixed at 100 USD in MVP (vote required if loan is larger than 100 USD).
- Governance voting is on-chain in MVP.
- Region-specific compliance flows for Sub-Saharan launch.

## Wallet Strategy Decision

- Preferred embedded wallet provider: Circle Programmable Wallets.
- Rationale:
  - Solana compatibility aligns with the core chain choice.
  - Better fit for global, stablecoin-first operations than Coinbase Smart Wallets, which are more EVM ecosystem oriented.
  - Works with a dual UX where advanced users can connect non-custodial wallets directly.
