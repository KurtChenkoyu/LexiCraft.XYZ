# Environment & Branch Strategy

**Last Updated:** 2025-01-XX

## Branch Mapping

This project uses a strict **main/develop** branching strategy to separate development and production environments.

| Branch | Environment | URL | Purpose |
|--------|-------------|-----|---------|
| `main` | **Production** | `https://lexicraft.xyz` | Live code deployed to production. Only merge here when ready for users. |
| `develop` | **Development** | `http://localhost:3000` | Active development branch. All new work happens here. |

## AI Assistant Context

**For Cursor, Gemini, and other AI assistants:**

- **When working on `develop` branch:** Use development environment variables (localhost URLs, test payment keys, dev Supabase project)
- **When working on `main` branch:** Use production environment variables (lexicraft.xyz URLs, live payment keys, prod Supabase project)
- **Always check current branch** before suggesting environment variable changes or URL references

## Environment Variables

### Development (`.env.local`)

- `NEXT_PUBLIC_SITE_URL=http://localhost:3000`
- `NEXT_PUBLIC_SUPABASE_URL=https://dev-project.supabase.co` (dev Supabase project)
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Payment keys: **Test Mode** (`sk_test_...`, `pk_test_...`)

### Production (Railway/Vercel)

- `NEXT_PUBLIC_SITE_URL=https://lexicraft.xyz`
- `NEXT_PUBLIC_SUPABASE_URL=https://prod-project.supabase.co` (prod Supabase project)
- `NEXT_PUBLIC_API_URL=https://api.lexicraft.xyz`
- Payment keys: **Live Mode** (`sk_live_...`, `pk_live_...`)

## Deployment Rules

1. **Railway/Vercel Production Services:** Configured to **only** deploy from `main` branch
2. **Local Development:** Always work on `develop` branch
3. **Release Process:** Merge `develop` → `main` when ready for production

## Quick Reference

- **Current Production:** Check `main` branch
- **Current Development:** Check `develop` branch
- **Which environment am I in?** Check your current git branch and `.env.local` file

