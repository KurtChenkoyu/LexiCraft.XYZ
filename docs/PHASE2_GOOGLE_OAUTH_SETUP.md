# Phase 2: Google OAuth Setup (Dev & Prod)

## Overview

Separate Google OAuth clients for development and production to ensure:
- Dev OAuth only works with localhost (safe testing)
- Prod OAuth only works with production domain (secure)
- No cross-contamination between environments

## Architecture

```
Development Environment:
├── Google OAuth Client: lexicraft-dev
├── Authorized Redirect URIs:
│   └── https://[DEV_SUPABASE_REF].supabase.co/auth/v1/callback
│       (Supabase handles all redirects - no wildcards needed)
└── Used by: Dev Supabase project

Production Environment:
├── Google OAuth Client: lexicraft-prod
├── Authorized Redirect URIs:
│   └── https://[PROD_SUPABASE_REF].supabase.co/auth/v1/callback
│       (Supabase handles all redirects - no wildcards needed)
└── Used by: Production Supabase project
```

**Important:** Google OAuth doesn't allow wildcards (`*`) in redirect URIs. Supabase handles all frontend redirects, so you only need to add the Supabase callback URL.

## Step 1: Create Dev Google OAuth Client

**In Google Cloud Console:**

1. **Go to [Google Cloud Console](https://console.cloud.google.com)**
2. **Select or create a project:**
   - Use existing project or create new one (e.g., "LexiCraft")
3. **Enable Google+ API:**
   - Go to **APIs & Services** → **Library**
   - Search for "Google+ API" or "Google Identity"
   - Click **Enable**
4. **Create OAuth 2.0 Client ID:**
   - Go to **APIs & Services** → **Credentials**
   - Click **+ CREATE CREDENTIALS** → **OAuth client ID**
   - If prompted, configure OAuth consent screen first:
     - **User Type:** External (unless you have Google Workspace)
     - **App name:** LexiCraft Dev
     - **Support email:** Your email
     - **Developer contact:** Your email
     - Click **Save and Continue** through scopes and test users
   - **Application type:** Web application
   - **Name:** `lexicraft-dev` (or `LexiCraft Development`)
   - **Authorized JavaScript origins:**
     - `http://localhost:3000`
   - **Authorized redirect URIs:**
     - `https://[DEV_SUPABASE_REF].supabase.co/auth/v1/callback`
       - Replace `[DEV_SUPABASE_REF]` with your dev Supabase project reference
       - Example: `https://kaaqoziufmpsmnsqypln.supabase.co/auth/v1/callback`
       - ⚠️ **Note:** Google OAuth doesn't allow wildcards. Only add the Supabase callback URL here.
       - The frontend redirects are handled by Supabase, not directly by Google.
   - Click **Create**
5. **Copy credentials:**
   - **Client ID:** Copy this (starts with something like `123456789-abc...`)
   - **Client Secret:** Copy this (starts with `GOCSPX-...`)
   - ⚠️ **Save these securely** - you'll need them for Supabase

## Step 2: Configure Dev OAuth in Supabase

**In Supabase Dashboard → lexicraft-dev:**

1. **Go to Authentication → Providers**
2. **Find Google and click "Enable"**
3. **Enter OAuth credentials:**
   - **Client ID (for OAuth):** Paste the Client ID from Google Cloud Console
   - **Client Secret (for OAuth):** Paste the Client Secret from Google Cloud Console
4. **Click "Save"**

**Verify:**
- Google provider should show as "Enabled" with green checkmark
- Test by trying to sign in with Google on `http://localhost:3000`

## Step 3: Create/Update Production Google OAuth Client

**In Google Cloud Console:**

1. **Go to same Google Cloud project** (or create separate one for prod)
2. **Create another OAuth 2.0 Client ID:**
   - **Application type:** Web application
   - **Name:** `lexicraft-prod` (or `LexiCraft Production`)
   - **Authorized JavaScript origins:**
     - `https://lexicraft.xyz`
     - `https://www.lexicraft.xyz` (if using www subdomain)
   - **Authorized redirect URIs:**
     - `https://[PROD_SUPABASE_REF].supabase.co/auth/v1/callback`
       - Replace `[PROD_SUPABASE_REF]` with your production Supabase project reference
       - Example: `https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback`
       - ⚠️ **Note:** Google OAuth doesn't allow wildcards. Only add the Supabase callback URL here.
       - The frontend redirects are handled by Supabase, not directly by Google.
   - Click **Create**
3. **Copy credentials:**
   - **Client ID:** Copy this
   - **Client Secret:** Copy this
   - ⚠️ **Save these securely**

## Step 4: Configure Production OAuth in Supabase

**In Supabase Dashboard → Production Project (lexicraft-prod):**

1. **Go to Authentication → Providers**
2. **Find Google and click "Enable"** (or "Edit" if already enabled)
3. **Enter OAuth credentials:**
   - **Client ID (for OAuth):** Paste the Production Client ID
   - **Client Secret (for OAuth):** Paste the Production Client Secret
4. **Click "Save"**

**Verify:**
- Google provider should show as "Enabled"
- Test by trying to sign in with Google on `https://lexicraft.xyz`

## Security Notes

- **Never mix dev and prod OAuth clients:**
  - Dev client should ONLY have localhost redirects
  - Prod client should ONLY have production domain redirects
- **Keep secrets secure:**
  - OAuth secrets are stored in Supabase (not in your code)
  - Don't commit secrets to git
- **Test thoroughly:**
  - Test dev OAuth on localhost
  - Test prod OAuth on production domain
  - Verify redirects work correctly

## Troubleshooting

**Issue: "redirect_uri_mismatch" error**
- **Cause:** Redirect URI in Google Console doesn't match what Supabase is sending
- **Fix:** Verify redirect URI in Google Console matches exactly:
  - `https://[SUPABASE_REF].supabase.co/auth/v1/callback`
  - Check for typos, missing `https://`, wrong project reference
  - ⚠️ **No wildcards:** Google doesn't allow `*` in redirect URIs
  - Only add the exact Supabase callback URL (no frontend URLs needed)

**Issue: OAuth works in dev but not prod (or vice versa)**
- **Cause:** Using wrong OAuth client for the environment
- **Fix:** Verify Supabase project is using the correct OAuth client:
  - Dev Supabase → Dev OAuth client
  - Prod Supabase → Prod OAuth client

**Issue: "Access blocked: This app's request is invalid"**
- **Cause:** OAuth consent screen not configured or app in testing mode
- **Fix:** 
  - Configure OAuth consent screen in Google Cloud Console
  - Add test users if app is in testing mode
  - Or publish app (for production use)

## Next Steps

After completing OAuth setup:
1. Test authentication flow in both environments
2. Continue with payment keys separation
3. Configure Railway environment variables

