# Implementation Roadmap (4 to 6 Weeks MVP)

## Delivery Strategy

- Sequence priority: Telegram webhook in production first, then database wiring in a later session when Supabase credentials are available.
- Payments strategy: testnet-first implementation to validate flows without risking funds.
- Integration strategy: payment logic is provider-agnostic so Solana USDC links can later be swapped for Paystack, Stripe, or other payment links with minimal code changes.

## Phase 1: Bot Runtime and Webhook Go-Live (Week 1)

- Finalize policy constants already decided:
	- Membership minimum: 3 months.
	- Pool utilization cap: 60%.
	- Governance threshold: on-chain vote required above 100 USD.
- Complete Lambda deployment and webhook registration.
- Verify command loop in Telegram (`/start`, `/help`, `/contribute`, `/loan_request`).
- Add webhook secret validation and deployment runbook.
- Keep data repositories in placeholder mode until Supabase details are provided.

## Phase 2: Persistence and Core Domain Wiring (Week 2)

- Integrate Supabase/PostgreSQL after credentials are shared.
- Replace placeholder repositories with real tables and queries:
	- members
	- billing_intents
	- loan_requests
	- repayment_schedules
	- message_delivery
- Add idempotency and audit logging for webhook updates and command outcomes.
- Implement member state lookup for real loan eligibility checks.

## Phase 3: Testnet Payments Module (Weeks 3 to 4)

- Implement a payment provider interface (adapter pattern), with the first adapter as Solana testnet USDC direct transfer intent.
- Define stable internal contract for providers, for example:
	- `create_payment_intent`
	- `verify_payment_settlement`
	- `refund_or_reverse` (optional, provider-dependent)
- Add testnet settlement verifier and reconciliation jobs.
- Ensure all payment actions record both service fee and net-to-pool amounts.
- Build integration tests that run only against testnet fixtures/mocks.

## Phase 4: Governance, Repayments, and Transparency (Week 5)

- Implement on-chain governance workflow for loans above 100 USD.
- Implement repayment schedule generation and reminder dispatch.
- Connect website dashboard to indexed aggregate metrics.
- Add member-facing status updates for contribution, loan state, and repayment progress.

## Phase 5: Hardening and Pilot Launch (Week 6)

- Security review:
	- secrets handling
	- key management
	- webhook auth and replay protection
- End-to-end rehearsal on testnet with 10 to 20 pilot users.
- Incident playbooks for payment mismatch, delayed settlement, and failed reminder delivery.
- Enable production payment adapter only after testnet acceptance criteria are met.

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
- Loan requests are evaluated with real member data and policy rules.
- On-chain governance is active for loans above 100 USD.
- Public dashboard shows accurate aggregate transparency metrics.
