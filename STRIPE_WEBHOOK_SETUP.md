# Stripe Webhook Setup - Quick Guide

**Your Vercel Domain:** `lexicraft-landing.vercel.app`

---

## Step 1: Add Webhook in Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click **"Add endpoint"**
3. **Endpoint URL:** 
   ```
   https://lexicraft-landing.vercel.app/api/webhooks/stripe
   ```
4. **Description:** "LexiCraft MVP - Payment webhooks"
5. **Events to send:**
   - ✅ `checkout.session.completed`
   - ✅ `payment_intent.succeeded`
   - ✅ `payment_intent.payment_failed`
6. Click **"Add endpoint"**

---

## Step 2: Copy Webhook Signing Secret

After creating the endpoint:
1. Click on the endpoint you just created
2. Find **"Signing secret"** section
3. Click **"Reveal"** or **"Click to reveal"**
4. Copy the secret (starts with `whsec_...`)

---

## Step 3: Add to Vercel Environment Variables

1. Go to: https://vercel.com/dashboard
2. Click on your project: **lexicraft-landing**
3. Go to **Settings** → **Environment Variables**
4. Add these variables (if not already added):

```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_... (paste from Step 2)
```

5. Make sure to select **Production**, **Preview**, and **Development** environments
6. Click **"Save"**

---

## Step 4: Redeploy (if needed)

After adding environment variables:
1. Go to **Deployments** tab
2. Click **"..."** on the latest deployment
3. Click **"Redeploy"**
4. Or just push a new commit (auto-deploys)

---

## Step 5: Test the Webhook

### Test with Stripe CLI (Local Testing)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:3000/api/webhooks/stripe
```

This gives you a local webhook secret for testing.

### Test with Real Payment

1. Use test card: `4242 4242 4242 4242`
2. Complete a test payment
3. Check Stripe Dashboard → Webhooks → Your endpoint
4. You should see a successful delivery

---

## Verify It's Working

1. **Check Stripe Dashboard:**
   - Go to Webhooks → Your endpoint
   - You should see recent events
   - Status should be "Succeeded" (green)

2. **Check Vercel Logs:**
   - Go to Vercel Dashboard → Your Project → Deployments
   - Click on latest deployment → "Functions" tab
   - Look for `/api/webhooks/stripe` logs

3. **Test Payment:**
   - Make a test deposit
   - Check database: `points_transactions` should have new record
   - Check `points_accounts` should be updated

---

## Troubleshooting

### Webhook not receiving events
- ✅ Verify URL is correct: `https://lexicraft-landing.vercel.app/api/webhooks/stripe`
- ✅ Check webhook secret matches in Vercel env vars
- ✅ Verify events are selected in Stripe dashboard
- ✅ Check Vercel function logs for errors

### 400 Bad Request
- ✅ Webhook secret mismatch - verify `STRIPE_WEBHOOK_SECRET` in Vercel
- ✅ Check Stripe signature header is being sent

### 500 Internal Server Error
- ✅ Check backend API is accessible
- ✅ Verify database connection
- ✅ Check function logs in Vercel

---

## Your Webhook URL

**Production:**
```
https://lexicraft-landing.vercel.app/api/webhooks/stripe
```

**For local testing:**
```
http://localhost:3000/api/webhooks/stripe
```

---

**Next:** Once webhook is set up, test a payment with test card `4242 4242 4242 4242`!

