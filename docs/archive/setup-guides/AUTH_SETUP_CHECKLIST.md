# Authentication Setup Checklist

**Status:** 🟡 **Almost Complete** - Final Steps Needed

**Quick Status Check:** Run `python3 check_supabase_status.py` to see current configuration status.

---

## ✅ What's Done

- ✅ Frontend auth code implemented (Supabase clients, auth context, login/signup pages)
- ✅ Backend database connection configured for Supabase
- ✅ Database migrations created (001_initial_schema.sql, 004_supabase_auth_integration.sql)
- ✅ Test scripts available (backend/scripts/test_auth_flow.py, verify_supabase_setup.py)

---

## ⚠️ Final Steps Needed

### 1. Create/Verify Supabase Project

If you haven't already:
1. Go to https://supabase.com
2. Create new project: `lexicraft-mvp`
3. Region: `Southeast Asia (Singapore)`
4. Get API keys from Settings → API

### 2. Add Frontend Environment Variables

**Local Development:**
Create `landing-page/.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

**Vercel Deployment:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Select all environments (Production, Preview, Development)
4. Redeploy after adding variables

---

### 3. Add Backend Environment Variables

Add to `backend/.env`:
```bash
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_URL=https://xxxxx.supabase.co
```
(Note: `DATABASE_URL` should already exist)

### 4. Run Database Migrations

**First, run the initial schema:**
1. Go to **SQL Editor** in Supabase dashboard
2. Copy contents of `backend/migrations/001_initial_schema.sql`
3. Paste and click **"Run"**

**Then, update users table for Supabase Auth:**
```sql
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
```

**Finally, run the auth integration migration:**
1. Go to **SQL Editor** in Supabase dashboard
2. Copy contents of `backend/migrations/004_supabase_auth_integration.sql`
3. Paste and click **"Run"**

**What the auth integration migration does:**
- Creates trigger function `handle_new_user()` to auto-create user records
- Creates trigger `on_auth_user_created` on `auth.users` table
- Links Supabase Auth users to your `users` table automatically
- Sets up Row Level Security (RLS) policies

---

### 5. Test Authentication

**Quick Verification:**
```bash
# Check configuration status
python3 check_supabase_status.py

# Verify environment variables
python3 backend/scripts/verify_supabase_setup.py

# Full integration test (requires Supabase project)
python3 backend/scripts/test_auth_flow.py
```

**Manual Testing:**

After redeploying Vercel with environment variables:

1. **Test Signup:**
   - Visit: `https://lexicraft-landing.vercel.app/zh-TW/signup`
   - Try email/password signup
   - Should redirect to `/dashboard`

2. **Test Login:**
   - Visit: `https://lexicraft-landing.vercel.app/zh-TW/login`
   - Try logging in
   - Should redirect to `/dashboard`

3. **Test Protected Route:**
   - Log out
   - Try visiting `/dashboard`
   - Should redirect to `/login`

4. **Test Google OAuth (if enabled):**
   - Click "使用 Google 登入"
   - Complete OAuth flow
   - Should redirect to `/dashboard`

---

## 🐛 Troubleshooting

### "Invalid API key" error
- ✅ Check environment variables are set in Vercel
- ✅ Verify keys are correct (no extra spaces)
- ✅ Make sure you redeployed after adding variables

### "User not found" after signup
- ✅ Check if database trigger was created
- ✅ Verify trigger is active in Supabase
- ✅ Check Supabase logs for errors

### Redirect not working
- ✅ Check callback URL in Supabase Auth settings
- ✅ Verify redirect URL matches your domain

---

## 🎯 Next Steps After Auth Works

1. **Create Child Account Management**
   - API endpoint: `POST /api/children`
   - Parent creates child accounts
   - Link to `children` table

2. **Update Dashboard**
   - Fetch real child IDs from database
   - Show actual balance from `points_accounts`
   - Display user's children

3. **Connect Deposits**
   - Use real `user_id` from auth
   - Link deposits to authenticated user
   - Update `child_id` to use real child from database

---

**Status:** Ready to test once trigger is created and Vercel is redeployed!

