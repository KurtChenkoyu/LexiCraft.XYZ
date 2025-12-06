# Supabase Authentication Setup Guide

**Status:** ✅ **Code Complete** - Needs Supabase Project Setup

---

## ✅ What's Been Implemented

### Frontend Components
- ✅ Supabase client setup (browser & server)
- ✅ Auth context/provider for user state
- ✅ Login page (`/login`) with Google OAuth + email/password
- ✅ Signup page (`/signup`) with Google OAuth + email/password
- ✅ Auth callback handler (`/auth/callback`)
- ✅ Protected dashboard route
- ✅ Navbar with login/logout buttons
- ✅ Middleware for session refresh

### Features
- ✅ Google Sign-In (OAuth)
- ✅ Email/password authentication
- ✅ Session management
- ✅ Protected routes
- ✅ Auto-redirect to login when not authenticated

---

## 🚀 Setup Instructions

### Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Sign up or log in
3. Click **"New Project"**
4. Fill in:
   - **Name**: `lexicraft-mvp`
   - **Database Password**: (choose strong password, save it!)
   - **Region**: `Southeast Asia (Singapore)` (closest to Taiwan)
5. Click **"Create new project"**
6. Wait 2-3 minutes for setup

---

### Step 2: Get Supabase Keys

1. In Supabase dashboard, go to **Settings** → **API**
2. You'll see:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

Copy both values.

---

### Step 3: Configure Site URL (IMPORTANT!)

**This is critical for OAuth redirects!**

1. Go to **Settings** → **Authentication** → **URL Configuration**
2. Set **Site URL** to your production domain:
   ```
   https://lexicraft-landing.vercel.app
   ```
3. Add **Redirect URLs** (one per line):
   ```
   https://lexicraft-landing.vercel.app/**
   http://localhost:3000/**
   ```
   - The `**` wildcard allows all paths under that domain
   - Add both production and localhost for development
4. Click **"Save"**

**Why this matters:** Supabase uses the Site URL as a fallback redirect destination. If it's set to `http://localhost:3000`, users will be redirected there even from production!

---

### Step 4: Enable Google OAuth (Optional but Recommended)

1. Go to **Authentication** → **Providers**
2. Find **Google** and click **"Enable"**
3. You'll need:
   - **Client ID**: From Google Cloud Console
   - **Client Secret**: From Google Cloud Console
4. **Redirect URL**: Add this to Google OAuth settings:
   ```
   https://xxxxx.supabase.co/auth/v1/callback
   ```

**To get Google OAuth credentials:**
1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Add authorized redirect URI: `https://xxxxx.supabase.co/auth/v1/callback`
6. Copy Client ID and Client Secret to Supabase

---

### Step 5: Add Environment Variables

#### Local Development (`.env.local`)

Create `landing-page/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Vercel Deployment

1. Go to Vercel Dashboard → Your Project → **Settings** → **Environment Variables**
2. Add:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. Select all environments (Production, Preview, Development)
4. Click **"Save"**
5. **Redeploy** your project

---

### Step 5: Configure Supabase Database

Your PostgreSQL schema already exists in `backend/migrations/001_initial_schema.sql`.

**Option A: Use Supabase SQL Editor (Recommended)**
1. Go to **SQL Editor** in Supabase dashboard
2. Click **"New query"**
3. Copy contents of `backend/migrations/001_initial_schema.sql`
4. Paste and click **"Run"**

**Option B: Use Supabase as PostgreSQL**
- Your existing `DATABASE_URL` can point to Supabase
- Supabase provides PostgreSQL, so you can use the same connection string

---

### Step 6: Link Supabase Auth to Your Database

Supabase Auth creates a `auth.users` table automatically. You need to link it to your `users` table.

**Create a trigger in Supabase SQL Editor:**

```sql
-- Function to create user record when auth user is created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, name, created_at)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', ''),
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call function on auth user creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

This automatically creates a `users` record when someone signs up via Supabase Auth.

---

## 🧪 Testing

### Test Email/Password Signup
1. Visit `/signup`
2. Enter name, email, password
3. Click "註冊"
4. Should redirect to `/dashboard`

### Test Google Sign-In
1. Visit `/login` or `/signup`
2. Click "使用 Google 登入"
3. Complete Google OAuth flow
4. Should redirect to `/dashboard`

### Test Protected Routes
1. Log out
2. Try to visit `/dashboard`
3. Should redirect to `/login`

---

## 📝 Next Steps

### After Auth is Working

1. **Create Child Accounts API**
   - Endpoint: `POST /api/children`
   - Parent creates child accounts
   - Link to `children` table

2. **Update Dashboard**
   - Fetch real child IDs from database
   - Show actual balance from `points_accounts`
   - Display transaction history

3. **Connect Deposits**
   - Link deposits to authenticated user
   - Use real `user_id` and `child_id` in Stripe metadata

---

## 🔒 Security Notes

- ✅ Supabase handles password hashing automatically
- ✅ JWT tokens managed by Supabase
- ✅ Session refresh in middleware
- ✅ Protected routes redirect to login
- ⚠️ Make sure `NEXT_PUBLIC_SUPABASE_ANON_KEY` is public (safe to expose)
- ⚠️ Never expose service role key in frontend

---

## 🐛 Troubleshooting

### "Invalid API key"
- Check `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are correct
- Make sure they're set in Vercel environment variables
- Redeploy after adding variables

### "Redirect URI mismatch" (Google OAuth)
- Check redirect URI in Google Cloud Console matches Supabase callback URL
- Format: `https://xxxxx.supabase.co/auth/v1/callback`

### "User not found" after signup
- Check if trigger function was created
- Verify `users` table exists
- Check Supabase logs for errors

---

**Status:** ✅ **Ready for Setup**

Once you create the Supabase project and add environment variables, authentication will work!

