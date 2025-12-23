# Phase 2: Production Supabase Configuration Checklist

**Manual Action Required** - Complete this in Supabase Dashboard

## Step 1: Configure Production Supabase URL Settings

**In Supabase Dashboard → Production Project (lexicraft-prod):**

1. **Go to Authentication → URL Configuration**
   - **Site URL:** Set to `https://lexicraft.xyz`
   - **Redirect URLs:** 
     - ✅ Add: `https://lexicraft.xyz/**`
     - ✅ Add: `https://www.lexicraft.xyz/**` (if using www subdomain)
     - ❌ Remove: `http://localhost:3000/**` (if present - this should only be in dev)
   - Click **"Save"**

**Why this matters:**
- Site URL is used as fallback redirect destination
- If it's set to localhost, production users will be redirected to localhost (broken!)
- Redirect URLs must include your production domain for OAuth to work

## Step 2: Verify Production API Settings

**In Supabase Dashboard → Production Project:**

1. **Go to Settings → API**
   - Verify **Project URL** is correct: `https://[PROD_PROJECT_REF].supabase.co`
   - Note: Don't change production API keys unless necessary
   - Production keys are already configured in Railway/Vercel

## Step 3: Verify Database Connection

**Production database connection string:**
- Already configured in Railway backend environment variables
- Uses production Supabase project
- Connection string format: `postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres`

## Verification

After completing these steps:
- ✅ Production Site URL: `https://lexicraft.xyz`
- ✅ Production Redirect URLs: Only production domains (no localhost)
- ✅ Dev Site URL: `http://localhost:3000` (separate project)
- ✅ Dev Redirect URLs: Only localhost (separate project)

## Next Steps

After completing this checklist:
1. Continue with Google OAuth setup (dev + prod)
2. Update code to use environment variables
3. Configure Railway environment variables

