# Implementation Roadmap (4 to 6 Weeks MVP)

## Phase 1: Foundations (Week 1)

- Finalize product requirements and risk policy constants.
- Create monorepo CI and environment strategy.
- Build Telegram webhook skeleton on Lambda.
- Initialize Next.js app with public pages and auth placeholders.
- Define Solana program accounts and instruction interfaces.

## Phase 2: Core Money Flows (Weeks 2 to 3)

- Implement contribution billing intents and reminder scheduler.
- Build stablecoin payment link generation and settlement verifier.
- Implement loan request intake + risk scoring service.
- Implement initial Solana contract for pool and loan state.
- Add website public transparency dashboard backed by indexer snapshots.

## Phase 3: Governance and Repayment (Weeks 4 to 5)

- Add governance vote flow for non-auto loans.
- Implement repayment schedules and Telegram reminders.
- Add member dashboard with personal contribution and loan state.
- Add audit logs for scoring decisions and policy checks.

## Phase 4: Hardening and Pilot Launch (Week 6)

- Security review and secrets audit.
- Testnet and staging rehearsal with 10 to 20 pilot users.
- Incident playbooks for payment mismatch and missed reminders.
- Mainnet soft launch for first cohort of 20 to 50 users.

## MVP Exit Criteria

- Members can sign up, verify email/phone, and link wallet.
- Monthly contribution reminders send successfully with payment links.
- On-chain contribution settlement is recognized in system state.
- Eligible members can request loans and receive approval outcome.
- Pool utilization hard cap is enforced.
- Public dashboard shows accurate aggregate transparency metrics.
