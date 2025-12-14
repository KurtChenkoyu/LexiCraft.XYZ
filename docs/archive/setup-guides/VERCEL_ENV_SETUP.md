# Vercel Environment Variables Setup

**Error:** `STRIPE_SECRET_KEY is not configured`

This means the Stripe environment variables are not set in your Vercel deployment.

---

## Quick Fix: Add Environment Variables to Vercel

### Step 1: Go to Vercel Dashboard
1. Visit: https://vercel.com/dashboard
2. Click on your project: **lexicraft-landing**

### Step 2: Add Environment Variables
1. Go to **Settings** → **Environment Variables**
2. Click **"Add New"**

### Step 3: Add These Variables

Add each variable one by one:

#### 1. Stripe Publishable Key (Public)
```
Name: NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
Value: pk_test_... (from Stripe dashboard)
Environment: Production, Preview, Development (select all)
```

#### 2. Stripe Secret Key (Private)
```
Name: STRIPE_SECRET_KEY
Value: sk_test_... (from Stripe dashboard)
Environment: Production, Preview, Development (select all)
```

#### 3. Stripe Webhook Secret (Private)
```
Name: STRIPE_WEBHOOK_SECRET
Value: whsec_... (from Stripe webhook endpoint)
Environment: Production, Preview, Development (select all)
```

#### 4. Backend URL (Optional - for webhook)
```
Name: BACKEND_URL
Value: http://localhost:8000 (or your backend URL)
Environment: Production, Preview, Development (select all)
```

### Step 4: Redeploy
After adding all variables:
1. Go to **Deployments** tab
2. Click **"..."** on the latest deployment
3. Click **"Redeploy"**
4. Or just push a new commit (auto-deploys)

---

## Where to Find Stripe Keys

### Stripe Dashboard
1. Go to: https://dashboard.stripe.com/test/apikeys
2. You'll see:
   - **Publishable key**: `pk_test_...` (starts with `pk_test_`)
   - **Secret key**: `sk_test_...` (starts with `sk_test_`)
   - Click "Reveal" to see the secret key

### Webhook Secret
1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click on your webhook endpoint: "LexiCraft MVP - Payment webhooks"
3. In "Signing secret" section, click "Reveal"
4. Copy the secret: `whsec_...`

---

## Verify It's Working

After redeploying:
1. Visit: `https://lexicraft-landing.vercel.app/zh-TW/dashboard`
2. Try making a test deposit
3. The error should be gone!

---

## Troubleshooting

### Still getting the error?
- ✅ Make sure you selected **all environments** (Production, Preview, Development)
- ✅ Make sure you **redeployed** after adding variables
- ✅ Check that the keys start with `pk_test_` and `sk_test_` (for test mode)
- ✅ Verify no extra spaces in the variable values

### Test with Stripe Test Card
Once working, test with:
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., `12/34`)
- CVC: Any 3 digits (e.g., `123`)
- ZIP: Any 5 digits (e.g., `12345`)

---

**Status:** ⚠️ **Environment variables need to be added to Vercel**

