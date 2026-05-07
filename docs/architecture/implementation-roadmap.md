# Implementation Roadmap (4 to 6 Weeks MVP)

## Delivery Strategy

- Sequence priority: Telegram webhook in production first, then database wiring in a later session when Supabase credentials are available.
- Payments strategy: testnet-first implementation to validate flows without risking funds.
- Integration strategy: payment logic is provider-agnostic so Solana USDC links can later be swapped for Paystack, Stripe, or other payment links with minimal code changes.
- Wallet strategy: users provide their own Solana wallet address during website registration. No embedded or custodial wallets.

## Phase 1: Bot Runtime and Webhook Go-Live (Week 1) [DONE]

- [x] Finalize policy constants already decided:
	- Membership minimum: 3 months.
	- Pool utilization cap: 60%.
	- Governance threshold: on-chain vote required above 100 USD.
- [x] Complete Lambda deployment and webhook registration.
- [x] Verify command loop in Telegram (`/start`, `/help`, `/contribute`, `/loan`, `/verify`, `/status`, `/proposals`, `/vote`).
- [x] Add webhook secret validation and deployment runbook.
- [x] GitHub Actions CI/CD pipeline with all parameter overrides.

## Phase 2: Persistence and Core Domain Wiring (Week 2) [DONE]

- [x] Prisma schema with all tables: members, billing_intents, loan_requests, repayment_schedules, message_delivery, governance_votes.
- [x] All repositories implemented with real Prisma queries (member, billing, loan, governance, message).
- [x] Idempotency keys on billing intents.
- [x] Member state lookup for real loan eligibility checks.
- [x] Website signup creates member in Supabase with email, phone, and wallet address.
- [x] NextAuth verifies email exists in members table before granting session.
- [x] Member API filters by authenticated user's email.

## Phase 3: Testnet Payments Module (Weeks 3 to 4) [DONE]

- [x] Payment provider interface (adapter pattern) with normalized PaymentIntent and SettlementResult schemas.
- [x] Solana testnet USDC adapter: create_payment_intent and verify_payment_settlement via JSON-RPC.
- [x] Crossmint adapter: hosted checkout order creation and transaction verification via REST API.
- [x] Payment reconciliation scheduled job (daily at 06:00 UTC).
- [x] All payment actions record service fee and net-to-pool amounts.
- [x] Integration tests for both providers with edge cases (21 test cases).

## Phase 4: Governance, Repayments, and Transparency (Week 5) [DONE]

- [x] Governance voting via `/vote` command with real tally tracking.
- [x] Governance proposals API returns real vote counts from governance_votes table.
- [x] Repayment schedule generation and daily reminder dispatch.
- [x] Monthly contribution reminder campaign (1st of each month at 07:00 UTC).
- [x] Public dashboard with aggregate pool metrics (ISR, 60s revalidation).
- [x] Member dashboard with personal profile, contribution total, and loan history.
- [x] Governance page listing active/passed/rejected proposals with vote tallies.
- [x] Interest rate calculation: base rate + risk premium - loyalty discount (formula-based, APR returned in policy result).

## Phase 5: Hardening and Pilot Launch (Week 6) [DONE]

- [x] Email verification flow: send verification email on signup, set email_verified flag on confirmation.
- [x] Rate limiting on webhook endpoint and API routes to prevent abuse.
- [x] Webhook replay protection: validate timestamp freshness on incoming Telegram updates.
- [x] Secrets audit: confirm all sensitive values are in GitHub Secrets and SAM parameter store, not in code.
- [x] Contribution history and repayment schedule views on the member dashboard.

## Post-MVP (After Pilot)

These items are out of scope for the MVP and should be tackled after the testnet pilot validates core flows:

- Solana mainnet payment adapter (config-only switch once testnet acceptance criteria are met).
- Refund / reversal logic on PaymentProvider base class.
- Advanced risk scoring (contribution consistency, repayment speed, debt exposure) replacing the simple `risk_tier` parameter.
- SQS dead-letter queue and retry worker for failed scheduled jobs.
- On-chain governance (post vote results to Solana, indexer to sync back).

## Payment Module Swap Plan

- Keep payment logic behind a provider interface in `chatbot-lambda/src/services/payments`.
- Select provider via configuration (`PAYMENT_PROVIDER=solana_testnet|solana_mainnet|paystack|stripe`).
- Enforce shared normalized response schema so command handlers do not depend on provider specifics.
- Require provider conformance tests before enabling a new adapter.

## MVP Exit Criteria

- Webhook is deployed and stable in production Lambda.
- Supabase-backed member and loan state is fully integrated.
- Payments are validated on testnet first, with no mainnet exposure during testing.
- Payment provider abstraction is implemented and can switch adapters with config-only changes.
- Monthly contribution reminders send with payment links and settlement tracking.
- Loan requests are evaluated with real member data and policy rules, including interest rate.
- Governance voting is active for loans above 100 USD with real tallies displayed.
- Public dashboard shows accurate aggregate transparency metrics.
- Users register with their own wallet address on the website (no custodial wallets).
