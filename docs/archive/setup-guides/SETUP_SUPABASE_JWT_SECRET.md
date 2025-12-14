# How to Set SUPABASE_JWT_SECRET

## Step 1: Get JWT Secret from Supabase

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Log in to your account

2. **Select Your Project**
   - Click on your project (e.g., "lexicraft-mvp")

3. **Go to Settings → API**
   - In the left sidebar, click **Settings** (gear icon)
   - Click **API** in the settings menu

4. **Find JWT Secret**
   - Scroll down to the **"JWT Settings"** section
   - You'll see:
     - **JWT Secret**: A long string starting with something like `your-super-secret-jwt-token-with-at-least-32-characters-long`
   - Click the **eye icon** or **"Reveal"** button to show the secret
   - **Copy the entire secret** (it's a long string)

---

## Step 2: Set for Local Development

### Option A: Using `.env` file (Recommended)

1. **Create or edit `.env` file** in your `backend` directory:
   ```bash
   cd backend
   touch .env  # If file doesn't exist
   ```

2. **Add the JWT secret**:
   ```bash
   # Supabase JWT Secret (for token verification)
   SUPABASE_JWT_SECRET=your-actual-jwt-secret-here-paste-the-long-string
   
   # Also add other Supabase variables if not already there
   SUPABASE_URL=https://xxxxx.supabase.co
   ```

3. **Verify it's loaded**:
   ```python
   # Test in Python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv("SUPABASE_JWT_SECRET"))  # Should print your secret
   ```

### Option B: Export in Terminal (Temporary)

```bash
export SUPABASE_JWT_SECRET="your-actual-jwt-secret-here"
```

**Note**: This only works for the current terminal session. Use `.env` file for persistence.

---

## Step 3: Set for Production Deployment

### Railway

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Click on your backend service

2. **Go to Variables Tab**
   - Click **Variables** in the left sidebar
   - Or go to **Settings** → **Variables**

3. **Add New Variable**
   - Click **"New Variable"** or **"Add Variable"**
   - **Name**: `SUPABASE_JWT_SECRET`
   - **Value**: Paste your JWT secret
   - Click **"Add"**

4. **Redeploy** (if needed)
   - Railway will automatically redeploy when you add variables
   - Or manually redeploy from the **Deployments** tab

### Render

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Click on your backend service

2. **Go to Environment Tab**
   - Click **Environment** in the left sidebar

3. **Add Environment Variable**
   - Scroll to **"Environment Variables"** section
   - Click **"Add Environment Variable"**
   - **Key**: `SUPABASE_JWT_SECRET`
   - **Value**: Paste your JWT secret
   - Click **"Save Changes"**

4. **Redeploy** (if needed)
   - Render will automatically redeploy
   - Or manually redeploy from the **Manual Deploy** section

### Vercel (if using serverless functions)

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Click on your project

2. **Go to Settings → Environment Variables**
   - Click **Settings** → **Environment Variables**

3. **Add Variable**
   - Click **"Add New"**
   - **Name**: `SUPABASE_JWT_SECRET`
   - **Value**: Paste your JWT secret
   - **Environment**: Select all (Production, Preview, Development)
   - Click **"Save"**

4. **Redeploy**
   - Go to **Deployments** tab
   - Click **"..."** → **"Redeploy"**

---

## Step 4: Verify It's Working

### Test Locally

1. **Start backend**:
   ```bash
   cd backend
   source venv/bin/activate  # If using virtualenv
   uvicorn src.main:app --reload
   ```

2. **Check logs**:
   - If `SUPABASE_JWT_SECRET` is not set, you'll see a warning:
     ```
     UserWarning: SUPABASE_JWT_SECRET not set. Token verification is disabled.
     ```
   - If it's set correctly, no warning should appear

3. **Test with a request**:
   ```bash
   # Get a token from Supabase (via frontend login)
   # Then test:
   curl -X GET http://localhost:8000/api/users/me \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

### Test in Production

1. **Check deployment logs**:
   - Railway/Render: Check service logs
   - Look for the warning message (should NOT appear if secret is set)

2. **Test API endpoint**:
   ```bash
   # With valid token
   curl -X GET https://your-backend-url.com/api/users/me \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

---

## Security Best Practices

### ✅ DO:
- ✅ Store secret in environment variables (never in code)
- ✅ Use different secrets for dev/staging/production if using multiple Supabase projects
- ✅ Keep secret secure and don't commit to git
- ✅ Rotate secret if compromised

### ❌ DON'T:
- ❌ Commit `.env` file to git (add to `.gitignore`)
- ❌ Share secret in chat/email
- ❌ Hardcode secret in Python files
- ❌ Use production secret in development

---

## Troubleshooting

### Issue: "Token verification failed" or "Invalid token"

**Possible causes:**
1. Wrong JWT secret
   - **Fix**: Double-check you copied the entire secret from Supabase
   - Make sure there are no extra spaces or line breaks

2. Secret not loaded
   - **Fix**: 
     - Verify `.env` file is in `backend/` directory
     - Check file is named exactly `.env` (not `.env.txt`)
     - Restart your backend server after adding to `.env`

3. Using wrong Supabase project
   - **Fix**: Ensure JWT secret matches the Supabase project your frontend uses

### Issue: Warning about token verification disabled

**Cause**: `SUPABASE_JWT_SECRET` not set  
**Fix**: Add it to `.env` file or environment variables

### Issue: Secret works locally but not in production

**Cause**: Secret not set in deployment platform  
**Fix**: Add `SUPABASE_JWT_SECRET` to Railway/Render environment variables

---

## Quick Checklist

- [ ] Got JWT secret from Supabase Dashboard → Settings → API
- [ ] Added to `backend/.env` file for local development
- [ ] Added to Railway/Render environment variables for production
- [ ] Verified no warnings in backend logs
- [ ] Tested API endpoint with auth token

---

## Example `.env` File

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long-xxxxx

# Database
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

# Neo4j
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

**Important**: Never commit this file to git! Make sure `.env` is in `.gitignore`.

---

## Need Help?

If you're still having issues:
1. Check Supabase Dashboard → Settings → API → JWT Settings
2. Verify secret is copied completely (no truncation)
3. Check backend logs for error messages
4. Verify environment variable is loaded: `print(os.getenv("SUPABASE_JWT_SECRET"))`

