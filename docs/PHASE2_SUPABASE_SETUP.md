# Phase 2: Supabase Environment Separation

**Status:** In Progress  
**Date:** 2025-01-XX

## Overview

Separate Supabase projects for development and production to ensure:
- Dev data doesn't affect production
- Test payments don't mix with real payments
- Safe experimentation without risk to live users

## Architecture

```
Development Environment:
├── Supabase Project: lexicraft-dev
├── Site URL: http://localhost:3000
├── Redirect URLs: http://localhost:3000/**
└── Database: Separate from production

Production Environment:
├── Supabase Project: lexicraft-prod (existing)
├── Site URL: https://lexicraft.xyz
├── Redirect URLs: https://lexicraft.xyz/**
└── Database: Current production database
```

## Step-by-Step Setup

### Step 1: Create Dev Supabase Project

**Manual Action Required:**

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click **"New Project"** (green button in top right)
3. Fill in the project creation form:
   - **Project Name:** `lexicraft-dev`
   - **Database Password:** Generate a strong password (save it! You'll need this for the connection string)
   - **Region:** 
     - **Where to find:** Dropdown menu in the project creation form (appears after entering project name and password)
     - **Recommendation:** Choose the **same region as your production project** (for consistency and lower latency)
     - **To check production region:** 
       1. Go to your existing production project
       2. Click **Settings** (left sidebar)
       3. Click **General** (first item under PROJECT SETTINGS)
       4. Look for **"Region"** in the project information section (usually near the top, shows something like "Southeast Asia (Singapore)" or "West US (North California)")
     - **Available regions:** US (multiple), EU (multiple), Asia Pacific (Singapore, Tokyo, Seoul, etc.), and more
     - **⚠️ Important:** Region **cannot be changed later** - you'd need to create a new project and migrate data
   - **Pricing Plan:** Free tier is fine for development
4. Click **"Create new project"**
5. Wait 2-3 minutes for project to initialize

**After Creation:**
- Note your **Project Reference ID** (e.g., `abcdefghijklmnop`)
- Your dev Supabase URL will be: `https://abcdefghijklmnop.supabase.co`

### Step 2: Configure Dev Project Settings

**In Supabase Dashboard → lexicraft-dev:**

1. **Go to Settings → API**
   - Copy **Project URL**: `https://[DEV_PROJECT_REF].supabase.co`
   - **For Frontend (Client-Side):**
     - **Option A (New - Recommended):** In "Publishable and secret API keys" tab, copy **Publishable key** (starts with `sb_publishable_...`)
     - **Option B (Legacy):** Click "Legacy anon, service_role API keys" tab, copy **anon public key** (starts with `eyJhbGc...`)
     - ⚠️ **Both work!** Use whichever is available. Variable name stays `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **For Backend (Server-Side - only if you need admin operations):**
     - **Option A (New - Recommended):** In "Publishable and secret API keys" tab, copy **Secret key** (starts with `sb_secret_...`)
     - **Option B (Legacy):** Click "Legacy anon, service_role API keys" tab, copy **service_role key** (starts with `eyJhbGc...`)
     - ⚠️ **Note:** Most backend operations use `SUPABASE_JWT_SECRET` (different from API keys). Only needed for admin scripts.
   - See `docs/SUPABASE_API_KEYS_MIGRATION.md` for full details on new vs legacy keys

2. **Go to Authentication → URL Configuration**
   - **Site URL:** `http://localhost:3000`
   - **Redirect URLs:** Add `http://localhost:3000/**`
   - Click **"Save"**

3. **Get Database Connection String**
   - **New Location:** Click the **"Connect"** button (usually in top right of project dashboard, or in Database section)
   - **Or:** Go to **Settings → Database** → Look for **"Connect"** or **"Connection string"** button
   - This opens a **"Connect to your project"** modal
   - In the modal:
     - **Tab:** "Connection String" (should be selected by default)
     - **Type:** Select "URI"
     - **Source:** Select "Primary Database" 
     - **Method:** Select **"Session Pooler"** (port 6543) - recommended for Railway/serverless
       - ⚠️ **Note:** "Direct connection" (port 5432) may show IPv4 compatibility warning
       - Use "Session Pooler" to avoid IPv4 issues on Railway
   - Copy the connection string
   - Format should be: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:6543/postgres?sslmode=require`
   - **Important:** Replace `[YOUR-PASSWORD]` with your actual database password

### Step 3: Run Database Migrations on Dev Project

**Option A: Using Supabase SQL Editor (Recommended)**

1. Go to **SQL Editor** in dev project
2. Click **"New query"**
3. Copy contents of migration files from `backend/migrations/`
4. Run migrations in order (001, 002, 003, etc.)
5. Verify tables are created

**Option B: Using psql (Advanced)**

```bash
# Get connection string from Supabase Dashboard
export DEV_DATABASE_URL="postgresql://postgres:[PASSWORD]@[DEV_PROJECT_REF].supabase.co:6543/postgres?sslmode=require"

# Run migrations
cd backend
for migration in migrations/*.sql; do
  echo "Running $migration..."
  psql "$DEV_DATABASE_URL" -f "$migration"
done
```

### Step 4: Configure Production Supabase Project

**In Supabase Dashboard → lexicraft-prod (your existing project):**

1. **Go to Authentication → URL Configuration**
   - **Site URL:** `https://lexicraft.xyz`
   - **Redirect URLs:** 
     - Remove `http://localhost:3000/**` if present
     - Add `https://lexicraft.xyz/**`
     - Add `https://www.lexicraft.xyz/**` (if using www subdomain)
   - Click **"Save"**

2. **Verify Production Settings**
   - Go to **Settings → API**
   - Verify **Project URL** is correct
   - Note: Don't change production keys unless necessary

### Step 5: Update Local Environment Variables

**Update `landing-page/.env.local`:**

```bash
# Development Supabase (NEW)
NEXT_PUBLIC_SUPABASE_URL=https://[DEV_PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[DEV_ANON_KEY]

# Keep existing for now (will switch to dev)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

**Update `backend/.env`:**

```bash
# Development Database (NEW)
# Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:6543/postgres?sslmode=require
DATABASE_URL=postgresql://postgres:[DEV_PASSWORD]@db.[DEV_PROJECT_REF].supabase.co:6543/postgres?sslmode=require
SUPABASE_JWT_SECRET=[DEV_JWT_SECRET]

# Keep existing Neo4j settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

**Note:** Connection string format changed - now uses `db.[PROJECT_REF].supabase.co` instead of `[PROJECT_REF].supabase.co`

### Step 6: Test Dev Environment

1. **Start Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn src.main:app --reload --port 8000
   ```

2. **Start Frontend:**
   ```bash
   cd landing-page
   npm run dev
   ```

3. **Test Authentication:**
   - Go to `http://localhost:3000/zh-TW/login`
   - Try signing up with a test email
   - Verify user is created in **dev** Supabase project (not production)

4. **Verify Database:**
   - Go to Supabase Dashboard → lexicraft-dev → Table Editor
   - Check that new user appears in `users` table
   - Verify no data in production project

## Verification Checklist

After setup, verify:

- [ ] Dev Supabase project created (`lexicraft-dev`)
- [ ] Dev project Site URL set to `http://localhost:3000`
- [ ] Dev project redirect URLs include `http://localhost:3000/**`
- [ ] Database migrations run on dev project
- [ ] Production project Site URL set to `https://lexicraft.xyz`
- [ ] Production project redirect URLs only include `https://lexicraft.xyz/**` (no localhost)
- [ ] Local `.env.local` uses dev Supabase credentials
- [ ] Local `backend/.env` uses dev database credentials
- [ ] Test signup creates user in dev project (not production)
- [ ] Production site still works correctly

## Troubleshooting

### Issue: "Redirect URI mismatch" in dev

**Solution:** 
- Check dev Supabase → Authentication → URL Configuration
- Ensure `http://localhost:3000/**` is in Redirect URLs
- Ensure Site URL is `http://localhost:3000`

### Issue: User created in production instead of dev

**Solution:**
- Check `landing-page/.env.local` has dev Supabase URL
- Restart Next.js dev server after changing env vars
- Clear browser cookies/localStorage

### Issue: Database connection fails

**Solution:**
- Verify DATABASE_URL uses Transaction mode (port 6543)
- Check password is correct (no extra spaces)
- Verify connection string format matches example

## Next Steps

After Phase 2 is complete:
- Phase 3: Google OAuth Separation (separate OAuth clients)
- Phase 4: Payment Provider Separation (test vs live keys)
- Phase 5: Code Updates (use NEXT_PUBLIC_SITE_URL)

## Reference

- Supabase Dashboard: https://supabase.com/dashboard
- Connection String Guide: https://supabase.com/docs/guides/database/connecting-to-postgres
- Migration Files: `backend/migrations/*.sql`

