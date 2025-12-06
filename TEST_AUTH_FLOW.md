# Test Auth Flow - Step by Step

## ✅ What's Ready

- ✅ Auth middleware implemented
- ✅ JWT secret configured
- ✅ Backend server running
- ✅ Frontend server running
- ✅ All API endpoints updated

---

## 🧪 Testing Steps

### 1. Test Backend Health

```bash
curl http://localhost:8000/health
```

**Expected**: `{"status":"ok","version":"7.1"}`

---

### 2. Test Auth Middleware (Without Token)

```bash
curl -X GET http://localhost:8000/api/users/me
```

**Expected**: `401 Unauthorized` with message about missing Authorization header

**This confirms**: Auth middleware is working and rejecting unauthenticated requests ✅

---

### 3. Test Full Flow in Browser

1. **Open browser**: http://localhost:3000

2. **Sign up**:
   - Go to `/signup`
   - Sign up with email/password or Google
   - Should redirect to `/onboarding`

3. **Complete onboarding**:
   - Select account type (parent/learner/both)
   - Enter age
   - Submit
   - Should redirect to `/dashboard`

4. **Check browser console** (F12):
   - Look for API requests
   - Verify they have `Authorization: Bearer <token>` header
   - No `user_id` query params in URLs

5. **Check Network tab**:
   - All API requests should have auth headers
   - Status codes should be 200 (not 401)

---

### 4. Test API Endpoints

#### Test `/api/users/me` (requires auth)

**In browser console** (after login):
```javascript
// Get token from Supabase
const supabase = window.supabase || (await import('/lib/supabase/client')).createClient()
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

// Test API
fetch('http://localhost:8000/api/users/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(console.log)
```

**Expected**: User info with roles

---

#### Test `/api/users/onboarding/status` (requires auth)

```javascript
fetch('http://localhost:8000/api/users/onboarding/status', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(console.log)
```

**Expected**: `{ completed: true, roles: [...], ... }`

---

### 5. Verify No Warnings

**Check backend logs** - you should NOT see:
```
UserWarning: SUPABASE_JWT_SECRET not set. Token verification is disabled.
```

If you don't see this warning, JWT secret is loaded correctly ✅

---

## ✅ Success Criteria

- [ ] Backend health check works
- [ ] Unauthenticated requests return 401
- [ ] Signup flow works
- [ ] Onboarding completes successfully
- [ ] Dashboard loads
- [ ] API requests have auth headers
- [ ] No warnings in backend logs
- [ ] No `user_id` query params in URLs

---

## 🐛 Troubleshooting

### Issue: 401 Unauthorized on all requests

**Check**:
1. Token is being sent (check Network tab)
2. Token is valid (not expired)
3. JWT secret is set correctly

**Fix**:
- Re-login to get fresh token
- Verify `SUPABASE_JWT_SECRET` in `.env`

---

### Issue: "Token verification failed"

**Check**:
1. JWT secret matches Supabase project
2. Token format is correct
3. Token not expired

**Fix**:
- Get fresh token (re-login)
- Verify secret from correct Supabase project

---

### Issue: Frontend not sending auth headers

**Check**:
1. Using `authenticatedGet`/`authenticatedPost` functions
2. User is logged in (has session)
3. Token exists in session

**Fix**:
- Ensure using authenticated API client functions
- Check user is logged in
- Verify Supabase session exists

---

## 📊 What to Look For

### ✅ Good Signs:
- All API requests have `Authorization: Bearer ...` header
- Status codes are 200 (not 401)
- No warnings in backend logs
- User info loads correctly
- Onboarding completes successfully

### ❌ Bad Signs:
- 401 errors on authenticated requests
- Missing Authorization headers
- Warnings about JWT secret
- `user_id` still in query params

---

## 🎯 Next Steps After Testing

Once everything works locally:

1. **Deploy backend** to Railway/Render
2. **Set NEXT_PUBLIC_API_URL** in Vercel
3. **Test in production**
4. **Fix any issues**

---

## Quick Test Script

Run this in browser console after login:

```javascript
async function testAuth() {
  const supabase = (await import('/lib/supabase/client')).createClient()
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    console.error('❌ Not logged in')
    return
  }
  
  const token = session.access_token
  console.log('✅ Token exists:', token.substring(0, 20) + '...')
  
  // Test /api/users/me
  const response = await fetch('http://localhost:8000/api/users/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  
  if (response.ok) {
    const data = await response.json()
    console.log('✅ Auth working! User:', data)
  } else {
    console.error('❌ Auth failed:', await response.text())
  }
}

testAuth()
```

