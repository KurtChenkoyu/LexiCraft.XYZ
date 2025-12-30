# Webhook Failures: Manual Payment Activation Guide

**Last Updated**: 2024-12-30  
**Purpose**: Step-by-step guide for manually activating user subscriptions when webhooks fail

## Overview

When Lemon Squeezy payment webhooks fail (network issues, email mismatch, backend downtime), users who paid are stuck with `subscription_status = NULL` and cannot access onboarding or the app. This guide provides a reliable way to manually activate subscriptions without code changes.

**Time Required**: 5-10 minutes per user

## When to Use Manual Activation

Use this guide when:

- ✅ User reports: "I paid but can't access onboarding"
- ✅ User is stuck on payment verification screen (polling timeout)
- ✅ Webhook logs show failure (500 error, timeout, or no delivery)
- ✅ User's `subscription_status` is NULL but payment was successful in Lemon Squeezy
- ✅ Email mismatch occurred (user changed email in checkout, legacy case)

**Do NOT use this guide if:**
- ❌ User hasn't actually paid (verify in Lemon Squeezy dashboard first)
- ❌ User's subscription is already active (check database first)
- ❌ Issue is unrelated to payment (e.g., login problems)

## Prerequisites

Before starting, you need:

1. **Database Access**: Connection to production or development PostgreSQL database
2. **User Information**: At least one of:
   - User's email address (from payment receipt or user report)
   - User's user_id (UUID) if available
   - Lemon Squeezy order ID (to find customer email)
3. **Payment Details**: From Lemon Squeezy dashboard:
   - Subscription status ('active' or 'trial')
   - Plan type ('lifetime', '6-month-pass', '12-month-pass', etc.)
   - Subscription end date (or NULL for lifetime plans)

## Step 1: Find the User ID

You need the user's UUID to activate their subscription. Use one of these methods:

### Method 1: Find by Email (Most Common)

**When to use**: User provides their email address

1. Connect to the database (production or development)
2. Run this query (replace `user@example.com` with actual email):

```sql
SELECT 
  id,
  email,
  name,
  subscription_status,
  plan_type,
  subscription_end_date
FROM public.users
WHERE email = 'user@example.com';
```

3. **Copy the `id` (UUID)** - you'll need this for activation
4. **Verify**: Check that email and name match the user's account

**Example Output:**
```
id                                   | email              | name      | subscription_status | plan_type | subscription_end_date
-------------------------------------|--------------------|-----------|---------------------|-----------|----------------------
123e4567-e89b-12d3-a456-426614174000| user@example.com   | John Doe  | NULL                | NULL      | NULL
```

### Method 2: Find by Lemon Squeezy Order

**When to use**: You have the Lemon Squeezy order ID but not the user's email

1. Go to Lemon Squeezy dashboard → Orders
2. Find the order by order ID
3. Copy the customer email from the order
4. Use Method 1 above to find the user by email

### Method 3: Find by Payment Date (Last Resort)

**When to use**: Email is unknown, but you know approximate signup time

1. Run this query to list recent users with NULL subscription_status:

```sql
SELECT 
  id,
  email,
  name,
  created_at
FROM public.users
WHERE subscription_status IS NULL
ORDER BY created_at DESC
LIMIT 20;
```

2. Match by timestamp (user signed up around payment time)
3. Verify email/name with user or payment receipt

## Step 2: Verify User Details

**CRITICAL**: Before activating, verify you have the correct user:

1. **Check Email**: Does the email match the payment receipt?
2. **Check Name**: Does the name match (if available)?
3. **Check Timestamp**: Does `created_at` make sense (user signed up before payment)?
4. **Check Current Status**: Is `subscription_status` NULL or 'inactive'?

**If anything doesn't match, STOP and verify the user_id before proceeding.**

## Step 3: Get Subscription Details from Lemon Squeezy

You need these values for the activation script:

