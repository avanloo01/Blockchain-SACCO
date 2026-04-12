# Website Architecture (Next.js on Vercel)

## Responsibilities

- Public landing and signup funnel.
- Member onboarding with light KYC (email + phone).
- Wallet connection options (non-custodial and embedded).
- Transparency dashboard with pool and loan metrics.

## Rendering Strategy

- Static pages for marketing and documentation.
- ISR or scheduled regeneration for public transparency aggregates.
- Authenticated server-rendered routes for member-specific data.

## Core Routes (MVP)

- `/` landing and value proposition.
- `/signup` account creation and verification start.
- `/onboarding` wallet setup and membership steps.
- `/dashboard/public` aggregate pool stats and recent activity.
- `/dashboard/member` personal contributions, loans, repayment status.
- `/governance` proposal list and voting interface.

## Data Sources

1. Indexer API:
- Pool balance, contribution totals, outstanding principal, repayment performance.

2. Membership API:
- User profile, verification state, linked wallets.

3. Governance API:
- Active proposals, vote windows, outcomes.

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

- Cache indexer responses for public dashboards to reduce cost.
- Display last-updated timestamps for transparency pages.
- Gracefully degrade if chain indexer is delayed.

## Design
 
- Black and blue, futuristic, but minimalist.
- Responsive and functional on mobile devices.
- Clear calls to action for signup and wallet connection.