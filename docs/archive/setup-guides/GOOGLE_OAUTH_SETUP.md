# Google OAuth Setup for Supabase

**Status:** 🟡 **Setup Required**

---

## Step-by-Step Guide

### Step 1: Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Sign in with your Google account

2. **Create or Select a Project**
   - Click the project dropdown at the top
   - Click **"New Project"** (or select existing)
   - Name: `LexiCraft` or `lexicraft-mvp`
   - Click **"Create"**

3. **Enable Google+ API**
   - In the left sidebar, go to **"APIs & Services"** → **"Library"**
   - Search for **"Google+ API"** (or "Google Identity")
   - Click on it and click **"Enable"**

4. **Create OAuth 2.0 Credentials**
   - Go to **"APIs & Services"** → **"Credentials"**
   - Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
   - If prompted, configure OAuth consent screen first:
     - **User Type**: External (unless you have Google Workspace)
     - **App name**: `LexiCraft`
     - **User support email**: Your email
     - **Developer contact**: Your email
     - Click **"Save and Continue"**
     - Scopes: Click **"Save and Continue"** (default is fine)
     - Test users: Add your email, click **"Save and Continue"**
     - Click **"Back to Dashboard"**

5. **Create OAuth Client ID**
   - Application type: **"Web application"**
   - Name: `LexiCraft Web`
   - **Authorized redirect URIs**: Add this (you'll get your Supabase URL first):
     ```
     https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback
     ```
     - Replace `YOUR_PROJECT_REF` with your Supabase project reference ID
     - Example: `https://abcdefghijklmnop.supabase.co/auth/v1/callback`
   - Click **"Create"**

6. **Copy Credentials**
   - You'll see a popup with:
     - **Client ID**: `123456789-abcdefghijklmnop.apps.googleusercontent.com`
     - **Client Secret**: `GOCSPX-abcdefghijklmnop`
   - **Copy both** (you'll need them for Supabase)

---

### Step 2: Get Your Supabase Project URL

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project: **lexicraft-mvp**

2. **Get Project Reference ID**
   - Go to **Settings** → **General**
   - Find **"Reference ID"** (looks like: `abcdefghijklmnop`)
   - Your Supabase URL is: `https://abcdefghijklmnop.supabase.co`

3. **Add Redirect URI to Google**
   - Go back to Google Cloud Console → Credentials
   - Edit your OAuth 2.0 Client ID
   - Add this redirect URI:
     ```
     https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback
     ```
   - Replace `YOUR_PROJECT_REF` with your actual Supabase reference ID
   - Click **"Save"**

---

### Step 3: Configure Google in Supabase

1. **Go to Supabase Authentication**
   - In Supabase dashboard, go to **Authentication** → **Providers**

2. **Enable Google Provider**
   - Find **"Google"** in the list
   - Click **"Enable"** or toggle it on

3. **Add Credentials**
   - **Client ID (for OAuth)**: Paste your Google Client ID
   - **Client Secret (for OAuth)**: Paste your Google Client Secret
   - Click **"Save"**

---

### Step 4: Test Google Sign-In

1. **Visit your login page**
   - Go to: `https://lexicraft-landing.vercel.app/zh-TW/login`

2. **Click "使用 Google 登入"**
   - Should redirect to Google OAuth consent screen
   - Select your Google account
   - Grant permissions
   - Should redirect back to your dashboard

---

## Troubleshooting

### "Redirect URI mismatch"
- ✅ Check redirect URI in Google Cloud Console matches exactly:
  ```
  https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback
  ```
- ✅ Make sure no trailing slashes
- ✅ Verify project reference ID is correct

### "Invalid client"
- ✅ Check Client ID and Secret are correct in Supabase
- ✅ Make sure you copied the full values (no extra spaces)

### OAuth consent screen issues
- ✅ Make sure you completed the OAuth consent screen setup
- ✅ Add your email as a test user if in testing mode

---

## Quick Checklist

- [ ] Google Cloud project created
- [ ] Google+ API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth 2.0 Client ID created (Web application)
- [ ] Redirect URI added to Google: `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`
- [ ] Client ID and Secret copied
- [ ] Google provider enabled in Supabase
- [ ] Credentials added to Supabase
- [ ] Tested Google sign-in

---

**Status:** Ready to configure! Follow the steps above.

