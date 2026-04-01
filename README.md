# Blockchain SACCO Monorepo

This monorepo contains two primary products:

1. `chatbot-lambda`: Telegram chatbot backend on AWS Lambda (Python).
2. `website-nextjs`: Static-first transparency and signup site on Vercel (Next.js).

Architecture and product design docs are in `docs/architecture`.

## Project Goals

- Enable monthly SACCO contributions via stablecoin links.
- Allow eligible members to request and receive loans from the shared pool.
- Provide transparent, auditable pool metrics with privacy protections.
- Launch MVP in 4 to 6 weeks for first cohort of 20 to 50 users.

## High-Level Stack

- Chatbot: Python, AWS Lambda, API Gateway, EventBridge, DynamoDB, SQS.
- Website: Next.js on Vercel (App Router), static pages + serverless API routes.
- Blockchain: Solana smart contract (program), USDC settlement.
- Payments: Stablecoin transfers (primary), x402 style pay links abstraction.
- Governance: Hybrid automated scoring + community vote for larger loans.
- Identity: Light KYC (email + phone), personal details private.

## Architecture Docs

- `docs/architecture/system-architecture.md`
- `docs/architecture/chatbot-architecture.md`
- `docs/architecture/website-architecture.md`
- `docs/architecture/loan-policy-and-risk.md`
- `docs/architecture/implementation-roadmap.md`
