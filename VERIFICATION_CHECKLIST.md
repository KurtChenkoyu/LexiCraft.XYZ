# Environment Variables Verification Checklist

## ✅ Step 1: Health Endpoint (Already Verified)
```bash
curl https://lexicraftxyz-production.up.railway.app/health
```
**Status**: ✅ Working - Returns 200 OK

## 🔍 Step 2: Check Railway Logs

1. Go to [Railway Dashboard](https://railway.app)
2. Select your backend service
3. Go to **"Logs"** tab
4. Look for:
   - ✅ No errors about `DATABASE_URL` missing
   - ✅ No errors about `SUPABASE_JWT_SECRET` missing
   - ✅ Successful database connections
   - ✅ Service started successfully

## 🧪 Step 3: Test Authenticated Endpoints

### Option A: Test via Browser (Easiest)

1. **Go to the live site**: https://lexicraft.xyz (or your Vercel URL)
2. **Log in** with your credentials
3. **Open Browser DevTools** (F12 or Cmd+Option+I)
4. **Go to Network tab**
5. **Navigate to authenticated pages**:
   - Dashboard
   - Profile
   - Mine
   - Leaderboards
   - Verification

6. **Check API calls**:
   - Look for requests to `lexicraftxyz-production.up.railway.app`
   - Status should be **200 OK** (not 500)
   - Response should contain data (not error messages)

### Option B: Test via curl (Requires JWT Token)

1. **Get your JWT token**:
   - Log in to the live site
   - Open Browser DevTools → Application/Storage → Local Storage
   - Find `sb-<project-ref>-auth-token` or check Network tab for Authorization header

2. **Test profile endpoint**:
   ```bash
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
        https://lexicraftxyz-production.up.railway.app/api/v1/profile
   ```
   Should return user profile data, not 500 error.

## ✅ Expected Results

### Before Fix:
- ❌ All authenticated endpoints return 500 Internal Server Error
- ❌ Backend logs show: `ValueError: PostgreSQL connection string missing`
- ❌ Backend logs show: `WARNING: SUPABASE_JWT_SECRET not set`

### After Fix:
- ✅ All authenticated endpoints return 200 OK
- ✅ Backend logs show successful database connections
- ✅ Backend logs show token verification working
- ✅ Frontend displays user data correctly

## 🐛 Troubleshooting

### If endpoints still return 500:

1. **Check environment variables are set**:
   - Railway Dashboard → Service → Variables tab
   - Verify `DATABASE_URL` and `SUPABASE_JWT_SECRET` are present

2. **Check deployment status**:
   - Railway Dashboard → Service → Deployments tab
   - Ensure latest deployment completed successfully

3. **Check logs for specific errors**:
   - Railway Dashboard → Service → Logs tab
   - Look for any error messages

4. **Verify DATABASE_URL format**:
   - Should start with `postgresql://`
   - Should include port `6543` (Transaction mode)
   - Should end with `?sslmode=require`

5. **Verify SUPABASE_JWT_SECRET**:
   - Should be a long string (80-200 characters)
   - Should be the Legacy JWT Secret from Supabase

### If endpoints return 401 (Unauthorized):

- This is expected if you're not logged in
- Make sure you're testing with a valid JWT token
- Token expires after 1 hour - you may need to log in again

### If endpoints return 404 (Not Found):

- Check the endpoint URL is correct
- Some endpoints may have different paths

## 📝 Next Steps

Once verified:
1. ✅ All authenticated features should work
2. ✅ Users can log in and see their data
3. ✅ Leaderboards, profiles, progress all load correctly
4. ✅ The app maintains its "snappy" behavior with instant UI + background sync

