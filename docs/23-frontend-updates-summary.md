# Frontend Updates Summary: Unified User Model Migration

**Date:** 2024  
**Status:** ✅ Complete

---

## Overview

Updated all frontend components to use the unified user model with `learner_id` instead of `child_id` and integrated with the new API endpoints.

---

## Updated Components

### 1. Dashboard Page (`app/[locale]/dashboard/page.tsx`)

**Changes:**
- ✅ Fetches children from `/api/users/me/children` endpoint
- ✅ Displays child selector if multiple children
- ✅ Uses `learnerId` instead of `childId`
- ✅ Shows loading state while fetching children
- ✅ Handles case when user has no children

**New Features:**
- Child selection dropdown (if multiple children)
- Real-time child data from API
- Better error handling

### 2. DepositForm Component (`components/deposit/DepositForm.tsx`)

**Changes:**
- ✅ `childId` prop → `learnerId` prop
- ✅ Updated to pass `learnerId` to DepositButton

### 3. DepositButton Component (`components/deposit/DepositButton.tsx`)

**Changes:**
- ✅ `childId` prop → `learnerId` prop
- ✅ Sends `learnerId` to create-checkout API
- ✅ Updated validation to check `learnerId`

### 4. Create Checkout Route (`app/api/deposits/create-checkout/route.ts`)

**Changes:**
- ✅ `childId` → `learnerId` in request body
- ✅ Stripe metadata uses `learner_id` instead of `child_id`
- ✅ Updated validation and error messages

### 5. Stripe Webhook (`app/api/webhooks/stripe/route.ts`)

**Changes:**
- ✅ Reads `learner_id` from Stripe metadata
- ✅ Sends `learner_id` to backend deposit confirmation API

---

## API Integration

### New Endpoint Used

**GET `/api/users/me/children`**
- Fetches all children for authenticated parent
- Returns: `[{ id, name, age, email }, ...]`
- Requires: `user_id` query parameter

**Example:**
```typescript
const response = await axios.get(
  `${API_BASE}/api/users/me/children`,
  { params: { user_id: user.id } }
)
setChildren(response.data)
```

---

## User Flow Updates

### Before:
1. User signs up
2. Dashboard uses hardcoded `'temp-child-id'`
3. Deposit uses `childId` parameter

### After:
1. User signs up → completes onboarding
2. Dashboard fetches real children from API
3. User selects child (if multiple)
4. Deposit uses `learnerId` from selected child
5. All API calls use `learner_id`

---

## Breaking Changes

### Component Props

**DepositForm:**
```diff
- <DepositForm childId={childId} userId={userId} />
+ <DepositForm learnerId={learnerId} userId={userId} />
```

**DepositButton:**
```diff
- <DepositButton childId={childId} userId={userId} amount={1000} />
+ <DepositButton learnerId={learnerId} userId={userId} amount={1000} />
```

### API Calls

**Create Checkout:**
```diff
- { amount, childId, userId }
+ { amount, learnerId, userId }
```

**Stripe Metadata:**
```diff
- metadata: { child_id: ..., user_id: ... }
+ metadata: { learner_id: ..., user_id: ... }
```

---

## Error Handling

### No Children
- Shows message: "您還沒有建立任何孩子的帳戶。"
- Suggests creating child account in settings

### API Errors
- Logs errors to console
- Doesn't break UI if fetch fails
- Gracefully handles non-parent users

---

## Testing Checklist

- [ ] Dashboard loads children from API
- [ ] Child selector appears when multiple children
- [ ] Deposit form works with selected child
- [ ] Stripe checkout creates session with learner_id
- [ ] Webhook confirms deposit with learner_id
- [ ] Error handling works for no children
- [ ] Error handling works for API failures

---

## Migration Notes

### For Developers

1. **Update all `childId` references to `learnerId`**
2. **Use `/api/users/me/children` to fetch children**
3. **Update Stripe metadata to use `learner_id`**
4. **Test with multiple children scenario**

### For Users

- No visible changes (same UI/UX)
- Better data accuracy (real children from database)
- Can select child if multiple children

---

## Next Steps

1. ✅ All components updated
2. ⏳ Test end-to-end flow
3. ⏳ Add child creation UI (if needed)
4. ⏳ Add balance display from API
5. ⏳ Add withdrawal functionality UI

---

**Status:** ✅ All frontend components updated and ready for testing

