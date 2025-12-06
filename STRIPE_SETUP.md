# Stripe Payment Integration - Setup Complete ✅

**Status:** ✅ **Complete**  
**Date:** January 2025

---

## What Was Implemented

### 1. Frontend Integration ✅

#### Packages Installed
- `@stripe/stripe-js` - Stripe.js client library
- `@stripe/react-stripe-js` - React components (for future use)
- `stripe` - Node.js Stripe SDK

#### Files Created
- `landing-page/lib/stripe.ts` - Stripe client utility
- `landing-page/app/api/deposits/create-checkout/route.ts` - Checkout session creation
- `landing-page/app/api/webhooks/stripe/route.ts` - Webhook handler
- `landing-page/components/deposit/DepositButton.tsx` - Deposit button component
- `landing-page/components/deposit/DepositForm.tsx` - Deposit form with amount selection

### 2. Backend Integration ✅

#### Packages Installed
- `stripe>=14.0.0` - Python Stripe SDK

#### Files Created
- `backend/src/api/deposits.py` - Deposit API endpoints
  - `POST /api/deposits/confirm` - Confirm deposit after payment
  - `GET /api/deposits/{child_id}/balance` - Get child balance

#### Files Updated
- `backend/src/main.py` - Added deposits router
- `backend/src/api/__init__.py` - Exported deposits router
- `backend/requirements.txt` - Added stripe package

---

## Environment Variables Required

### Frontend (`.env.local`)
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...  # For API routes
STRIPE_WEBHOOK_SECRET=whsec_...  # Get from Stripe dashboard
BACKEND_URL=http://localhost:8000  # Your backend URL
```

### Backend (`.env`)
```bash
STRIPE_SECRET_KEY=sk_test_...
DATABASE_URL=postgresql://...  # Your PostgreSQL connection
```

---

## How It Works

### Deposit Flow

1. **Parent selects deposit amount**
   - Uses `DepositForm` component
   - Preset amounts: NT$500, 1,000, 2,000, 5,000
   - Custom amount: NT$500 - NT$10,000

2. **Create checkout session**
   - Frontend calls `/api/deposits/create-checkout`
   - Backend creates Stripe Checkout session
   - Returns checkout URL

3. **Payment processing**
   - Parent redirected to Stripe Checkout
   - Enters payment details
   - Stripe processes payment

4. **Webhook confirmation**
   - Stripe sends webhook to `/api/webhooks/stripe`
   - Webhook handler calls backend `/api/deposits/confirm`
   - Backend:
     - Creates `points_transaction` record
     - Updates `points_accounts` balance
     - Credits available_points

5. **Success redirect**
   - Parent redirected to `/dashboard?success=true`
   - Balance updated in database

---

## Testing

### Test Cards (Stripe Test Mode)

**Successful Payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., `12/34`)
- CVC: Any 3 digits (e.g., `123`)
- ZIP: Any 5 digits (e.g., `12345`)

**Declined Payment:**
- Card: `4000 0000 0000 0002`
- (Use to test error handling)

### Test Checklist

- [ ] Install packages (`npm install` in landing-page)
- [ ] Add environment variables
- [ ] Test checkout creation: `POST /api/deposits/create-checkout`
- [ ] Complete test payment with test card
- [ ] Verify webhook received
- [ ] Check database: `points_transactions` and `points_accounts` updated
- [ ] Test balance endpoint: `GET /api/deposits/{child_id}/balance`

---

## Setting Up Webhooks

### 1. Install Stripe CLI (for local testing)

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Or download from: https://stripe.com/docs/stripe-cli
```

### 2. Login to Stripe CLI

```bash
stripe login
```

### 3. Forward webhooks to local server

```bash
stripe listen --forward-to localhost:3000/api/webhooks/stripe
```

This will give you a webhook signing secret (starts with `whsec_`).  
Add it to your `.env.local` as `STRIPE_WEBHOOK_SECRET`.

### 4. For Production

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. URL: `https://your-domain.com/api/webhooks/stripe`
4. Select events: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`
5. Copy webhook signing secret to environment variables

---

## API Endpoints

### Frontend API Routes

#### `POST /api/deposits/create-checkout`
Creates a Stripe Checkout session.

**Request:**
```json
{
  "amount": 1000,
  "childId": "uuid",
  "userId": "uuid"
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/...",
  "sessionId": "cs_test_..."
}
```

#### `POST /api/webhooks/stripe`
Handles Stripe webhook events (called by Stripe).

### Backend API Routes

#### `POST /api/deposits/confirm`
Confirms a deposit after payment succeeds.

**Request:**
```json
{
  "session_id": "cs_test_...",
  "child_id": "uuid",
  "user_id": "uuid",
  "amount": 1000.0
}
```

**Response:**
```json
{
  "message": "Deposit confirmed",
  "transaction_id": "uuid",
  "points_added": 1000,
  "amount_ntd": 1000.0
}
```

#### `GET /api/deposits/{child_id}/balance`
Gets current balance for a child.

**Response:**
```json
{
  "total_earned": 0,
  "available_points": 1000,
  "locked_points": 0,
  "withdrawn_points": 0
}
```

---

## Components Usage

### DepositForm Component

```tsx
import { DepositForm } from '@/components/deposit/DepositForm'

<DepositForm 
  childId="child-uuid"
  userId="user-uuid"
  onSuccess={() => console.log('Deposit successful!')}
/>
```

### DepositButton Component

```tsx
import { DepositButton } from '@/components/deposit/DepositButton'

<DepositButton
  amount={1000}
  childId="child-uuid"
  userId="user-uuid"
/>
```

---

## Database Schema

The deposit system uses these existing tables:

### `points_accounts`
- `child_id` - Links to child
- `available_points` - Points available for withdrawal
- `locked_points` - Points locked in learning
- `withdrawn_points` - Points already withdrawn

### `points_transactions`
- `child_id` - Links to child
- `transaction_type` - 'deposit', 'earned', 'withdrawn'
- `points` - Amount in points
- `amount_ntd` - Amount in NT$
- `metadata` - JSONB with session_id, user_id

---

## Next Steps

### Immediate
1. ✅ Stripe integration complete
2. ⏳ Set up webhook endpoint in Stripe dashboard
3. ⏳ Test payment flow end-to-end
4. ⏳ Add deposit page to dashboard

### Future Enhancements
- [ ] Add deposit history view
- [ ] Add refund handling (7-day policy)
- [ ] Add email notifications
- [ ] Add tax reporting (for rewards ≥NT$1,000)
- [ ] Add multiple payment methods (ECPay, convenience store)

---

## Troubleshooting

### Webhook not received
- Check webhook URL is correct
- Verify webhook secret matches
- Check Stripe dashboard for webhook delivery logs
- Use Stripe CLI for local testing

### Payment succeeds but balance not updated
- Check webhook handler logs
- Verify backend API is accessible
- Check database connection
- Verify child_id and user_id are correct

### Checkout session creation fails
- Verify `STRIPE_SECRET_KEY` is set
- Check API key is for correct mode (test vs live)
- Verify amount is within limits (500-10000)

---

## Security Notes

- ✅ Webhook signature verification implemented
- ✅ Environment variables for sensitive keys
- ✅ Input validation (amount limits)
- ✅ Database transactions for consistency
- ⚠️ Add authentication middleware before production
- ⚠️ Add rate limiting for API endpoints
- ⚠️ Add logging for audit trail

---

**Status:** ✅ **Ready for Testing**

Test the integration with Stripe test cards, then move to live mode when ready!

