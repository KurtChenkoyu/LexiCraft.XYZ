# Supabase API Keys Explained

## Key Types (They Are DIFFERENT!)

| Key Name | Purpose | Where Used | Starts With | Security |
|----------|---------|------------|-------------|----------|
| **Publishable Key** (anon) | Client-side operations | Frontend (browser) | `sb_publishable_...` or `eyJhbGc...` | ✅ Safe to expose |
| **Secret Key** (service_role) | Server-side admin operations | Backend (server) | `sb_secret_...` or `eyJhbGc...` | ❌ Keep secret! |
| **JWT Secret** | Token verification | Backend (server) | Long string (80-200 chars) | ❌ Keep secret! |

## They Should NOT Be The Same!

**✅ Correct Setup:**

**Frontend (`landing-page/.env.local`):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://kaaqoziufmpsmnsqypln.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...  # Publishable key (frontend)
```

**Backend (`backend/.env`):**
```bash
SUPABASE_URL=https://kaaqoziufmpsmnsqypln.supabase.co
SUPABASE_JWT_SECRET=[long JWT secret string]  # JWT secret (for token verification)
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...  # Optional: Only if backend needs admin operations
```

## What Each Key Does

### 1. Publishable Key (NEXT_PUBLIC_SUPABASE_ANON_KEY)
- **Used by:** Frontend (browser)
- **Purpose:** Client-side Supabase operations (auth, queries with RLS)
- **Security:** Safe to expose (it's in the browser anyway)
- **Where to get:** Supabase Dashboard → Settings → API → "Publishable and secret API keys" tab → Publishable key

### 2. Secret Key (SUPABASE_SERVICE_ROLE_KEY)
- **Used by:** Backend (server)
- **Purpose:** Admin operations that bypass Row Level Security (RLS)
- **Security:** Must be kept secret (never expose in frontend)
- **Where to get:** Supabase Dashboard → Settings → API → "Publishable and secret API keys" tab → Secret key
- **Note:** Most backends don't need this - only if you need admin operations

### 3. JWT Secret (SUPABASE_JWT_SECRET)
- **Used by:** Backend (server)
- **Purpose:** Verify JWT tokens from Supabase (authentication)
- **Security:** Must be kept secret
- **Where to get:** Supabase Dashboard → Settings → API → "Legacy anon, service_role API keys" tab → JWT Secret
- **Critical:** Must match the Supabase project that issued the token!

## For Your 401 Error

The issue is likely:

1. **JWT Secret mismatch:**
   - Frontend logs in with **dev Supabase** → gets JWT token signed with **dev JWT secret**
   - Backend tries to verify with **production JWT secret** → fails → 401 error

2. **Solution:**
   - Backend `SUPABASE_JWT_SECRET` must be from **dev Supabase project**
   - Get it from: https://supabase.com/dashboard/project/kaaqoziufmpsmnsqypln/settings/api
   - Legacy tab → JWT Secret

## Quick Checklist

**Frontend (`.env.local`):**
- ✅ `NEXT_PUBLIC_SUPABASE_URL` = dev Supabase URL
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY` = dev publishable key

**Backend (`.env`):**
- ✅ `SUPABASE_URL` = dev Supabase URL (same as frontend)
- ✅ `SUPABASE_JWT_SECRET` = dev JWT secret (from Legacy tab)
- ⚠️ `SUPABASE_SERVICE_ROLE_KEY` = dev secret key (optional, only if needed)

**Important:** All keys must be from the **same Supabase project** (dev)!


