# Test JWT Token Verification

Since your user exists in the database, the 401 error is likely due to JWT token verification failing.

## Step 1: Get Your Token

Open your browser console (F12) on your app and run:

```javascript
// Get your Supabase session token
const supabase = createClient()
const { data: { session } } = await supabase.auth.getSession()
console.log('Token:', session?.access_token)
console.log('Token length:', session?.access_token?.length)
```

Copy the token value.

## Step 2: Test Debug Endpoint

Use the debug endpoint we created to see what's happening:

```bash
# Replace YOUR_TOKEN with the token from Step 1
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/users/debug/token
```

This will show:
- ✅ If token is being extracted correctly
- ✅ If token verification is working
- ✅ What user ID is in the token
- ❌ Any error messages

## Step 3: Check Backend Logs

The backend should be logging authentication attempts. Check the terminal where you're running the backend for messages like:
- "Token extracted (length: XXX)"
- "Token verified successfully. User ID: XXX"
- "Invalid token: XXX"

## Step 4: Verify Token Claims

The token should contain:
- `sub`: Your user ID (should match the ID from the database query)
- `email`: Your email
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp

## Common Issues

### Issue 1: Token Expired
- **Symptom**: "Token has expired" error
- **Fix**: Sign out and sign in again to get a fresh token

### Issue 2: JWT Secret Mismatch
- **Symptom**: "Invalid token" or "Token verification failed"
- **Fix**: Verify `SUPABASE_JWT_SECRET` in backend `.env` matches Supabase dashboard

### Issue 3: Token Not Being Sent
- **Symptom**: "Missing Authorization header"
- **Fix**: Check browser Network tab to see if `Authorization` header is present

### Issue 4: User ID Mismatch
- **Symptom**: Token verifies but user not found
- **Fix**: Check if token's `sub` field matches your user ID in database

## Next Steps

1. Run the debug endpoint test
2. Share the output
3. Check backend logs
4. We'll fix based on the specific error

