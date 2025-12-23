# Phase 2: Dev Environment 401 Error Fix

## Problem

After logging in with dev Supabase, all API calls return **401 Unauthorized**.

**Symptoms:**
- Login works (Supabase auth succeeds)
- All backend API calls fail with 401
- Console shows: "Authentication failed (401) in API client"

## Root Cause

**Mismatch between frontend and backend Supabase projects:**

- **Frontend:** Using **dev Supabase** (`kaaqoziufmpsmnsqypln`)
- **Backend:** Using **production Supabase JWT secret** (can't verify dev tokens)

When you log in with dev Supabase, the JWT token is signed with the **dev JWT secret**. But if the backend has the **production JWT secret**, it can't verify the token → 401 error.

## Solution

Update backend to use **dev Supabase JWT secret**.

### Step 1: Get Dev Supabase JWT Secret

1. Go to **Dev Supabase Dashboard:**
   - https://supabase.com/dashboard/project/kaaqoziufmpsmnsqypln/settings/api

2. Click **"Legacy anon, service_role API keys"** tab

3. Copy **"JWT Secret"** (the long string, usually 80-200 characters)

### Step 2: Update Backend `.env`

**Edit `backend/.env`:**

```bash
# Dev Supabase (should match frontend)
SUPABASE_URL=https://kaaqoziufmpsmnsqypln.supabase.co
SUPABASE_JWT_SECRET=[paste dev JWT secret here]

# Dev Database (already set)
DATABASE_URL=postgresql://postgres.kaaqoziufmpsmnsqypln:...
```

### Step 3: Restart Backend

```bash
# Stop backend (Ctrl+C if running)
cd backend
uvicorn src.main:app --reload
```

### Step 4: Clear Browser Cache (Optional)

The old data you're seeing is from IndexedDB cache (from production). To start fresh:

1. Open DevTools (F12)
2. Go to **Application** tab
3. Click **"Clear storage"** → **"Clear site data"**
4. Refresh the page

Or manually clear IndexedDB:
- DevTools → Application → IndexedDB → Delete databases

## Verification

After fixing:

1. **Login again** (will create new session with dev Supabase)
2. **Check console** - should see successful API calls (200 status)
3. **Verify data** - should see data from **dev Supabase** (not production)

## Why This Happens

- **JWT tokens are project-specific:** Each Supabase project has its own JWT secret
- **Tokens can't be verified cross-project:** Dev tokens can't be verified with prod secret
- **Environment separation:** Dev and prod must use matching Supabase projects

## Prevention

Always ensure:
- ✅ Frontend `.env.local` → Dev Supabase URL + Key
- ✅ Backend `.env` → Dev Supabase URL + JWT Secret
- ✅ Both point to the **same** Supabase project

