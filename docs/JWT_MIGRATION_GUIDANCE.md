# JWT Signing Keys Migration Guidance

## Current Status

**Our backend code uses HS256 (symmetric algorithm) with legacy JWT secret.**

```python
# backend/src/middleware/auth.py
payload = jwt.decode(
    token,
    SUPABASE_JWT_SECRET,
    algorithms=["HS256"],  # ← Symmetric algorithm
    ...
)
```

## Should We Migrate?

**❌ NOT YET** - Do not migrate to new JWT signing keys right now.

### Why Not?

1. **Algorithm Mismatch:**
   - **Legacy JWT Secret:** Uses HS256 (symmetric - shared secret)
   - **New JWT Signing Keys:** Use RS256 (asymmetric - public/private key pair)
   - Our code is hardcoded to use HS256

2. **Code Changes Required:**
   - Would need to fetch public key from Supabase JWKS endpoint
   - Change algorithm from `["HS256"]` to `["RS256"]`
   - Update token verification logic
   - Test thoroughly

3. **Timeline:**
   - Legacy JWT secrets work until **late 2026**
   - No urgent need to migrate now
   - Can migrate later when we have time for proper testing

## What to Use Now

**For Development Setup (Phase 2):**

1. **Get Legacy JWT Secret:**
   - Go to Supabase Dashboard → Settings → API
   - Click **"Legacy anon, service_role API keys"** tab
   - Copy **"JWT Secret"** (the long string)
   - Use this for `SUPABASE_JWT_SECRET` in `backend/.env`

2. **Do NOT click "Migrate JWT secret" button** - ignore that banner for now

## When to Migrate

**Plan to migrate when:**
- We have dedicated time for testing
- We can update the code to use RS256
- We can test thoroughly with both dev and prod
- Before late 2026 deadline

## Migration Steps (For Future)

When ready to migrate:

1. **Update Code:**
   ```python
   # Change from HS256 to RS256
   # Fetch public key from Supabase JWKS endpoint
   # Update verification logic
   ```

2. **Migrate in Supabase Dashboard:**
   - Click "Migrate JWT secret" button
   - Follow Supabase's migration guide

3. **Test Thoroughly:**
   - Test authentication flow
   - Test all protected endpoints
   - Test with both dev and prod projects

## References

- [Supabase JWT Signing Keys Docs](https://supabase.com/docs/guides/auth/jwts)
- [JWT Algorithms: HS256 vs RS256](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

