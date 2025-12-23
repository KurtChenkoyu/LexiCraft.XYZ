# Supabase Connection Methods: Session Pooler vs Direct Connection

## Overview

Supabase offers two connection methods. Choose based on your environment and needs.

## Connection Methods Comparison

| Feature | **Session Pooler** (Port 6543) | **Direct Connection** (Port 5432) |
|---------|-------------------------------|-----------------------------------|
| **IPv4 Support** | ✅ Yes (works everywhere) | ❌ IPv6 only (requires IPv6 support) |
| **IPv6 Support** | ✅ Yes | ✅ Yes |
| **Best For** | Railway, Vercel, serverless, IPv4 networks | VMs, containers, IPv6 networks |
| **Connection Limit** | Managed by pooler | Direct to database (higher limit) |
| **Latency** | Slightly higher (pooler overhead) | Lower (direct connection) |
| **Our Code** | ✅ Configured for this | ⚠️ Would need code changes |

## When to Use Each

### Use Session Pooler (Port 6543) - Recommended

**Use when:**
- Deploying to Railway, Vercel, or other cloud platforms
- Your network only supports IPv4
- You're unsure which to use (safer default)
- Running serverless functions
- You see "Not IPv4 compatible" warning

**Why:** Works everywhere, no network compatibility issues.

### Use Direct Connection (Port 5432) - Advanced

**Use when:**
- Running on a VM or long-running container
- Your network fully supports IPv6
- You need the lowest possible latency
- You have Railway IPv4 add-on enabled
- You're doing local development with IPv6

**Why:** Slightly faster, but requires IPv6 or add-on.

## For Local Development

**You can use either!**

- **Session Pooler (6543):** Works on any network, matches production setup
- **Direct (5432):** Faster if your Mac/network supports IPv6

**Recommendation:** Use Session Pooler to match production environment.

## For Railway/Production

**Must use Session Pooler (6543)** unless:
- You've enabled Railway's IPv4 add-on
- Your Railway service supports IPv6 (varies by region)

**Why:** Railway's default networking is IPv4, and Direct connection requires IPv6.

## Our Code Configuration

Our backend code (`backend/src/database/postgres_connection.py`) is configured for:
- **Session Pooler (port 6543)**
- **Transaction mode** (not Session mode)
- **NullPool** (Supabase handles pooling)

If you want to use Direct connection, you'd need to:
1. Change port from 6543 to 5432
2. Ensure IPv6 support or Railway IPv4 add-on
3. Test thoroughly

## Quick Decision Guide

```
Are you deploying to Railway/Vercel?
├─ YES → Use Session Pooler (6543) ✅
└─ NO → Are you on IPv6 network?
    ├─ YES → Can use Direct (5432) or Pooler (6543)
    └─ NO → Use Session Pooler (6543) ✅
```

## Summary

**For this project:** Use **Session Pooler (port 6543)** because:
1. ✅ Works on Railway (IPv4)
2. ✅ Works locally (IPv4)
3. ✅ Code is already configured for it
4. ✅ No network compatibility issues
5. ✅ Matches production setup

**Direct connection is fine for local dev** if you have IPv6, but Session Pooler is the safer, more compatible choice.

