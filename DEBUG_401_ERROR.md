# Debugging 401 Unauthorized Error

## Problem
Frontend is getting `401 Unauthorized` when trying to access:
- `GET /api/users/onboarding/status`
- `GET /api/users/me/children`

## Possible Causes

### 1. JWT Token Verification Failing
The token might be:
- Expired
- Invalid format
- Signed with wrong secret
- Missing required claims

### 2. User Not in Database
When a user signs up with Google:
- Supabase creates an auth user
- A trigger should create a user in `public.users` table
- If the trigger failed or wasn't set up, the user won't exist

### 3. JWT Secret Mismatch
The `SUPABASE_JWT_SECRET` might not match the secret used to sign tokens.

## Debugging Steps

### Step 1: Test Token Extraction
Open browser console and run:
```javascript
// Get your token
const supabase = createClient()
const { data: { session } } = await supabase.auth.getSession()
console.log('Token:', session?.access_token)
console.log('Token length:', session?.access_token?.length)
```

### Step 2: Test Debug Endpoint
Use the debug endpoint to see what's happening:
```bash
# Replace YOUR_TOKEN with the token from Step 1
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/users/debug/token
```

This will show:
- If token is being extracted correctly
- If token verification is working
- What user ID is in the token
- Any error messages

### Step 3: Check if User Exists
Check if the user exists in the database:
```sql
-- In Supabase SQL Editor
SELECT id, email, name, created_at 
FROM public.users 
WHERE id = 'USER_ID_FROM_TOKEN';
```

### Step 4: Check Backend Logs
The backend should now log:
- Token extraction attempts
- Token verification results
- User ID from token
- Any errors

Look for log messages like:
- "Token extracted (length: XXX)"
- "Token verified successfully. User ID: XXX"
- "Invalid token: XXX"

### Step 5: Verify JWT Secret
Check if the JWT secret is correct:
```bash
cd backend
source venv/bin/activate
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('JWT Secret set:', os.getenv('SUPABASE_JWT_SECRET') is not None)"
```

## Quick Fix: Create Missing User

If the user doesn't exist in the database, you can create them manually:

```sql
-- Get user info from Supabase Auth
SELECT id, email, raw_user_meta_data 
FROM auth.users 
WHERE email = 'user@example.com';

-- Create user in public.users (replace with actual values)
INSERT INTO public.users (
  id, 
  email, 
  name, 
  country, 
  email_confirmed,
  created_at,
  updated_at
)
VALUES (
  'USER_ID_FROM_AUTH',
  'user@example.com',
  'User Name',
  'TW',
  TRUE,
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Add default learner role
INSERT INTO public.user_roles (user_id, role, created_at)
VALUES ('USER_ID_FROM_AUTH', 'learner', NOW())
ON CONFLICT (user_id, role) DO NOTHING;
```

## Next Steps

1. **Test the debug endpoint** to see what error you're getting
2. **Check backend logs** for detailed error messages
3. **Verify user exists** in the database
4. **Check JWT secret** is correct in Supabase dashboard

## Files Modified

- `backend/src/middleware/auth.py` - Added logging
- `backend/src/api/users.py` - Added `/debug/token` endpoint
- `backend/scripts/test_auth.py` - Test script for token verification

