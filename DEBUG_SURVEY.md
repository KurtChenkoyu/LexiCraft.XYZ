# Debugging Survey Initialization Error

## Quick Debug Steps

### 1. Check Browser Console
Open your browser's Developer Tools (F12) and check the Console tab. Look for:
- Network errors (CORS, connection refused, etc.)
- API response errors
- The actual error message

### 2. Check Network Tab
In Developer Tools → Network tab:
- Look for the request to `/api/v1/survey/start`
- Check the request URL (is it pointing to localhost or your backend?)
- Check the response status code
- Check the response body for error details

### 3. Verify API URL Configuration

**In Vercel:**
1. Go to Project Settings → Environment Variables
2. Check if `NEXT_PUBLIC_API_URL` is set
3. Verify the value is correct (should be your backend URL, not localhost)

**To check what URL is being used:**
Open browser console and run:
```javascript
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
```

### 4. Test Backend Directly

Test if your backend is accessible:

```bash
# Replace with your actual backend URL
curl -X POST https://your-backend-url.com/api/v1/survey/start \
  -H "Content-Type: application/json" \
  -d '{"cefr_level": "A2", "user_id": "test-user-id"}'
```

### 5. Common Issues

#### Issue: "Network Error" or "Connection Refused"
**Cause**: Backend is not accessible or URL is wrong
**Fix**: 
- Verify `NEXT_PUBLIC_API_URL` is set in Vercel
- Ensure backend is deployed and running
- Check backend logs for errors

#### Issue: "CORS Error"
**Cause**: Backend CORS settings don't allow your frontend domain
**Fix**: Check backend CORS configuration in `backend/src/main.py`

#### Issue: "500 Internal Server Error"
**Cause**: Backend error (database connection, missing tables, etc.)
**Fix**: 
- Check backend logs
- Verify database connection
- Check if `survey_sessions` table exists

#### Issue: "404 Not Found"
**Cause**: API endpoint doesn't exist or URL is wrong
**Fix**: 
- Verify backend is running
- Check API route is `/api/v1/survey/start`
- Verify backend includes the survey router

### 6. Check Database Tables

The survey API requires these tables:
- `survey_sessions`
- `survey_history`

Verify they exist:
```sql
-- Run in Supabase SQL Editor
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('survey_sessions', 'survey_history');
```

### 7. Enable Detailed Logging

Add this to your browser console to see more details:
```javascript
// In browser console
localStorage.setItem('debug', 'true')
// Then reload the page
```

## What to Share for Help

If you need help, share:
1. Browser console errors (screenshot or copy/paste)
2. Network tab request/response (screenshot)
3. Backend logs (if accessible)
4. The API URL being used (from console.log)
5. Whether backend is accessible (curl test result)

