# Blockchain SACCO Monorepo

This monorepo contains two primary products:

1. `chatbot-lambda`: Telegram chatbot backend on AWS Lambda (Python).
2. `website-nextjs`: Static-first transparency and signup site on Vercel (Next.js).

Architecture and product design docs are in `docs/architecture`.

## Project Goals

- Enable monthly SACCO contributions via Crossmint card checkout (USDC).
- Allow eligible members to request and receive loans from the shared pool.
- Provide transparent, auditable pool metrics with privacy protections.
- MVP is feature-complete and deployed; currently in devnet pilot phase.

## High-Level Stack

- Chatbot: Python, AWS Lambda, API Gateway, EventBridge, Prisma ORM + PostgreSQL (Supabase).
- Website: Next.js on Vercel (App Router), static pages + serverless API routes, NextAuth session handling.
- Blockchain: Solana (devnet), USDC settlement, on-chain governance via Memo transactions.
- Payments: Crossmint card checkout (primary, USDC delivered to treasury wallet) + direct Solana USDC transfers for loan disbursements.
- Governance: Auto-approval lane (≤ $100 USD, low risk) + on-chain community vote lane (> $100 USD); votes anchored as signed Solana Memo transactions.
- Identity: Light KYC (email + phone verified), personal details off-chain and access-controlled; members supply their own non-custodial Solana wallet address.

## Architecture Docs

- `docs/architecture/system-architecture.md`
- `docs/architecture/chatbot-architecture.md`
- `docs/architecture/website-architecture.md`
- `docs/architecture/loan-policy-and-risk.md`
- `docs/architecture/implementation-roadmap.md`
