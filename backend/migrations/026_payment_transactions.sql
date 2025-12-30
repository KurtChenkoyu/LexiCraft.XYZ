-- ============================================
-- Migration: Add Payment Transactions Table and Billing Customer ID
-- Created: 2024-12-30
-- Description: 
--   1. Add billing_customer_id to users table (required for Lemon Squeezy portal API)
--   2. Create payment_transactions table for local ledger pattern (vendor-agnostic payment history)
-- ============================================

-- 1. Add billing_customer_id to users table
-- This stores the Lemon Squeezy customer_id, required for generating portal URLs
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS billing_customer_id TEXT;

-- Create index for fast lookups when generating portal URLs
CREATE INDEX IF NOT EXISTS idx_users_billing_customer_id 
ON users(billing_customer_id) 
WHERE billing_customer_id IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN users.billing_customer_id IS 'Lemon Squeezy customer_id - required for generating customer portal URLs. Populated automatically by webhook handler.';

-- 2. Create payment_transactions table
-- This implements the "Local Ledger Pattern" - we maintain our own payment history
-- independent of the payment provider, enabling vendor-agnostic reporting and migration
CREATE TABLE IF NOT EXISTS payment_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,  -- 'lemonsqueezy', 'stripe', etc.
  provider_transaction_id TEXT NOT NULL,  -- External transaction ID (e.g., Lemon Squeezy order_id)
  amount INTEGER NOT NULL,  -- Amount in cents (e.g., 999 = $9.99)
  currency TEXT NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL,  -- 'succeeded', 'pending', 'failed', 'refunded'
  invoice_url TEXT,  -- Link to invoice/receipt
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX idx_payment_transactions_provider ON payment_transactions(provider);
CREATE INDEX idx_payment_transactions_created_at ON payment_transactions(created_at DESC);
CREATE INDEX idx_payment_transactions_provider_transaction_id ON payment_transactions(provider, provider_transaction_id);

-- Add comments for documentation
COMMENT ON TABLE payment_transactions IS 'Local ledger of all payment transactions - vendor-agnostic payment history for reporting and migration';
COMMENT ON COLUMN payment_transactions.amount IS 'Amount in cents (integer) to avoid floating-point precision issues';
COMMENT ON COLUMN payment_transactions.provider IS 'Payment provider identifier (lemonsqueezy, stripe, etc.)';
COMMENT ON COLUMN payment_transactions.provider_transaction_id IS 'External transaction ID from provider - allows lookup in external systems';

