# Complete Your Existing Supabase Setup

You already have a Supabase project! Here's what you need to finish:

**Your Supabase Project:** `cwgexbjyfcqndeyhravb.supabase.co`

---

## What You Already Have ✅

- ✅ Supabase project created
- ✅ Database connection configured (`DATABASE_URL` in `backend/.env`)
- ✅ Supabase URL and anon key in `backend/.env`

---

## What You Need to Do (15 minutes)

### Step 1: Get Secret Key from Your Existing Project

Supabase has updated their API key system. You have two options:

**Option A: Use New Secret Key (Recommended)**
1. Go to **https://supabase.com/dashboard/project/cwgexbjyfcqndeyhravb**
2. Click **Settings** → **API** → **"Publishable and secret API keys"** tab (should be selected by default)
3. In the **"Secret keys"** section, find the **"default"** key
4. Click the **eye icon** 👁️ to reveal the full key
5. Click the **copy icon** to copy it (keep it secret!)

**Option B: Use Legacy Service Role Key**
1. In the same API settings page, click the **"Legacy anon, service_role API keys"** tab
2. Scroll down to find **"service_role"** key
3. Copy this key (keep it secret!)

### Step 2: Add Missing Backend Environment Variable

Add to `backend/.env`:
```bash
# Use the secret key from Step 1 (either new secret key or legacy service_role key)
SUPABASE_SERVICE_ROLE_KEY=your-secret-key-here
SUPABASE_URL=https://cwgexbjyfcqndeyhravb.supabase.co
```

**Note:** The variable name is still `SUPABASE_SERVICE_ROLE_KEY` for compatibility, but you can use either:
- The new **secret key** (starts with `sb_secret_...`)
- The legacy **service_role key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

(You already have `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in backend/.env, but they should be in frontend)

### Step 3: Create Frontend Environment File

Create `landing-page/.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://cwgexbjyfcqndeyhravb.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_s52K0oEmrobynJTT4I-XGA_GjwmP1mr
```

**Note:** Use the **Publishable key** from the "Publishable and secret API keys" tab. This is safe to use in the browser.

### Step 4: Configure Authentication Settings

1. In Supabase dashboard → **Settings** → **Authentication** → **URL Configuration**
2. Set **Site URL**: `https://lexicraft-landing.vercel.app` (or your production URL)
3. Add **Redirect URLs**:
   ```
   https://lexicraft-landing.vercel.app/**
   http://localhost:3000/**
   ```
4. Click **"Save"**

5. **Disable Email Confirmation Requirement** (for low-friction signup):
   - Go to **Authentication** → **Settings** → **Email Auth**
   - Toggle **"Enable email confirmations"** to **OFF**
   - Click **"Save"**
   - Note: Confirmation emails are still sent, but not required for signup

### Step 5: Run Database Migrations (if not already done)

1. Go to Supabase dashboard → **SQL Editor**
2. Check if `users` table exists (go to **Table Editor**)
3. If tables don't exist, run `backend/migrations/001_initial_schema.sql`
4. Run: `ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;`
5. Run `backend/migrations/004_supabase_auth_integration.sql`
6. Run `backend/migrations/005_email_confirmation_tracking.sql` (adds email confirmation fields)
7. Run `backend/migrations/006_update_trigger_for_email_confirmation.sql` (updates triggers)
6. Run `backend/migrations/005_email_confirmation_tracking.sql` (adds email confirmation fields)
7. Run `backend/migrations/006_update_trigger_for_email_confirmation.sql` (updates triggers)

### Step 6: Verify Setup

```bash
# Check status
python3 check_supabase_status.py

# Test backend connection
cd backend && python3 scripts/verify_supabase_setup.py
```

---

## Quick Checklist

- [ ] Get secret key from Supabase dashboard (new secret key or legacy service_role)
- [ ] Add `SUPABASE_SERVICE_ROLE_KEY` to `backend/.env` (use the secret key you copied)
- [ ] Add `SUPABASE_URL` to `backend/.env` (if not there)
- [ ] Create `landing-page/.env.local` with Supabase keys
- [ ] Configure Site URL and Redirect URLs in Supabase
- [ ] Run database migrations (if needed)
- [ ] Test: `python3 check_supabase_status.py`

---

That's it! You're using your existing Supabase project, just need to add the missing pieces.

