# Testing Strategy: Systematic Test User Management

**Purpose:** Guide for creating and managing test users to systematically test different scenarios in LexiCraft.

---

## Quick Start

### 1. Confirm Fake Email Users (SQL)

For test accounts with fake emails that can't receive confirmation links:

```sql
-- Run in Supabase SQL Editor: backend/scripts/confirm_test_user.sql
UPDATE auth.users
SET 
  email_confirmed_at = NOW(),
  email_confirmed = true
WHERE email = '554rrttg@gmail.com';
```

### 2. Create Standardized Test Accounts

Use the automated seed script to create test accounts with different personas:

```bash
cd backend
source venv/bin/activate

# Create all test accounts
python scripts/seed_test_accounts.py

# Reset all test accounts to known state
python scripts/seed_test_accounts.py --reset

# List existing test accounts
python scripts/seed_test_accounts.py --list

# Delete all test accounts
python scripts/seed_test_accounts.py --delete

# Create only one persona
python scripts/seed_test_accounts.py --persona fresh
```

**All test accounts use password:** `TestPassword123!`

---

## Test Account Personas

The seed script creates these standardized personas:

| Persona | Email | Description | Use Case |
|---------|-------|-------------|----------|
| `fresh` | `test+fresh@lexicraft.xyz` | New user, no progress, Level 1 | Test onboarding, first-time experience |
| `active` | `test+active@lexicraft.xyz` | 7-day streak, Level 5, 50 words | Test normal gameplay, progress tracking |
| `power` | `test+power@lexicraft.xyz` | Level 15, 45-day streak, 500 words, many achievements | Test advanced features, leaderboards |
| `churned` | `test+churned@lexicraft.xyz` | Was active, broken streak | Test re-engagement flows, notifications |
| `edge_levelup` | `test+edge@lexicraft.xyz` | 5 XP away from level up | Test level-up animations, rewards |
| `edge_achieve` | `test+achieve@lexicraft.xyz` | 99 words (1 away from 100-word achievement) | Test achievement unlocks, edge cases |

---

## Testing Scenarios by Feature

### Onboarding Flow

**Test Users Needed:**
- `fresh` persona (new user)
- Manual: Parent account (age 25+)
- Manual: Learner account (age 20+)
- Manual: Parent + Learner account (`account_type == 'both'`)
- Manual: Child account (age < 20)

**Test Steps:**
1. Sign up as each account type
2. Verify role assignment (`parent`, `learner`, or both)
3. Verify learner profile creation
4. Verify email confirmation status (should not block login)

**Quick Setup:**
```bash
# Create fresh persona
python scripts/seed_test_accounts.py --persona fresh

# Then manually sign up additional account types via UI
```

### Email Confirmation

**Test Users Needed:**
- Unconfirmed user (fake email)
- Confirmed user

**Test Steps:**
1. Try to withdraw with unconfirmed email → Should show error
2. Confirm email via SQL (for fake emails) or email link (for real emails)
3. Try to withdraw again → Should succeed

**Quick Setup:**
```sql
-- Confirm a test user
UPDATE auth.users
SET email_confirmed_at = NOW(), email_confirmed = true
WHERE email = 'test+fresh@lexicraft.xyz';
```

### Payment Flows

**Test Users Needed:**
- User with confirmed email
- User with wallet balance
- User with pending withdrawal

**Test Steps:**
1. Make deposit (Stripe test mode)
2. Verify wallet balance updates
3. Request withdrawal (should require confirmed email)
4. Verify withdrawal flow

**Quick Setup:**
```bash
# Use 'active' persona (has progress, can test payments)
python scripts/seed_test_accounts.py --persona active

# Confirm email
# Then test deposit/withdrawal flows
```

### Gamification Features

**Test Users Needed:**
- `edge_levelup` (tests level-up animation)
- `edge_achieve` (tests achievement unlock)
- `power` (tests leaderboard ranking)
- `churned` (tests re-engagement)

**Test Steps:**
1. Log in as `edge_levelup`
2. Complete one more activity → Should trigger level-up animation
3. Log in as `edge_achieve`
4. Learn one more word → Should unlock achievement
5. Check leaderboard → `power` should be ranked

**Quick Setup:**
```bash
# Create all gamification personas
python scripts/seed_test_accounts.py --persona edge_levelup
python scripts/seed_test_accounts.py --persona edge_achieve
python scripts/seed_test_accounts.py --persona power
python scripts/seed_test_accounts.py --persona churned
```

### Parent Dashboard

