# Phase 2: Next Steps Checklist

**Status:** OAuth separated ✅ | Ready for final configuration

## Quick Checklist

### 1. Configure Production Supabase URLs ⏳

**Time:** 2 minutes  
**Guide:** `docs/PHASE2_PROD_SUPABASE_CHECKLIST.md`

**Action:**
- Go to Production Supabase Dashboard → Authentication → URL Configuration
- Set **Site URL:** `https://lexicraft.xyz`
- **Redirect URLs:** 
  - ✅ Add: `https://lexicraft.xyz/**`
  - ✅ Add: `https://www.lexicraft.xyz/**` (if using www)
  - ❌ Remove: `http://localhost:3000/**` (if present)

**Why:** Prevents production users from being redirected to localhost.

---

### 2. Set Railway Backend Environment Variables ⏳

**Time:** 5-10 minutes  
**Guide:** `docs/PHASE2_RAILWAY_CONFIGURATION.md` (Backend section)

**Required Variables:**
```bash
DATABASE_URL=postgresql://postgres.[PROD_REF]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[PROD_REF].supabase.co
SUPABASE_JWT_SECRET=[PROD_JWT_SECRET]  # From prod Supabase → Settings → API → Legacy JWT Secret
ALLOWED_ORIGINS=https://lexicraft.xyz,https://www.lexicraft.xyz
STRIPE_SECRET_KEY=sk_live_...  # Live mode key (not test!)
```

**Where:** Railway Dashboard → Backend Service → Variables

---

### 3. Set Vercel Frontend Environment Variables ⏳

**Time:** 5-10 minutes  
**Guide:** `docs/PHASE2_RAILWAY_CONFIGURATION.md` (Frontend section)

**Required Variables:**
```bash
NEXT_PUBLIC_SITE_URL=https://lexicraft.xyz
NEXT_PUBLIC_SUPABASE_URL=https://[PROD_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[PROD_ANON_KEY]  # Publishable key from prod Supabase
NEXT_PUBLIC_API_URL=https://[BACKEND_RAILWAY_URL].railway.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...  # Live mode key (not test!)
```

**Where:** Vercel Dashboard → Project → Settings → Environment Variables

---

### 4. Test Dev Environment ✅

**Time:** 5 minutes

**Test:**
1. Start local backend: `cd backend && uvicorn src.main:app --reload`
2. Start local frontend: `cd landing-page && npm run dev`
3. Visit `http://localhost:3000`
4. Test signup/login (should use dev Supabase)
5. Verify user appears in **dev** Supabase project (not production)

**Expected:**
- ✅ Authentication works
- ✅ User created in dev Supabase
- ✅ No errors in console

---

### 5. Test Production Environment ✅

**Time:** 5 minutes

**Test:**
1. Visit `https://lexicraft.xyz`
2. Test signup/login (should use prod Supabase)
3. Verify user appears in **production** Supabase project
4. Test payment flow (should use live Stripe - be careful!)

**Expected:**
- ✅ Authentication works
- ✅ User created in prod Supabase
- ✅ No errors in console
- ✅ API calls work (check Network tab)

---

## Verification Checklist

After completing all steps:

- [ ] Production Supabase Site URL: `https://lexicraft.xyz`
- [ ] Production Supabase Redirect URLs: Only production domains (no localhost)
- [ ] Railway backend variables: All set with production values
- [ ] Vercel frontend variables: All set with production values
- [ ] Dev environment: Works with dev Supabase
- [ ] Prod environment: Works with prod Supabase
- [ ] OAuth: Dev and prod separated
- [ ] Payment keys: Test mode in dev, live mode in prod

---

## Troubleshooting

**Issue: Production redirects to localhost**
- **Fix:** Check production Supabase Site URL is `https://lexicraft.xyz` (not localhost)

**Issue: CORS errors in production**
- **Fix:** Verify `ALLOWED_ORIGINS` in Railway includes `https://lexicraft.xyz`

**Issue: Authentication fails in production**
- **Fix:** Check `NEXT_PUBLIC_SUPABASE_URL` in Vercel points to production Supabase

**Issue: Payment test mode in production**
- **Fix:** Verify Stripe keys in Railway/Vercel are live mode (`sk_live_`, `pk_live_`)

---

## What's After Phase 2?

Once Phase 2 is complete:
- ✅ Dev and prod environments fully separated
- ✅ Safe local development without affecting production
- ✅ Production secured with proper environment variables
- ✅ Ready for ongoing development on `develop` branch

**Next:** Continue development on `develop` branch, merge to `main` when ready for production release.

