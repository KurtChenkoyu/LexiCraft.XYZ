# Supabase Email Confirmation Setup

**Strategy**: Low-friction signup with selective confirmation requirements

---

## Supabase Dashboard Configuration

### Step 1: Disable Email Confirmation Requirement

1. Go to **Supabase Dashboard** → **Authentication** → **Settings** → **Email Auth**
2. Find **"Enable email confirmations"**
3. Toggle it **OFF**
4. Click **"Save"**

**Why:** This allows users to sign up and use the app immediately without waiting for email confirmation.

### Step 2: Keep Confirmation Emails Enabled

Even though confirmation isn't required, you should still:
1. Keep **"Send confirmation email"** enabled
2. Users will receive confirmation emails
3. They can confirm when ready (to enable withdrawals)

### Step 3: Configure Email Templates (Optional)

1. Go to **Authentication** → **Email Templates**
2. Customize the confirmation email template
3. Add your branding and messaging

---

## How It Works

### Signup Flow
1. User signs up → **No confirmation required**
2. User can immediately:
   - Access the dashboard
   - Make deposits
   - Use all features
3. Confirmation email is sent (but not blocking)

### Sensitive Actions
1. User tries to withdraw → **Email confirmation required**
2. If not confirmed:
   - Error: "Please confirm your email to enable withdrawals"
   - Banner shown on dashboard
3. User confirms email → Can withdraw

### Email Confirmation Status
- Tracked in `users.email_confirmed` field
- Synced from `auth.users.email_confirmed`
- Updated automatically when user confirms

---

## Database Migrations

Run these migrations in order:

1. **005_email_confirmation_tracking.sql** - Adds email confirmation fields
2. **006_update_trigger_for_email_confirmation.sql** - Updates triggers to track confirmation

**In Supabase SQL Editor:**
1. Run `backend/migrations/005_email_confirmation_tracking.sql`
2. Run `backend/migrations/006_update_trigger_for_email_confirmation.sql`

---

## Testing

### Test Signup (No Confirmation Required)
1. Sign up with a new email
2. Should redirect to dashboard immediately
3. Should see email confirmation banner (if not confirmed)

### Test Withdrawal (Confirmation Required)
1. Try to create withdrawal request
2. If email not confirmed → Should get error
3. Confirm email → Should be able to withdraw

### Test Email Confirmation
1. Check email for confirmation link
2. Click link → Email confirmed
3. Banner should disappear
4. Should be able to withdraw

---

## Benefits

✅ **Low Friction**: Users can sign up and pay immediately  
✅ **Security**: Sensitive actions still protected  
✅ **Flexibility**: Can adjust requirements per action  
✅ **Industry Standard**: Same pattern as Stripe, PayPal, etc.

---

**Status**: ✅ Ready to use after running migrations