**Test Users Needed:**
- Parent account with children
- Parent account without children
- Parent + Learner account (can switch roles)

**Test Steps:**
1. Log in as parent
2. Add child account
3. View child progress
4. Set goals for child
5. Switch to learner view (if `account_type == 'both'`)

**Quick Setup:**
```bash
# Create fresh parent account manually via UI
# Then add children via parent dashboard
```

---

## Manual Test User Creation

For scenarios not covered by seed personas, create users manually:

### Via UI (Recommended for Real Testing)

1. Go to `/signup`
2. Create account with test email (e.g., `test+scenario@lexicraft.xyz`)
3. Complete onboarding
4. Test the scenario

### Via SQL (For Quick Setup)

```sql
-- Create auth user (will trigger user record creation)
-- Note: This requires Supabase Admin API or manual Supabase dashboard creation
-- Better to use the seed script or UI signup
```

### Via Seed Script (For Custom Personas)

Edit `backend/scripts/seed_test_accounts.py`:

```python
TEST_PERSONAS = {
    # ... existing personas ...
    "custom_scenario": {
        "name": "Custom Test User",
        "description": "Tests specific scenario X",
        "level": 10,
        "xp": 5000,
        "streak_days": 14,
        # ... other config ...
    }
}
```

Then run:
```bash
python scripts/seed_test_accounts.py --persona custom_scenario
```

---

## Best Practices

### 1. Use Seed Script for Standard Scenarios

The seed script ensures:
- ✅ Consistent test data
- ✅ Known passwords (`TestPassword123!`)
- ✅ Predictable user states
- ✅ Easy reset (`--reset` flag)

### 2. Reset Test Accounts Regularly

```bash
# Before major testing session
python scripts/seed_test_accounts.py --reset
```

This ensures you're testing with known, clean state.

### 3. Confirm Fake Email Users

For test accounts with fake emails, always confirm them via SQL:

```sql
-- Confirm all test accounts
UPDATE auth.users
SET email_confirmed_at = NOW(), email_confirmed = true
WHERE email LIKE 'test+%@lexicraft.xyz';
```

### 4. Use Environment-Specific Test Accounts

- **Dev environment:** Use `test+*@lexicraft.xyz` accounts
- **Production:** Never use test accounts (use real emails for QA)

### 5. Document Custom Scenarios

If you create a custom test user for a specific bug/feature:
1. Document the scenario in this file
2. Consider adding it to `seed_test_accounts.py` if it's reusable
3. Delete the test user after testing (or use `--delete` to clean up)

---

## Troubleshooting

### Test User Can't Log In

1. **Check email confirmation:**
   ```sql
   SELECT email, email_confirmed, email_confirmed_at
   FROM auth.users
   WHERE email = 'test+fresh@lexicraft.xyz';
   ```

2. **Confirm if needed:**
   ```sql
   UPDATE auth.users
   SET email_confirmed_at = NOW(), email_confirmed = true
   WHERE email = 'test+fresh@lexicraft.xyz';
   ```

### Test User Missing Role

```sql
-- Check roles
SELECT user_id, role FROM user_roles WHERE user_id = 'USER_ID';

-- Add missing role
INSERT INTO user_roles (user_id, role, created_at)
VALUES ('USER_ID', 'learner', NOW())
ON CONFLICT (user_id, role) DO NOTHING;
```

### Test User Missing Learner Profile

```sql
-- Check learner profile
SELECT * FROM learners WHERE user_id = 'USER_ID';

-- Create if missing (via API or manual insert)
-- Better to use the onboarding API endpoint
```

---

## Reference

- **Seed Script:** `backend/scripts/seed_test_accounts.py`
- **Confirm Script:** `backend/scripts/confirm_test_user.sql`
- **Testing Guide:** `docs/31-testing-guide.md`
- **Environment Setup:** `README_ENV.md`

---

## Quick Command Reference

```bash
# Create all test accounts
python scripts/seed_test_accounts.py

# Reset all test accounts
python scripts/seed_test_accounts.py --reset

# List test accounts
python scripts/seed_test_accounts.py --list

# Delete all test accounts
python scripts/seed_test_accounts.py --delete

# Create specific persona
python scripts/seed_test_accounts.py --persona fresh
```

```sql
-- Confirm test user email
UPDATE auth.users
SET email_confirmed_at = NOW(), email_confirmed = true
WHERE email = 'test+fresh@lexicraft.xyz';

-- Confirm all test accounts
UPDATE auth.users
SET email_confirmed_at = NOW(), email_confirmed = true
WHERE email LIKE 'test+%@lexicraft.xyz';
```

