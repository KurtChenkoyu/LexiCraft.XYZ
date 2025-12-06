# Frontend Routing - How to Access the App

## The Issue

Your app uses **locale-based routing**. This means:
- All routes require a locale prefix (`/zh-TW/` or `/en/`)
- `http://localhost:3000` should redirect to `http://localhost:3000/zh-TW/`
- If you see 404, you might be accessing a route without locale

---

## ✅ Correct URLs

### Home Page
- ✅ `http://localhost:3000/zh-TW` (or `/zh-TW/`)
- ✅ `http://localhost:3000` (auto-redirects to `/zh-TW/`)

### Other Pages
- ✅ `http://localhost:3000/zh-TW/signup`
- ✅ `http://localhost:3000/zh-TW/login`
- ✅ `http://localhost:3000/zh-TW/onboarding`
- ✅ `http://localhost:3000/zh-TW/dashboard`
- ✅ `http://localhost:3000/zh-TW/survey`

---

## 🔍 Troubleshooting

### If you see 404 on `http://localhost:3000`:

**Try these:**

1. **Wait for redirect**:
   - The page should auto-redirect to `/zh-TW/`
   - Wait 1-2 seconds
   - Check if URL changes to `/zh-TW/`

2. **Manually go to**:
   ```
   http://localhost:3000/zh-TW
   ```

3. **Check browser console**:
   - Open DevTools (F12)
   - Look for redirect errors
   - Check Network tab for failed requests

4. **Clear browser cache**:
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Or clear cache and reload

---

## 🧪 Test the Routes

### Test Home Page
```bash
curl -L http://localhost:3000
# Should redirect and return HTML
```

### Test Signup
```bash
curl http://localhost:3000/zh-TW/signup
# Should return signup page
```

### Test Login
```bash
curl http://localhost:3000/zh-TW/login
# Should return login page
```

---

## 📝 How Locale Routing Works

1. **User visits**: `http://localhost:3000`
2. **Middleware checks**: No locale in path
3. **Middleware redirects**: To `/zh-TW/` (default locale)
4. **Page loads**: Home page with locale

This is handled by:
- `middleware.ts` - Redirects to default locale
- `app/[locale]/page.tsx` - Home page component
- `i18n/routing.ts` - Locale configuration

---

## ✅ Quick Fix

**Just add `/zh-TW` to your URL:**

Instead of: `http://localhost:3000`  
Use: `http://localhost:3000/zh-TW`

Or wait for the automatic redirect (should happen in 1-2 seconds).

---

## 🎯 What to Test

1. **Home page**: `http://localhost:3000/zh-TW`
2. **Signup**: `http://localhost:3000/zh-TW/signup`
3. **Login**: `http://localhost:3000/zh-TW/login`
4. **Onboarding** (after signup): `http://localhost:3000/zh-TW/onboarding`
5. **Dashboard** (after onboarding): `http://localhost:3000/zh-TW/dashboard`

---

## 💡 Why This Design?

Locale-based routing allows:
- ✅ Multiple languages (zh-TW, en, etc.)
- ✅ SEO-friendly URLs
- ✅ Easy language switching
- ✅ Clean URL structure

This is a common pattern in Next.js i18n apps.

