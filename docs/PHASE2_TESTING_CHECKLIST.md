# Phase 2: Environment Testing Checklist

## Dev Environment Testing (localhost)

### Prerequisites
- Backend running: `cd backend && uvicorn src.main:app --reload`
- Frontend running: `cd landing-page && npm run dev`
- Dev Supabase project active
- Dev OAuth configured

### Test 1: Authentication Flow ✅

**Steps:**
1. Visit `http://localhost:3000/zh-TW/login`
2. Click "使用 Google 登入" (Sign in with Google)
3. Complete Google OAuth flow
4. Should redirect back to localhost

**Expected:**
- ✅ Redirects to Google OAuth
- ✅ After auth, redirects back to `http://localhost:3000`
- ✅ User is logged in
- ✅ No errors in browser console

**Verify in Supabase:**
- Go to **Dev Supabase Dashboard** → Authentication → Users
- ✅ New user should appear in **dev** project (not production)

---

### Test 2: Database Connection ✅

**Steps:**
1. After logging in, navigate to any page that uses backend API
2. Check browser Network tab for API calls
3. Verify API calls succeed (status 200)

**Expected:**
- ✅ API calls to `http://localhost:8000` succeed
- ✅ No CORS errors
- ✅ Data loads correctly

**Verify in Backend Logs:**
- ✅ No database connection errors
- ✅ Queries execute successfully

---

### Test 3: Payment Flow (Test Mode) ✅

**Steps:**
1. Navigate to deposit/payment page
2. Try to create a test payment
3. Use Stripe test card: `4242 4242 4242 4242`

**Expected:**
- ✅ Payment form loads
- ✅ Can create checkout session
- ✅ Uses test mode (check Stripe Dashboard → Test mode)
- ✅ No real charges

**Verify:**
- ✅ Stripe Dashboard shows test payment (not live)
- ✅ Payment appears in test mode transactions

---

## Production Environment Testing (lexicraft.xyz)

### Prerequisites
- Production site deployed: `https://lexicraft.xyz`
- Production Supabase project active
- Production OAuth configured
- Railway backend deployed

### Test 1: Authentication Flow ✅

**Steps:**
1. Visit `https://lexicraft.xyz/zh-TW/login`
2. Click "使用 Google 登入" (Sign in with Google)
3. Complete Google OAuth flow
4. Should redirect back to lexicraft.xyz

**Expected:**
- ✅ Redirects to Google OAuth
- ✅ After auth, redirects back to `https://lexicraft.xyz` (NOT localhost!)
- ✅ User is logged in
- ✅ No errors in browser console

**Verify in Supabase:**
- Go to **Production Supabase Dashboard** → Authentication → Users
- ✅ New user should appear in **production** project (not dev)

---

### Test 2: API Connection ✅

**Steps:**
1. After logging in, navigate to any page that uses backend API
2. Check browser Network tab for API calls
3. Verify API calls succeed (status 200)

**Expected:**
- ✅ API calls to Railway backend succeed
- ✅ No CORS errors
- ✅ Data loads correctly

**Verify:**
- ✅ Railway backend logs show successful requests
- ✅ No database connection errors

---

### Test 3: Payment Flow (Live Mode) ⚠️

**⚠️ WARNING: This will process REAL payments!**

**Steps:**
1. Navigate to deposit/payment page
2. Verify it's using live mode (check environment)
3. **Only test if you're ready for real payments!**

**Expected:**
- ✅ Payment form loads
- ✅ Can create checkout session
- ✅ Uses live mode (check Stripe Dashboard → Live mode)
- ⚠️ Real charges will be processed

**Verify:**
- ✅ Stripe Dashboard shows live payment (not test)
- ✅ Payment appears in live mode transactions

---

## Environment Separation Verification

### Verify Dev Uses Dev Supabase ✅

**Check:**
1. Sign up new user on `http://localhost:3000`
2. Go to **Dev Supabase Dashboard** → Authentication → Users
3. ✅ User appears in dev project
4. Go to **Production Supabase Dashboard** → Authentication → Users
5. ✅ User does NOT appear in production project

### Verify Prod Uses Prod Supabase ✅

**Check:**
1. Sign up new user on `https://lexicraft.xyz`
2. Go to **Production Supabase Dashboard** → Authentication → Users
3. ✅ User appears in production project
4. Go to **Dev Supabase Dashboard** → Authentication → Users
5. ✅ User does NOT appear in dev project

### Verify Payment Keys Separation ✅

**Dev Environment:**
- Check `landing-page/.env.local`: Should have `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...`
- Check `backend/.env`: Should have `STRIPE_SECRET_KEY=sk_test_...`

**Prod Environment:**
- Check Railway backend variables: Should have `STRIPE_SECRET_KEY=sk_live_...`
- Check Vercel frontend variables: Should have `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...`

---

## Common Issues & Fixes

### Issue: Dev redirects to production Supabase
**Symptoms:** User created in production when testing on localhost  
**Fix:** Check `landing-page/.env.local` has dev Supabase URL, restart dev server

### Issue: Production redirects to localhost
**Symptoms:** After OAuth, redirects to `http://localhost:3000`  
**Fix:** Check production Supabase Site URL is `https://lexicraft.xyz` (not localhost)

### Issue: CORS errors in production
**Symptoms:** API calls fail with CORS error  
**Fix:** Check Railway `ALLOWED_ORIGINS` includes `https://lexicraft.xyz`

### Issue: Payment uses test mode in production
**Symptoms:** Payments show in Stripe test mode  
**Fix:** Check Railway/Vercel have live mode keys (`sk_live_`, `pk_live_`)

---

## Success Criteria

✅ **All tests pass:**
- Dev environment uses dev Supabase
- Prod environment uses prod Supabase
- OAuth works in both environments
- API connections work in both environments
- Payment keys separated (test in dev, live in prod)
- No cross-contamination between environments

**Phase 2 Complete!** 🎉

