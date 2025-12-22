# Phase 2: Supabase Setup - Quick Action Checklist

**Estimated Time:** 15-20 minutes

## ✅ What's Automated

- ✅ Migration script created (`backend/scripts/setup_dev_supabase.sh`)
- ✅ Documentation complete (`docs/PHASE2_SUPABASE_SETUP.md`)
- ✅ Migration order documented (`backend/migrations/README.md`)

## 📋 Manual Steps Required

### 1. Create Dev Supabase Project (5 min)

- [ ] Go to https://supabase.com/dashboard
- [ ] Click "New Project"
- [ ] Name: `lexicraft-dev`
- [ ] Set database password (save it!)
- [ ] Choose region (same as production)
- [ ] Wait for project to initialize
- [ ] Copy Project Reference ID: `_________________`

### 2. Configure Dev Project (3 min)

- [ ] Settings → API: Copy Project URL and anon key
- [ ] Authentication → URL Configuration:
  - [ ] Site URL: `http://localhost:3000`
  - [ ] Add Redirect URL: `http://localhost:3000/**`
  - [ ] Save
- [ ] Settings → Database: Copy connection string (Transaction mode, port 6543)

### 3. Run Migrations on Dev (5 min)

**Option A: Use Script (Easiest)**
```bash
cd backend
export DEV_DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:6543/postgres?sslmode=require"
./scripts/setup_dev_supabase.sh
```

**Option B: Use Supabase SQL Editor**
- [ ] Go to SQL Editor
- [ ] Run migrations from `backend/migrations/` in order
- [ ] Verify tables created in Table Editor

### 4. Configure Production Project (2 min)

- [ ] Go to existing production Supabase project
- [ ] Authentication → URL Configuration:
  - [ ] Site URL: `https://lexicraft.xyz`
  - [ ] Remove `http://localhost:3000/**` if present
  - [ ] Add `https://lexicraft.xyz/**`
  - [ ] Save

### 5. Update Local Environment Files (3 min)

**Update `landing-page/.env.local`:**
```bash
# Dev Supabase (NEW)
NEXT_PUBLIC_SUPABASE_URL=https://[DEV_PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[DEV_ANON_KEY]
```

**Update `backend/.env`:**
```bash
# Dev Database (NEW)
DATABASE_URL=postgresql://postgres:[DEV_PASSWORD]@[DEV_PROJECT_REF].supabase.co:6543/postgres?sslmode=require
SUPABASE_JWT_SECRET=[DEV_JWT_SECRET]
```

### 6. Test Dev Environment (2 min)

- [ ] Start backend: `cd backend && uvicorn src.main:app --reload`
- [ ] Start frontend: `cd landing-page && npm run dev`
- [ ] Go to `http://localhost:3000/zh-TW/login`
- [ ] Sign up with test email
- [ ] Verify user appears in **dev** Supabase (not production)

## 🎯 Success Criteria

- [ ] Can sign up in dev environment
- [ ] User created in dev Supabase project
- [ ] No data in production Supabase
- [ ] Production site still works (verify after Railway redeploy)

## 📚 Full Documentation

See `docs/PHASE2_SUPABASE_SETUP.md` for detailed instructions and troubleshooting.

## ➡️ Next Steps

After Phase 2:
- Phase 3: Google OAuth Separation
- Phase 4: Payment Provider Separation
- Phase 5: Code Updates

