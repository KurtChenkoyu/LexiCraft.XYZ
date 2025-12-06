# Email Confirmation Strategy

**Industry Standard: Low-Friction Signup with Selective Confirmation Requirements**

---

## Overview

This document outlines LexiCraft's email confirmation strategy, following industry best practices used by Stripe, PayPal, Coinbase, and other financial platforms.

---

## Strategy

### Core Principle
**Allow signup and payments without friction, require confirmation for sensitive actions.**

### User Flow

1. **Signup** → No email confirmation required
   - User can immediately use the app
   - Can make deposits/payments
   - Can browse and learn

2. **Sensitive Actions** → Email confirmation required
   - Withdrawals
   - Account changes (email, password)
   - High-value transactions
   - Access to sensitive data

3. **Soft Prompts** → Non-blocking reminders
   - Banner on dashboard
   - Reminder emails
   - In-app notifications

---

## Implementation

### Database Schema

The `users` table tracks email confirmation status:

```sql
email_confirmed BOOLEAN DEFAULT FALSE
email_confirmed_at TIMESTAMP
```

### Signup Flow

- **No email confirmation required** for signup
- User can immediately access the app
- Session is created immediately

### Sensitive Actions Requiring Confirmation

1. **Withdrawals**
   - Check: `if (!user.email_confirmed) return error`
   - Message: "Please confirm your email to enable withdrawals"

2. **Account Changes**
   - Changing email address
   - Changing password (if not logged in)
   - Account deletion

3. **High-Value Transactions**
   - Large withdrawals (>$1000)
   - Account transfers

### UI Prompts

- **Dashboard Banner**: Show if email not confirmed
- **Withdrawal Page**: Clear message about confirmation requirement
- **Settings Page**: Prominent "Confirm Email" button

---

## Configuration

### Supabase Settings

**Authentication → Settings → Email Auth:**
- ✅ **Enable email confirmations**: OFF (for low-friction signup)
- ✅ **Send confirmation email**: ON (so users can confirm when ready)
- ✅ **Email template**: Customize confirmation email

**Why this works:**
- Users can sign up without waiting for email
- Confirmation emails are still sent (for when they want to confirm)
- We check confirmation status in code, not at signup

---

## Code Implementation

### 1. Database Migration

See: `backend/migrations/005_email_confirmation_tracking.sql`

### 2. Signup Flow

- Updated to allow signup without confirmation
- Checks session availability
- Shows message if confirmation needed (but doesn't block)

### 3. Withdrawal Checks

```typescript
// In withdrawal API endpoint
if (!user.email_confirmed) {
  return error('Please confirm your email to enable withdrawals')
}
```

### 4. UI Components

- `EmailConfirmationBanner` - Shows on dashboard
- `EmailConfirmationPrompt` - Shows on withdrawal page
- Confirmation status in user profile

---

## Benefits

1. **Higher Conversion**: No friction at signup
2. **Better UX**: Users can start using immediately
3. **Security**: Sensitive actions still protected
4. **Flexibility**: Can adjust requirements per action

---

## Industry Examples

- **Stripe**: Pay without confirmation; confirm for payouts
- **PayPal**: Receive money without confirmation; confirm to withdraw
- **Coinbase**: Buy without confirmation; confirm to send/withdraw
- **Most SaaS**: Subscribe without confirmation; confirm for account changes

---

## Future Enhancements

1. **Grace Period**: Allow 7-30 days before requiring confirmation
2. **Reminder System**: Automated emails to confirm
3. **Progressive Disclosure**: Gradually require confirmation as usage increases
4. **Risk-Based**: Require confirmation based on transaction amount/risk

---

**Status**: ✅ Implemented
**Last Updated**: 2024-12-04

