# Railway Environment Variables Setup

## Critical Issue

The backend is currently returning **500 Internal Server Errors** for all authenticated endpoints because two critical environment variables are missing in the Railway deployment:

1. `DATABASE_URL` - PostgreSQL connection string (Supabase)
2. `SUPABASE_JWT_SECRET` - JWT secret for token verification

## Error Messages

From the backend logs:
```
ValueError: PostgreSQL connection string missing. Provide connection_string or set DATABASE_URL environment variable.
WARNING:src.middleware.auth:SUPABASE_JWT_SECRET not set. Decoding without verification.
```

## Required Environment Variables

### 1. DATABASE_URL

**What it is**: PostgreSQL connection string for Supabase database

**How to get it**:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **Database**
4. Under **Connection string**, select **Transaction mode** (port 6543)
5. Copy the connection string (it should look like: `postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?sslmode=require`)

**Format**: 
```
postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:6543/postgres?sslmode=require
```

**Note**: Make sure to use the **Transaction mode** connection string (port 6543), not Session mode (port 5432).

### 2. SUPABASE_JWT_SECRET

**What it is**: JWT secret key used to verify Supabase authentication tokens

**How to get it**:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **API**
4. Under **Project API keys**, find **JWT Secret** (Legacy)
5. Copy the entire secret (it's a long string, usually 80-200 characters)

**Format**: A long base64-encoded string

**Security Note**: This is a sensitive secret. Never commit it to version control.

**About Legacy JWT Secret**:
- ✅ **Yes, Legacy JWT secret works perfectly** with the current backend implementation
- The backend uses `HS256` algorithm which is compatible with the Legacy (symmetric) JWT secret
- This is the correct secret to use for now - no changes needed
- **Future consideration**: Supabase recommends migrating to asymmetric keys (RSA/EC) for better security, but this requires code changes. The Legacy secret is fine for production use and will continue to work.

## How to Set in Railway

### Option 1: Railway Dashboard (Recommended - Updated 2025)

**Step-by-step instructions for the current Railway interface:**

1. **Access Your Railway Project**:
   - Go to [Railway Dashboard](https://railway.app) and log in
   - From your dashboard, select the project containing your backend service

2. **Navigate to the Service's Variables Section**:
   - Within your project, **click on the specific backend service** (not just the project)
   - In the service's menu/sidebar, select the **"Variables"** tab

3. **Add New Environment Variables**:
   - Click on the **"+ New Variable"** button (or "New Variable" button)
   - Enter the variable details:
     - **Name**: `DATABASE_URL`
     - **Value**: Your Supabase connection string (paste the full connection string)
   - Click **Add** or **Save**
   - Repeat this process for `SUPABASE_JWT_SECRET`:
     - Click **"+ New Variable"** again
     - **Name**: `SUPABASE_JWT_SECRET`
     - **Value**: Your JWT secret from Supabase

4. **Deploy the Changes**:
   - After adding the variables, Railway will show a banner indicating that there are **staged changes**
   - Review the staged changes
   - Click the **"Deploy"** button to apply these changes
   - This will redeploy your service with the new environment variables

**Visual Reference**: Railway has a [video tutorial](https://www.youtube.com/watch?v=f91MUenGEkc) on managing environment variables.

**Note**: The variables are staged first, so you must click "Deploy" for them to take effect. The service will automatically redeploy after you deploy the changes.

### Option 2: Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login
railway login

# Link to your project
cd backend
railway link

# Set environment variables
railway variables set DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?sslmode=require"
railway variables set SUPABASE_JWT_SECRET="[YOUR-JWT-SECRET]"
```

## Optional Environment Variables

These are not required for basic functionality but may be needed for specific features:

- `NEO4J_URI`: Neo4j connection URI (if using Neo4j features)
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`: For AI features
- `ANTHROPIC_API_KEY`: For Claude AI features
- `SUPABASE_URL`: Supabase project URL (optional, can use `NEXT_PUBLIC_SUPABASE_URL`)

## Verification

After setting the environment variables and clicking "Deploy":

1. **Wait for Deployment**: Railway will automatically redeploy your service. Wait for the deployment to complete (check the "Deployments" tab)

2. **Check Logs**: 
   - Go to the service's **"Logs"** tab in Railway dashboard
   - Look for successful startup messages
   - Verify there are no errors about missing `DATABASE_URL` or `SUPABASE_JWT_SECRET`

3. **Test Health Endpoint**:
   ```bash
   curl https://lexicraftxyz-production.up.railway.app/health
   ```
   Should return: `{"status":"ok","version":"7.1","service":"LexiCraft Survey API"}`

4. **Test Authenticated Endpoint** (requires valid JWT token from a logged-in user):
   ```bash
   curl -H "Authorization: Bearer [YOUR-JWT-TOKEN]" \
        https://lexicraftxyz-production.up.railway.app/api/v1/profile
   ```
   Should return user profile data instead of a 500 error

## Current Status

✅ **Frontend**: Working correctly, loads instantly (adhering to "snappy" principle)
✅ **Backend Health**: Working (`/health` endpoint returns 200 OK)
❌ **Authenticated Endpoints**: Failing with 500 errors due to missing environment variables

Once the environment variables are set, all authenticated endpoints should work correctly.

