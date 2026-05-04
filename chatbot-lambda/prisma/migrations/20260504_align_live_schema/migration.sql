ALTER TABLE public.billing_intents
  ADD COLUMN IF NOT EXISTS memo text,
  ADD COLUMN IF NOT EXISTS payment_url text,
  ADD COLUMN IF NOT EXISTS recipient_address text,
  ADD COLUMN IF NOT EXISTS settled_at timestamp(3),
  ADD COLUMN IF NOT EXISTS tx_signature text;

ALTER TABLE public.billing_intents
  ALTER COLUMN network SET DEFAULT 'solana_devnet';

ALTER TABLE public.members
  ADD COLUMN IF NOT EXISTS email text,
  ADD COLUMN IF NOT EXISTS email_verification_token text,
  ADD COLUMN IF NOT EXISTS phone text,
  ADD COLUMN IF NOT EXISTS wallet_address text;

ALTER TABLE public.members
  ALTER COLUMN telegram_chat_id DROP NOT NULL,
  ALTER COLUMN id SET DEFAULT gen_random_uuid()::text,
  ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS public.governance_votes (
  id text NOT NULL,
  loan_request_id text NOT NULL,
  member_id text NOT NULL,
  vote text NOT NULL,
  created_at timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp(3) NOT NULL,
  CONSTRAINT governance_votes_pkey PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS governance_votes_loan_request_id_member_id_key
  ON public.governance_votes (loan_request_id, member_id);

CREATE UNIQUE INDEX IF NOT EXISTS members_email_key
  ON public.members (email);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'governance_votes_loan_request_id_fkey'
  ) THEN
    ALTER TABLE public.governance_votes
      ADD CONSTRAINT governance_votes_loan_request_id_fkey
      FOREIGN KEY (loan_request_id)
      REFERENCES public.loan_requests(id)
      ON DELETE RESTRICT
      ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'governance_votes_member_id_fkey'
  ) THEN
    ALTER TABLE public.governance_votes
      ADD CONSTRAINT governance_votes_member_id_fkey
      FOREIGN KEY (member_id)
      REFERENCES public.members(id)
      ON DELETE RESTRICT
      ON UPDATE CASCADE;
  END IF;
END $$;