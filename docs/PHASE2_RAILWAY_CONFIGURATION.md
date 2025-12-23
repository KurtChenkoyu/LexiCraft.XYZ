# Phase 2: Railway Environment Variables Configuration

## Overview

Configure Railway environment variables for production deployments to ensure:
- Production uses production Supabase, payment keys, and OAuth
- Environment-aware configuration (no hardcoded values)
- Secure key management (keys in Railway, not in code)

## Backend Railway Configuration

### Required Environment Variables

**In Railway Dashboard → Backend Service → Variables:**

```bash
# Database (Production Supabase)
DATABASE_URL=postgresql://postgres.[PROD_PROJECT_REF]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres

# Supabase (Production)
SUPABASE_URL=https://[PROD_PROJECT_REF].supabase.co
SUPABASE_JWT_SECRET=[PROD_JWT_SECRET]  # Legacy JWT secret from prod Supabase

# CORS (Production domains only)
ALLOWED_ORIGINS=https://lexicraft.xyz,https://www.lexicraft.xyz

# Stripe (Live Mode - Production)
STRIPE_SECRET_KEY=sk_live_...

# Neo4j (if used)
NEO4J_URI=bolt://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Other backend config
PORT=8000  # Usually set automatically by Railway
```

### How to Set in Railway

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Select your backend service

2. **Open Variables Tab**
   - Click on your service
   - Go to **Variables** tab

3. **Add Each Variable**
   - Click **+ New Variable**
   - Enter variable name (e.g., `DATABASE_URL`)
   - Enter variable value
   - Click **Add**

4. **Verify All Variables**
   - Check that all required variables are set
   - Verify no test mode keys in production

## Frontend Railway/Vercel Configuration

### Required Environment Variables

**In Vercel Dashboard → Project → Settings → Environment Variables:**

```bash
# Site URL (Production)
NEXT_PUBLIC_SITE_URL=https://lexicraft.xyz

# Supabase (Production)
NEXT_PUBLIC_SUPABASE_URL=https://[PROD_PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[PROD_ANON_KEY]  # Publishable key from prod Supabase

# API URL (Backend)
NEXT_PUBLIC_API_URL=https://[BACKEND_RAILWAY_URL].railway.app

# Stripe (Live Mode - Production)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### How to Set in Vercel

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Select your project

2. **Open Environment Variables**
   - Go to **Settings** → **Environment Variables**

3. **Add Each Variable**
   - Enter variable name
   - Enter variable value
   - Select environments (Production, Preview, Development)
   - Click **Save**

4. **Redeploy**
   - After adding variables, trigger a new deployment
   - Or wait for next automatic deployment

## Environment-Specific Values

### Development (Local `.env` files)

```bash
# Backend (.env)
DATABASE_URL=postgresql://postgres.[DEV_PROJECT_REF]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[DEV_PROJECT_REF].supabase.co
SUPABASE_JWT_SECRET=[DEV_JWT_SECRET]
ALLOWED_ORIGINS=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_...

# Frontend (.env.local)
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_SUPABASE_URL=https://[DEV_PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[DEV_ANON_KEY]
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Production (Railway/Vercel)

```bash
# Backend (Railway)
DATABASE_URL=postgresql://postgres.[PROD_PROJECT_REF]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[PROD_PROJECT_REF].supabase.co
SUPABASE_JWT_SECRET=[PROD_JWT_SECRET]
ALLOWED_ORIGINS=https://lexicraft.xyz,https://www.lexicraft.xyz
STRIPE_SECRET_KEY=sk_live_...

# Frontend (Vercel)
NEXT_PUBLIC_SITE_URL=https://lexicraft.xyz
NEXT_PUBLIC_SUPABASE_URL=https://[PROD_PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[PROD_ANON_KEY]
NEXT_PUBLIC_API_URL=https://[BACKEND_RAILWAY_URL].railway.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## Verification Checklist

After configuring Railway/Vercel:

- [ ] All backend variables set in Railway
- [ ] All frontend variables set in Vercel
- [ ] Production uses production Supabase project
- [ ] Production uses live mode payment keys
- [ ] CORS allows only production domains
- [ ] Site URL points to production domain
- [ ] API URL points to Railway backend
- [ ] No test mode keys in production
- [ ] No localhost URLs in production

## Testing Production Configuration

1. **Deploy to Railway/Vercel**
   - Push to `main` branch (triggers deployment)
   - Or manually trigger deployment

2. **Verify Environment Variables**
   - Check Railway/Vercel logs for any missing variable errors
   - Verify variables are loaded correctly

3. **Test Production Site**
   - Visit `https://lexicraft.xyz`
   - Test authentication (should use prod Supabase)
   - Test payment flow (should use live Stripe)
   - Verify API calls work (should hit Railway backend)

## Troubleshooting

**Issue: "Environment variable not found"**
- **Fix:** Verify variable name matches exactly (case-sensitive)
- Check Railway/Vercel dashboard for typos

**Issue: "CORS error"**
- **Fix:** Verify `ALLOWED_ORIGINS` includes production domain
- Check frontend is using correct `NEXT_PUBLIC_API_URL`

**Issue: "Database connection failed"**
- **Fix:** Verify `DATABASE_URL` uses production Supabase
- Check connection string format (Session Pooler)

**Issue: "Payment test mode"**
- **Fix:** Verify Stripe keys are live mode (`sk_live_`, `pk_live_`)
- Check Railway/Vercel variables, not local `.env` files

## Next Steps

After completing Railway configuration:
1. Test complete production environment
2. Verify all features work in production
3. Monitor logs for any configuration issues

