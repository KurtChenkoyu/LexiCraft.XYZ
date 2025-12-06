# Fix: Survey API 405 Error - Missing NEXT_PUBLIC_API_URL

## Problem
The survey is failing with `405 Method Not Allowed` because:
1. `NEXT_PUBLIC_API_URL` is not set in Vercel
2. The request is trying to go to `localhost:8000` which doesn't work in production
3. The request is being made to the frontend domain instead of the backend

## Solution: Set Environment Variable in Vercel

### Step 1: Go to Vercel Dashboard
1. Visit: https://vercel.com/dashboard
2. Click on your project: **lexicraft-landing** (or your project name)

### Step 2: Add Environment Variable
1. Go to **Settings** → **Environment Variables**
2. Click **"Add New"**

### Step 3: Add NEXT_PUBLIC_API_URL
```
Name: NEXT_PUBLIC_API_URL
Value: https://api.lexicraft.xyz  (or your actual backend URL)
Environment: Production, Preview, Development (select all)
```

**Important**: 
- Do NOT include `/api/v1/survey` in the URL - that's added by the code
- Do NOT include a trailing slash
- Use `https://` (not `http://`) for production

### Step 4: Redeploy
After adding the variable:
1. Go to **Deployments** tab
2. Click **"..."** on the latest deployment
3. Click **"Redeploy"**
4. Or push a new commit (auto-deploys)

## Verify It's Working

After redeploying, check:
1. The error screen should show the correct API URL (not localhost)
2. Browser console should show the correct API URL in logs
3. Network tab should show requests going to your backend URL

## What Your Backend URL Should Be

If your backend is deployed on:
- **Railway**: `https://your-app.railway.app`
- **Render**: `https://your-app.onrender.com`
- **Custom domain**: `https://api.lexicraft.xyz`

## Testing

After setting the variable and redeploying:
1. Go to the survey page
2. Open browser console (F12)
3. Look for: `Survey API Base URL: https://your-backend-url/api/v1/survey`
4. The request should now go to your backend, not localhost

## Troubleshooting

### Still seeing localhost?
- Make sure you redeployed after adding the variable
- Check that the variable is set for the correct environment (Production/Preview/Development)
- Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Still getting 405?
- Verify your backend is running and accessible
- Test the backend directly: `curl https://your-backend-url/health`
- Check backend CORS settings allow your frontend domain

### Variable not showing in console?
- Environment variables are embedded at build time
- You must redeploy for changes to take effect
- Check Vercel build logs to confirm the variable is being used

