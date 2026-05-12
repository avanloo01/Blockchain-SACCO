# Website Architecture (Next.js on Vercel)

## Responsibilities

- Public landing and signup funnel.
- Member onboarding with light KYC (email + phone verification via Resend).
- Wallet address capture during signup (member-supplied non-custodial Solana address).
- Transparency dashboard with pool and loan metrics.
- Crossmint hosted checkout for card-to-USDC contributions.

## Rendering Strategy

- Static pages for marketing and documentation.
- ISR or scheduled regeneration for public transparency aggregates.
- Authenticated server-rendered routes for member-specific data.

## Core Routes (MVP)

- `/` landing and value proposition.
- `/signup` account creation, email verification, and wallet address capture.
- `/login` NextAuth-backed session login.
- `/onboarding` post-signup membership steps (links to Telegram bot).
- `/checkout/crossmint` Crossmint hosted checkout page for card contributions.
- `/dashboard/public` aggregate pool stats and recent activity (ISR, 60s revalidation).
- `/dashboard/member` personal contributions, loans, repayment schedule.
- `/governance` active and resolved governance proposals with vote tallies.

## API Routes

- `GET /api/pool-stats` — public aggregate pool metrics (balance, utilization, member count).
- `GET /api/member` — authenticated member profile, contribution history, loans, repayment schedule.
- `GET /api/governance/proposals` — governance proposals with vote tallies.
- `POST /api/auth/signup` — create member record and send verification email (Resend).
- `GET /api/auth/verify-email` — confirm email verification token and set `email_verified`.
- `POST /api/auth/login`, `GET /api/auth/[...nextauth]` — NextAuth credential flow.
- `POST /api/checkout/link-order` — link a Crossmint order to a member after checkout.

## Data Sources

1. Supabase (direct PostgreSQL queries via REST API):
- Pool balance, contribution totals, outstanding principal, repayment performance — aggregated server-side in `/api/pool-stats`.
- Member profile, verification state, contribution history — returned by `/api/member`.
- Governance proposals and vote tallies — returned by `/api/governance/proposals`.

There is no separate indexer service. All reads go directly to the Supabase PostgreSQL database.

## Privacy Model

- Public:
  - Pool-level totals.
  - Aggregate risk and repayment indicators.
  - Pseudonymous transaction references.

- Private (authenticated):
  - Personal contact details.
  - Contribution and loan history at member level.
  - Verification status and profile controls.

## Vercel Integration Notes

- Use environment variables for API endpoints and public keys.
- Avoid storing secrets in client bundles.
- Use server actions/API routes for protected calls.

## Reliability Considerations

- Cache Supabase query results for public dashboards to reduce database load (ISR revalidation every 60s).
- Display last-updated timestamps for transparency pages.
- Gracefully degrade public dashboard if database is unavailable.

## Design
 
- Black and blue, futuristic, but minimalist.
- Responsive and functional on mobile devices.
- Clear calls to action for signup and wallet connection.