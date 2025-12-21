# Testing Checklist for Lemon Squeezy Webhook Integration

## Pre-Testing Setup

1. ✅ **Database Migration**: Run migration `025_add_subscription_fields.sql`
2. ✅ **Environment Variables**: 
   - `LEMON_SQUEEZY_WEBHOOK_SECRET` in `landing-page/.env.local`
   - `BACKEND_URL` configured (or `NEXT_PUBLIC_API_URL`)

## Testing Steps

### 1. Test Backend API Endpoint

**Run the test script:**
```bash
cd backend
source venv/bin/activate
python scripts/test_subscription_api.py
```

**Or test manually with curl:**
```bash
# Test with a real user email from your database
curl -X POST http://localhost:8000/api/subscriptions/activate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@example.com",
    "subscription_status": "active",
    "plan_type": "6-month-pass",
    "subscription_end_date": "2025-06-30T00:00:00Z"
  }'
```

**Expected Results:**
- ✅ Returns 200 OK with subscription data
- ✅ Status mapping works (e.g., "on_trial" → "trial")
- ✅ Idempotency check works (older dates are skipped)
- ✅ Returns 404 for non-existent emails

### 2. Test Webhook Signature Verification

**Run the test script:**
```bash
cd landing-page
node scripts/test_webhook_signature.js
```

**Expected Results:**
- ✅ Valid signatures are accepted
- ✅ Invalid signatures are rejected
- ✅ Handles both "sha256=..." and plain hash formats

### 3. Test Database Schema

**Verify columns exist:**
```bash
cd backend
source venv/bin/activate
python -c "
from src.database.postgres_connection import PostgresConnection
from sqlalchemy import text

conn = PostgresConnection()
session = conn.get_session()

result = session.execute(text('''
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'users' 
    AND column_name IN ('subscription_status', 'plan_type', 'subscription_end_date')
    ORDER BY column_name;
''')).fetchall()

print('Subscription columns:')
for row in result:
    print(f'  - {row[0]}: {row[1]}')

session.close()
conn.close()
"
```

**Expected Results:**
- ✅ All three columns exist: `subscription_status`, `plan_type`, `subscription_end_date`
- ✅ Index `idx_users_subscription_status` exists

### 4. Test Webhook Endpoint (Local Testing)

**Option A: Use ngrok to expose local server:**
```bash
# Terminal 1: Start Next.js dev server
cd landing-page
npm run dev

# Terminal 2: Expose with ngrok
ngrok http 3000

# Use the ngrok URL in Lemon Squeezy webhook settings:
# https://your-ngrok-url.ngrok.io/api/webhook/lemonsqueezy
```

**Option B: Test with a mock webhook request:**
```bash
# Generate a test signature
SECRET="your-webhook-secret"
BODY='{"meta":{"event_name":"subscription_created"},"data":{"attributes":{"status":"active","customer_email":"test@example.com"}}}'
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
SIGNATURE="sha256=$SIGNATURE"

# Send test webhook
curl -X POST http://localhost:3000/api/webhook/lemonsqueezy \
  -H "Content-Type: application/json" \
  -H "x-signature: $SIGNATURE" \
  -d "$BODY"
```

**Expected Results:**
- ✅ Returns 200 OK
- ✅ Calls backend API successfully
- ✅ Updates user subscription in database
- ✅ Handles email mismatches gracefully (logs as "Pending Assignment")

### 5. Test Status Mapping

**Test all status mappings:**
```bash
# Test each Lemon Squeezy status
for status in "on_trial" "active" "past_due" "unpaid" "cancelled" "expired"; do
  echo "Testing: $status"
  curl -X POST http://localhost:8000/api/subscriptions/activate \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"your-test-email@example.com\",
      \"subscription_status\": \"$status\",
      \"plan_type\": \"6-month-pass\"
    }"
  echo ""
done
```

**Expected Mappings:**
- `on_trial` → `trial`
- `active` → `active`
- `past_due` → `past_due`
- `unpaid` / `cancelled` / `expired` → `inactive`

### 6. Test Idempotency

**Test that older webhooks don't overwrite newer data:**
```bash
# First, set a future end date
curl -X POST http://localhost:8000/api/subscriptions/activate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@example.com",
    "subscription_status": "active",
    "subscription_end_date": "2025-12-31T00:00:00Z"
  }'

# Then try to set an older date (should be skipped)
curl -X POST http://localhost:8000/api/subscriptions/activate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@example.com",
    "subscription_status": "active",
    "subscription_end_date": "2025-06-30T00:00:00Z"
  }'
```

**Expected Results:**
- ✅ Second request returns `"skipped": true`
- ✅ Database still has the newer date (2025-12-31)

### 7. Test Email Mismatch Handling

**Test with non-existent email:**
```bash
curl -X POST http://localhost:3000/api/webhook/lemonsqueezy \
  -H "Content-Type: application/json" \
  -H "x-signature: $SIGNATURE" \
  -d '{
    "meta": {"event_name": "subscription_created"},
    "data": {
      "attributes": {
        "status": "active",
        "customer_email": "nonexistent@example.com"
      }
    }
  }'
```

**Expected Results:**
- ✅ Returns 200 OK (doesn't fail webhook)
- ✅ Logs "PENDING ASSIGNMENT" message
- ✅ Backend returns 404, but webhook handles it gracefully

## Production Testing

### 8. Test with Real Lemon Squeezy Webhook

1. **Configure webhook in Lemon Squeezy dashboard:**
   - URL: `https://lexicraft.xyz/api/webhook/lemonsqueezy`
   - Events: `order_created`, `subscription_created`, `subscription_updated`, `subscription_cancelled`
   - Get signing secret and add to `.env.local`

2. **Make a test purchase** (use Lemon Squeezy test mode)

3. **Check logs:**
   - Next.js logs should show webhook received
   - Backend logs should show subscription updated
   - Database should have updated user record

## Quick Verification Commands

**Check if backend is running:**
```bash
curl http://localhost:8000/health
```

**Check if Next.js is running:**
```bash
curl http://localhost:3000
```

**Check database columns:**
```bash
cd backend
source venv/bin/activate
python -c "
from src.database.postgres_connection import PostgresConnection
from sqlalchemy import text
conn = PostgresConnection()
session = conn.get_session()
result = session.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name LIKE 'subscription%'\")).fetchall()
print([r[0] for r in result])
session.close()
conn.close()
"
```

## Common Issues

1. **"ModuleNotFoundError: No module named 'dotenv'"**
   - Solution: Activate virtual environment: `source venv/bin/activate`

2. **"LEMON_SQUEEZY_WEBHOOK_SECRET is not configured"**
   - Solution: Add to `landing-page/.env.local`

3. **"User not found with email"**
   - Solution: Use a real email from your database, or create a test user first

4. **"Connection refused"**
   - Solution: Make sure backend is running on port 8000 and Next.js on port 3000

