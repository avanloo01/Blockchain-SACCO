-- Add tx_signature column to governance_votes for on-chain vote anchoring
ALTER TABLE governance_votes ADD COLUMN tx_signature TEXT;
