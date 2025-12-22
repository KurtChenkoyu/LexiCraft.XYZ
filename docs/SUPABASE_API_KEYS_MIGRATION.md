# Supabase API Keys: New vs Legacy Structure

**Last Updated:** 2025-01-XX

## Overview

Supabase has updated their API key system. Both old and new keys work, but you should migrate to the new structure for future compatibility.

## Key Changes

| Old Name | New Name | Purpose | Starts With |
|----------|----------|---------|-------------|
| `anon` key | **Publishable key** | Client-side (browser) | `sb_publishable_...` |
| `service_role` key | **Secret key** | Server-side (admin) | `sb_secret_...` |

## Timeline

- **October 1, 2025:** Existing projects automatically migrate to new JWT signing keys
- **November 1, 2025:** New projects won't include legacy keys
- **Late 2026:** All projects required to use new keys

## Current Status

**✅ Both work for now!** Your code will work with either:
- Legacy keys (`anon`, `service_role`) - still supported
- New keys (`publishable`, `secret`) - recommended

## Where to Find Keys

### In Supabase Dashboard → Settings → API

**New Keys (Recommended):**
1. **"Publishable and secret API keys"** tab (default)
2. **Publishable key:** For frontend/client-side (safe to expose)
3. **Secret key:** For backend/server-side (keep secret!)

**Legacy Keys (Still Available):**
1. Click **"Legacy anon, service_role API keys"** tab
2. **anon key:** For frontend (old name)
3. **service_role key:** For backend (old name)

## Code Compatibility

Our codebase supports both:

**Frontend (`landing-page/.env.local`):**
```bash
# Both work - use whichever you have
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...  # New (recommended)
# OR
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...          # Legacy (still works)
```

**Backend (`backend/.env`):**
```bash
# For server-side operations (if needed)
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...           # New (recommended)
# OR
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...              # Legacy (still works)
```

**Note:** Variable names stay the same (`NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) - just use the new key values.

## Migration Recommendation

**For Phase 2 Setup (Now):**
- Use **new keys** (publishable/secret) if available
- If you only see legacy keys, that's fine - they still work
- Both dev and prod projects can use different key types

**For Future:**
- Plan to migrate all projects to new keys by late 2026
- New projects created after Nov 2025 will only have new keys

## Security Notes

- **Publishable/Anon Key:** Safe to expose in client code (browser)
- **Secret/Service Role Key:** NEVER expose in client code - server-side only
- Both key types respect Row Level Security (RLS) policies

## References

- [Supabase API Keys Documentation](https://supabase.com/docs/guides/api/api-keys)
- [JWT Signing Keys Migration](https://dev.to/supabase/introducing-jwt-signing-keys-4h3g)

