# Google OAuth Redirect URI Mismatch - Troubleshooting

## Current Error
```
Error 400: redirect_uri_mismatch
redirect_uri=https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
```

## Exact URI to Add (Copy This Exactly)
```
https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
```

## Checklist

### ✅ Step 1: Verify in Google Cloud Console
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Scroll to **"Authorized redirect URIs"**
4. Verify the URI is listed EXACTLY as:
   ```
   https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
   ```
5. Check for:
   - ❌ No trailing slash: `.../callback/` (WRONG)
   - ✅ No trailing slash: `.../callback` (CORRECT)
   - ❌ No extra spaces before/after
   - ❌ No `http://` (must be `https://`)

### ✅ Step 2: Click "Save"
- Make sure you clicked the **"Save"** button at the bottom
- Wait for confirmation that settings were saved

### ✅ Step 3: Wait for Propagation
- Google says: "It may take 5 minutes to a few hours for settings to take effect"
- Try again after 5-10 minutes

### ✅ Step 4: Verify Supabase Configuration
1. Go to Supabase Dashboard → Authentication → Providers
2. Check that Google provider is **enabled**
3. Verify Client ID and Client Secret are correct
4. Make sure no extra spaces in the credentials

### ✅ Step 5: Clear Browser Cache
- Sometimes browsers cache OAuth redirects
- Try incognito/private window
- Or clear cookies for `accounts.google.com`

## Common Issues

### Issue: URI has trailing slash
**Wrong:**
```
https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback/
```

**Correct:**
```
https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
```

### Issue: Using http instead of https
**Wrong:**
```
http://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
```

**Correct:**
```
https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
```

### Issue: Extra whitespace
**Wrong:**
```
 https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback 
```

**Correct:**
```
https://cwgexbjyfcqndeyhravb.supabase.co/auth/v1/callback
```

## Still Not Working?

1. **Double-check the exact URI** in the error message matches what's in Google Cloud Console
2. **Wait 10-15 minutes** after saving
3. **Try in incognito mode** to rule out cache issues
4. **Verify Supabase Client ID** matches the one in Google Cloud Console

## Reference
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2/web-server#authorization-errors-redirect-uri-mismatch)

