# Loan Policy and Risk Model (MVP)

## Hard Eligibility Rules

1. Membership age must be at least 3 months.
2. Identity minimum must be completed (email + phone verified).
3. Member must have no active severe delinquency flag.
4. Pool utilization cap: total principal lent out must remain <= 60% of current pool balance.

## Scoring Inputs

- Membership duration (older members score higher).
- Total lifetime contribution amount.
- Contribution consistency (on-time monthly behavior).
- Repayment speed on prior loans.
- Current debt exposure ratio.

## Initial Scoring Output

The risk service returns:

- `eligibility`: yes/no
- `risk_tier`: low/medium/high
- `max_recommended_loan`
- `recommended_interest_rate`
- `governance_lane`: auto or vote

## Lending Limit Approach

Because you want loans potentially larger than personal contributions, the system should not hard-bind loan amount to contribution amount. Instead:

- Use a contribution-weighted credit multiplier.
- Cap by risk tier and pool liquidity.
- Apply stricter approval for members with shorter repayment history.

Example model (tunable):

- Low risk: up to 2.0x contribution base score value.
- Medium risk: up to 1.2x contribution base score value.
- High risk: manual or rejected in MVP.

## Interest Rate Framework

Use transparent formula-based rates:

- Base rate + risk premium - loyalty discount.
- Loyalty discount increases with membership age and on-time behavior.

Suggested guardrails:

- Minimum APR floor to keep pool yield positive after defaults.
- Maximum APR ceiling to protect borrowers.
- Late fee policy with capped penalty.

## Governance Lane Rules

- Auto lane:
  - Loan amount is <= 100 USD.
  - Risk tier low.
  - No policy violations.

- Vote lane:
  - Loan amount is > 100 USD.
  - Medium risk profiles.
  - Any exceptional override request.
  - Voting occurs on-chain.

## Anti-Crisis Controls

- Automatic freeze on new loans if utilization exceeds 60%.
- Temporary freeze if default ratio breaches threshold.
- Emergency multi-sig power to pause disbursement and notify members.

## Transparency Requirements

- Publish aggregate metrics for approvals, rejects, defaults, and yield.
- Keep individual borrower details private by default.
- Version all policy formula changes with effective dates.