1. **Go to Lemon Squeezy Dashboard** → Orders
2. **Find the order** by email or order ID
3. **Copy these details**:
   - **Subscription Status**: Usually 'active' or 'on_trial' (map to 'active' or 'trial')
   - **Plan Type**: From product name (e.g., '6-Month Pass' → '6-month-pass')
   - **End Date**: 
     - For lifetime plans: NULL
     - For time-limited plans: Calculate from purchase date + plan duration
     - Example: 6-month plan purchased Jan 1, 2025 → end date: '2025-07-01 23:59:59'

**Status Mapping:**
- Lemon Squeezy `active` → Database `'active'`
- Lemon Squeezy `on_trial` → Database `'trial'`
- Lemon Squeezy `cancelled` → Database `'inactive'`
- Lemon Squeezy `expired` → Database `'inactive'`

**Plan Type Mapping:**
- '6-Month Pass' → '6-month-pass'
- '12-Month Pass' → '12-month-pass'
- 'Lifetime Pass' → 'lifetime'
- 'Monthly Subscription' → 'monthly'
- 'Yearly Subscription' → 'yearly'

## Step 4: Run the Activation Script

1. **Open the SQL script**: `docs/scripts/manual_payment_activation.sql`

2. **Start a transaction** (safety wrapper):
   ```sql
   BEGIN;
   ```

3. **Verify user exists** (replace `USER_ID` with UUID from Step 1):
   ```sql
   SELECT 
     id,
     email,
     name,
     subscription_status,
     plan_type,
     subscription_end_date
   FROM public.users
   WHERE id = 'USER_ID'::uuid;
   ```
   
   **Verify**: Email and name match the payment receipt

4. **Run the UPDATE** (replace all placeholders):
   ```sql
   UPDATE public.users
   SET 
     subscription_status = 'active',              -- From Step 3
     plan_type = '6-month-pass',                  -- From Step 3
     subscription_end_date = '2025-07-01 23:59:59'::timestamp,  -- From Step 3 (or NULL for lifetime)
     updated_at = NOW()
   WHERE id = 'USER_ID'::uuid;                    -- From Step 1
   ```

5. **Verify the update** (run immediately after UPDATE):
   ```sql
   SELECT 
     id,
     email,
     subscription_status,
     plan_type,
     subscription_end_date,
     updated_at
   FROM public.users
   WHERE id = 'USER_ID'::uuid;
   ```
   
   **Check**:
   - `subscription_status` is now 'active' or 'trial' (not NULL)
   - `plan_type` matches the order
   - `subscription_end_date` is correct (or NULL for lifetime)
   - `updated_at` timestamp is recent

6. **Commit the transaction** (only if verification passed):
   ```sql
   COMMIT;
   ```

**If verification failed**: Run `ROLLBACK;` to undo changes

## Step 5: Verify Activation Worked

After committing, verify the user can now access the app:

1. **Check Database** (already done in Step 4)
2. **Ask User to Try Again**:
   - User should refresh the onboarding page
   - Payment verification should pass (no more polling timeout)
   - User should be able to complete onboarding
3. **Check User Profile** (if user has access):
   - Subscription status should show as active
   - Plan type should be visible

## Common Scenarios & Solutions

### Scenario A: Email Mismatch (Legacy Case)

**Problem**: User paid with different email than their account email

**Example**: 
- Account email: `personal@gmail.com`
- Payment email: `billing@company.com`

**Solution**:
1. Find user by **account email** (the one they use to log in)
2. Verify payment in Lemon Squeezy (by billing email)
3. Run activation script for **account email** (not billing email)
4. User can now access app with their account email

**Note**: Phase 1 (User ID passing) should prevent this in the future, but legacy cases may exist.

### Scenario B: Webhook Never Fired

**Problem**: No webhook logs, user definitely paid, but subscription_status is NULL

**Solution**:
1. Verify payment in Lemon Squeezy dashboard
2. Find user by email (Method 1)
3. Run activation script
4. **Check webhook configuration** to prevent future failures:
   - Verify webhook URL is correct
   - Verify webhook secret matches
   - Check webhook delivery logs in Lemon Squeezy

### Scenario C: Backend Was Down

**Problem**: Webhook logs show 500 error at time of payment

