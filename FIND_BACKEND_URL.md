# How to Find Your Backend URL

## Quick Check: Test Common URLs

First, let's test if your backend is already deployed:

### Option 1: Test Custom Domain (if set up)
```bash
curl https://api.lexicraft.xyz/health
```

If this works, your backend URL is: `https://api.lexicraft.xyz`

### Option 2: Check Railway (if deployed there)
1. Go to [Railway Dashboard](https://railway.app)
2. Log in with your account
3. Look for a project/service named "lexicraft" or "lexicraft-api"
4. Click on it
5. Go to **Settings** → **Networking** or **Domains**
6. You'll see a URL like: `https://your-app.railway.app`
7. Test it: `curl https://your-app.railway.app/health`

If this works, your backend URL is: `https://your-app.railway.app`

### Option 3: Check Render (if deployed there)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Log in with your account
3. Look for a service named "lexicraft-api"
4. Click on it
5. You'll see a URL in the top: `https://your-app.onrender.com`
6. Test it: `curl https://your-app.onrender.com/health`

If this works, your backend URL is: `https://your-app.onrender.com`

## If Backend is NOT Deployed Yet

You have two options:

### Option A: Deploy Backend Now (Recommended)

#### Using Railway (Easier):
1. Go to [Railway](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect it's a Python app
5. Add environment variables:
   - `DATABASE_URL` (from Supabase)
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` (from Neo4j)
6. Railway will give you a URL like: `https://your-app.railway.app`
7. Use this as your `NEXT_PUBLIC_API_URL`

#### Using Render:
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   - **Name**: `lexicraft-api`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Render will give you a URL like: `https://your-app.onrender.com`
7. Use this as your `NEXT_PUBLIC_API_URL`

### Option B: Use Localhost for Testing (Development Only)

**⚠️ This only works for local development, not production!**

For now, you can test locally:
1. Make sure backend is running: `cd backend && uvicorn src.main:app --port 8000`
2. In Vercel, set `NEXT_PUBLIC_API_URL` to your local machine's public IP (not recommended)
3. Or use a tunneling service like ngrok: `ngrok http 8000` → use the ngrok URL

## Once You Have the Backend URL

1. **Update Vercel Environment Variable**:
   - Go to Vercel → Your Project → Settings → Environment Variables
   - Edit `NEXT_PUBLIC_API_URL`
   - Set it to your backend URL (e.g., `https://api.lexicraft.xyz` or `https://your-app.railway.app`)
   - **Important**: No trailing slash, no `/api/v1/survey` path

2. **Redeploy**:
   - Vercel will auto-deploy, or manually redeploy

3. **Test**:
   - Visit your survey page
   - Check browser console - should see the correct API URL
   - Survey should work!

## Quick Test Script

Run this to test common backend URLs:

```bash
# Test custom domain
echo "Testing api.lexicraft.xyz..."
curl -s https://api.lexicraft.xyz/health || echo "❌ Not accessible"

# If you have Railway URL, test it:
# curl -s https://your-app.railway.app/health

# If you have Render URL, test it:
# curl -s https://your-app.onrender.com/health
```

## What to Do Right Now

1. **First**: Check if `https://api.lexicraft.xyz/health` works
   - If yes → Use `https://api.lexicraft.xyz` as your backend URL
   
2. **If not**: Check Railway or Render dashboards for your backend service
   - Find the service URL
   - Test it with `/health` endpoint
   - Use that URL

3. **If backend doesn't exist**: Deploy it to Railway or Render (see Option A above)

4. **Update Vercel**: Set `NEXT_PUBLIC_API_URL` to your backend URL

5. **Redeploy and test**

Let me know what you find!

