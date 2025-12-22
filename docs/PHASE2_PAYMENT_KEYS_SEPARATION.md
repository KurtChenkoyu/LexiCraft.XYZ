# Phase 2: Payment Keys Separation (Test vs Live)

## Overview

Separate payment provider keys for development and production to ensure:
- **Test mode keys** used in development (no real charges)
- **Live mode keys** used in production (real payments)
- No accidental charges during development
- Safe testing of payment flows

## Architecture

```
Development Environment:
├── Stripe: Test Mode Keys (sk_test_..., pk_test_...)
├── Lemon Squeezy: Test Mode (if applicable)
└── Used by: Local development, dev deployments

Production Environment:
├── Stripe: Live Mode Keys (sk_live_..., pk_live_...)
├── Lemon Squeezy: Live Mode (if applicable)
└── Used by: Railway/Vercel production deployments
```

## Stripe Keys

### Test Mode Keys (Development)

**Where to get:**
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)
2. Make sure you're in **Test mode** (toggle in top right)
3. Copy:
   - **Publishable key:** `pk_test_...` (starts with `pk_test_`)
   - **Secret key:** `sk_test_...` (starts with `sk_test_`)

**Where to use:**
- `landing-page/.env.local` (local development)
- Railway/Vercel **preview** environments (optional)

### Live Mode Keys (Production)

**Where to get:**
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Make sure you're in **Live mode** (toggle in top right)
3. Copy:
   - **Publishable key:** `pk_live_...` (starts with `pk_live_`)
   - **Secret key:** `sk_live_...` (starts with `sk_live_`)

**Where to use:**
- Railway backend environment variables (production)
- Vercel frontend environment variables (production)

### Environment Variable Names

**Frontend (`landing-page/.env.local` for dev):**
```bash
# Test Mode (Development)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**Backend (`backend/.env` for dev):**
```bash
# Test Mode (Development)
STRIPE_SECRET_KEY=sk_test_...
```

**Railway/Vercel (Production):**
```bash
# Live Mode (Production)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

## Lemon Squeezy Keys (If Used)

### Test Mode Keys (Development)

**Where to get:**
1. Go to [Lemon Squeezy Dashboard](https://app.lemonsqueezy.com/settings/api)
2. Use **Test Mode** API keys
3. Copy:
   - **API Key:** Test mode key

**Where to use:**
- Local development `.env` files

### Live Mode Keys (Production)

**Where to get:**
1. Go to [Lemon Squeezy Dashboard](https://app.lemonsqueezy.com/settings/api)
2. Use **Live Mode** API keys
3. Copy:
   - **API Key:** Live mode key

**Where to use:**
- Railway/Vercel production environment variables

## Security Best Practices

1. **Never commit keys to git:**
   - All payment keys should be in `.env` files (already in `.gitignore`)
   - Never hardcode keys in source code

2. **Use different keys per environment:**
   - Dev: Test mode keys
   - Prod: Live mode keys
   - Never mix them

3. **Verify key mode before deploying:**
   - Check key prefix: `sk_test_` vs `sk_live_`
   - Test mode keys won't process real payments (safe for dev)
   - Live mode keys will process real payments (only for prod)

4. **Rotate keys if exposed:**
   - If keys are accidentally committed or exposed, rotate them immediately
   - Revoke old keys in Stripe/Lemon Squeezy dashboard

## Verification Checklist

After setup, verify:

- [ ] Dev environment uses test mode keys (`sk_test_`, `pk_test_`)
- [ ] Production environment uses live mode keys (`sk_live_`, `pk_live_`)
- [ ] Test payment flow in dev (should use test mode)
- [ ] Verify production keys are in Railway/Vercel (not in code)
- [ ] No payment keys committed to git

## Testing Payment Flows

### Test Mode (Development)

**Stripe Test Cards:**
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- 3D Secure: `4000 0025 0000 3155`

**Verify:**
- Payments show in Stripe Dashboard → Test mode
- No real charges to cards
- Can refund test payments

### Live Mode (Production)

**⚠️ Warning:** Only test with real cards if you're ready to process real payments!

**Verify:**
- Payments show in Stripe Dashboard → Live mode
- Real charges are processed
- Refunds work correctly

## Next Steps

After completing payment keys separation:
1. Update Railway environment variables with production keys
2. Test payment flow in both environments
3. Document key locations for team members