**Solution**:
1. Verify backend is now running
2. Find user by email
3. Run activation script
4. **Check backend logs** to identify why it failed
5. Fix backend issue to prevent future failures

### Scenario D: User Paid but Onboarding Still Blocked

**Problem**: User's subscription_status is 'active' but onboarding still shows payment check

**Solution**:
1. **This is NOT a webhook failure** - subscription is already active
2. Check frontend cache:
   - User should clear browser cache
   - User should refresh the page
   - User should try logging out and back in
3. Check if user has completed onboarding:
   - If yes, redirect to appropriate page (`/parent/dashboard` or `/learner/home`)
   - If no, check if there's a different blocker (e.g., missing learner profile)

## Rollback Instructions

If you made a mistake and need to undo the activation:

### Before Committing

If you haven't committed yet, simply run:
```sql
ROLLBACK;
```

This will undo all changes in the current transaction.

### After Committing

If you already committed, run this to reset subscription back to NULL:

```sql
BEGIN;

UPDATE public.users
SET 
  subscription_status = NULL,
  plan_type = NULL,
  subscription_end_date = NULL,
  updated_at = NOW()
WHERE id = 'USER_ID'::uuid;  -- Replace with actual UUID

-- Verify the rollback
SELECT 
  id,
  email,
  subscription_status,
  plan_type,
  subscription_end_date
FROM public.users
WHERE id = 'USER_ID'::uuid;

COMMIT;
```

**Note**: Only rollback if you're certain the activation was incorrect. If the user actually paid, they should have an active subscription.

## Verification Checklist

After activation, verify:

- [ ] Database shows `subscription_status = 'active'` or `'trial'`
- [ ] Database shows correct `plan_type`
- [ ] Database shows correct `subscription_end_date` (or NULL for lifetime)
- [ ] User can access onboarding page
- [ ] Payment verification passes (no polling timeout)
- [ ] User can complete onboarding
- [ ] User can access app features
- [ ] Subscription status shows in user profile (if available)

## Troubleshooting

### Problem: UPDATE returns "0 rows affected"

**Cause**: User_id is incorrect or user doesn't exist

**Solution**:
1. Re-run the "Find User" query (Step 1)
2. Verify the UUID is correct
3. Check for typos in the UUID

### Problem: UPDATE succeeds but subscription_status is still NULL

**Cause**: Transaction wasn't committed

**Solution**:
1. Check if you ran `COMMIT;`
2. If not, run `COMMIT;` now
3. Re-run verification query

### Problem: User still can't access onboarding after activation

**Cause**: Frontend cache or different issue

**Solution**:
1. Verify database shows active subscription
2. Ask user to clear browser cache
3. Ask user to log out and log back in
4. Check if there's a different blocker (e.g., missing learner profile)

### Problem: Can't find user by email

**Cause**: Email doesn't exist in database or typo

**Solution**:
1. Double-check email spelling
2. Try searching with partial email: `WHERE email LIKE '%partial%'`
3. Check if user signed up with different email
4. Ask user to confirm their account email

## Safety Reminders

- ✅ **Always verify user_id before UPDATE** - prevents activating wrong user
- ✅ **Always use BEGIN/COMMIT transaction** - allows rollback if mistake
- ✅ **Always verify after UPDATE** - confirms changes succeeded
- ✅ **Only commit if verification passes** - prevents bad data
- ✅ **Check Lemon Squeezy dashboard** - confirms payment was actually made
- ✅ **Document what you did** - helps with future troubleshooting

## Related Documentation

- **SQL Script**: `docs/scripts/manual_payment_activation.sql` - Full script with all queries
- **Webhook Verification**: `docs/WEBHOOK_VERIFICATION_REPORT.md` - Webhook setup and testing
- **Payment Flow Sprint**: `docs/PAYMENT_FLOW_SPRINT.md` - Overall payment flow documentation

## Support Contact

If you encounter issues not covered in this guide:

1. Check backend logs for webhook errors
2. Check Lemon Squeezy webhook delivery logs
3. Verify database connection and permissions
4. Contact development team with:
   - User email or user_id
   - Error message or symptoms
   - Steps you've already tried

