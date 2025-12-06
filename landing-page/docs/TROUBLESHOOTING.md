# Troubleshooting Deployment Issues

## Common Issues and Fixes

### Issue 1: Page Not Loading / 404 Error

**Symptoms:**
- Visiting the root URL shows 404
- Page doesn't load

**Fix:**
The middleware should automatically redirect `/` to `/zh-TW` or `/en`. If it's not working:

1. **Check Vercel deployment logs** for middleware errors
2. **Verify middleware is running**: Check Vercel function logs
3. **Test direct URLs**:
   - `https://your-site.vercel.app/zh-TW` (should work)
   - `https://your-site.vercel.app/en` (should work)

### Issue 2: Middleware Not Working

**Symptoms:**
- Root redirect not happening
- Language detection not working

**Possible Causes:**
1. **Middleware not deployed**: Check Vercel logs
2. **Matcher pattern issue**: The matcher should catch all routes except API

**Fix:**
The middleware matcher is configured to catch all routes except:
- `/api/*`
- `/_next/*`
- `/_vercel/*`
- Files with dots (e.g., `favicon.ico`)

### Issue 3: API Route Not Working

**Symptoms:**
- Form submission fails
- 404 on `/api/waitlist`

**Fix:**
API routes should work at `/api/waitlist` (not `/zh-TW/api/waitlist`). The middleware skips API routes.

### Issue 4: Language Detection Not Working

**Symptoms:**
- Always shows one language
- Doesn't detect Taiwan IP

**Fix:**
1. **Check Vercel geolocation**: Vercel provides `x-vercel-ip-country` header automatically
2. **Test from different locations**: Use VPN to test
3. **Use language switcher**: Manual toggle should always work

### Issue 5: Build Errors

**Symptoms:**
- Deployment fails
- Build errors in Vercel logs

**Common Fixes:**
1. **Missing dependencies**: Run `npm install` locally first
2. **TypeScript errors**: Check `npm run build` locally
3. **Missing environment variables**: Some are optional, but check logs

## Quick Debug Steps

1. **Check Vercel Deployment Logs**:
   - Go to Vercel dashboard → Your project → Deployments
   - Click on latest deployment → View logs

2. **Test Direct URLs**:
   ```
   https://your-site.vercel.app/zh-TW
   https://your-site.vercel.app/en
   https://your-site.vercel.app/api/waitlist
   ```

3. **Check Browser Console**:
   - Open browser DevTools (F12)
   - Check Console for errors
   - Check Network tab for failed requests

4. **Verify Environment Variables**:
   - Vercel dashboard → Settings → Environment Variables
   - Ensure all required vars are set (if using email/analytics)

## Expected Behavior

✅ **Working correctly:**
- Root `/` redirects to `/zh-TW` or `/en` based on IP
- `/zh-TW` shows Traditional Chinese
- `/en` shows English
- Language switcher in top-right works
- Privacy policy at `/zh-TW/privacy` and `/en/privacy`
- API route at `/api/waitlist` works

## Still Not Working?

1. **Share the specific error message** you're seeing
2. **Check Vercel function logs** for middleware errors
3. **Test the build locally**: `npm run build && npm start`
4. **Check the deployed URL** and share what you see

## Quick Test Commands

```bash
# Test build locally
cd landing-page
npm run build
npm start

# Test on localhost:3000
# Should redirect to /zh-TW or /en
```

