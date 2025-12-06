# Fix: Next.js Module Resolution Error

## Error
```
Error: Cannot find module './vendor-chunks/@supabase.js'
```

## Cause
This is a Next.js build cache issue. The `.next` cache can become corrupted or out of sync with dependencies.

## Solution

### Step 1: Clear Next.js Cache
```bash
cd landing-page
rm -rf .next
rm -rf node_modules/.cache
```

### Step 2: Reinstall Dependencies (if needed)
```bash
npm install
```

### Step 3: Restart Dev Server
```bash
npm run dev
```

## Alternative: Full Clean Rebuild

If the above doesn't work:

```bash
cd landing-page

# Remove all caches
rm -rf .next
rm -rf node_modules/.cache
rm -rf .turbo  # If using Turbopack

# Reinstall dependencies
rm -rf node_modules
npm install

# Restart dev server
npm run dev
```

## Why This Happens

1. **Dependency updates**: When Supabase packages are updated, Next.js cache can become stale
2. **Build cache corruption**: Sometimes the `.next` folder gets corrupted
3. **Module resolution**: Next.js uses vendor chunks for optimization, and these can get out of sync

## Prevention

- Clear `.next` folder when:
  - Updating dependencies
  - Seeing module resolution errors
  - Switching branches with different dependencies
  - After major code changes

## Quick Fix Command

```bash
cd landing-page && rm -rf .next && npm run dev
```

This clears the cache and restarts the server in one command.

