-- Add interest_rate_apr column to loan_requests
ALTER TABLE loan_requests ADD COLUMN interest_rate_apr DOUBLE PRECISION NOT NULL DEFAULT 0;
