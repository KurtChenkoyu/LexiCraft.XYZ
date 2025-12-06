# How to Get JWT Secret from Supabase Dashboard

## Quick Steps

### Option 1: Use Legacy JWT Secret (Easier for MVP)

1. **You're already on the right page!** (Settings → JWT Keys)

2. **Click the "Legacy JWT Secret" tab** (next to "JWT Signing Keys")

3. **You'll see the JWT Secret**:
   - It will show as a long string
   - Click the **eye icon** or **"Reveal"** button to show it
   - Copy the entire secret

4. **Add to your `.env` file**:
   ```bash
   SUPABASE_JWT_SECRET=your-copied-secret-here
   ```

### Option 2: Use New JWT Signing Keys (More Secure, More Complex)

If you want to use the new JWT signing keys:

1. **Click "Migrate JWT secret"** button (green button you see)

2. **Follow the migration process**

3. **Get the signing key**:
   - After migration, you'll see signing keys
   - Use the **private key** for backend verification

**Note**: For MVP, **Option 1 (Legacy JWT Secret) is recommended** - it's simpler and works perfectly for our auth middleware.

---

## What You Should See

After clicking "Legacy JWT Secret" tab, you should see:

```
JWT Secret
[Long string of characters]
[Eye icon] Reveal
```

Click "Reveal" and copy the entire secret.

---

## Why Legacy JWT Secret?

- ✅ **Simpler**: One secret to manage
- ✅ **Works with our middleware**: Our code uses standard JWT verification
- ✅ **Good for MVP**: Perfect for getting started
- ✅ **Can migrate later**: You can switch to signing keys later if needed

---

## After Getting the Secret

1. **Copy the secret** (the entire long string)

2. **Add to `backend/.env`**:
   ```bash
   SUPABASE_JWT_SECRET=paste-your-secret-here
   ```

3. **Restart your backend server**

4. **Test**: The warning about missing JWT secret should disappear

---

## Troubleshooting

**Can't find "Legacy JWT Secret" tab?**
- Make sure you're on Settings → JWT Keys page
- The tab should be visible next to "JWT Signing Keys"

**Secret seems too short?**
- Make sure you copied the entire secret
- It should be a very long string (usually 100+ characters)

**Still seeing warnings?**
- Double-check the variable name: `SUPABASE_JWT_SECRET` (exact spelling)
- Make sure `.env` file is in `backend/` directory
- Restart your backend server after adding to `.env`

