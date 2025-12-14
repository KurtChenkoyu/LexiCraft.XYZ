# Frontend-Backend Connection Audit

## Summary
Full audit of all API connections between frontend (Next.js) and backend (FastAPI).

---

## ✅ WORKING CONNECTIONS

### 1. User Management APIs
| Frontend Call | Backend Endpoint | Status |
|--------------|------------------|--------|
| `authenticatedGet('/api/users/me')` | `GET /api/users/me` | ✅ Works |
| `authenticatedGet('/api/users/me/children')` | `GET /api/users/me/children` | ✅ Works |
| `authenticatedPost('/api/users/children')` | `POST /api/users/children` | ✅ Works |

### 2. Onboarding APIs
| Frontend Call | Backend Endpoint | Status |
|--------------|------------------|--------|
| `authenticatedPost('/api/users/onboarding/complete')` | `POST /api/users/onboarding/complete` | ✅ Works |
| `authenticatedGet('/api/users/onboarding/status')` | `GET /api/users/onboarding/status` | ✅ Works |

### 3. Survey APIs
| Frontend Call | Backend Endpoint | Status |
|--------------|------------------|--------|
| `axios.post('${API_BASE}/start')` | `POST /api/v1/survey/start` | ✅ Works (no auth) |
| `axios.post('${API_BASE}/next')` | `POST /api/v1/survey/next` | ✅ Works (no auth) |

### 4. Deposit APIs (Next.js API Routes)
| Frontend Call | Handled By | Status |
|--------------|------------|--------|
| `fetch('/api/deposits/create-checkout')` | Next.js route | ✅ Works |
| Stripe webhook | `app/api/webhooks/stripe/route.ts` | ✅ Works |

---

## ❌ ISSUES FOUND

### Issue 1: Survey Not Linked to User
**Problem**: Survey results are not saved to user profile
**Location**: `surveyApi.ts` uses anonymous user ID
**Fix**: Pass authenticated user ID to survey

### Issue 2: Balance Display Hardcoded
**Problem**: Dashboard shows `NT$ 0` always
**Location**: `dashboard/page.tsx` line 395
**Fix**: Fetch real balance from backend

### Issue 3: Stripe Redirect Missing Locale
**Problem**: Redirect URLs don't include locale prefix
**Location**: `app/api/deposits/create-checkout/route.ts`
**Fix**: Include locale in redirect URLs

### Issue 4: No Loading States for API Errors
**Problem**: API timeouts show loading spinner forever
**Status**: Already fixed with timeout handling

---

## ACTION ITEMS

1. [x] Supabase client singleton (DONE)
2. [x] Add balance fetching to dashboard (DONE)
3. [x] Survey already uses authenticated user (VERIFIED)
4. [x] Add locale to Stripe redirect URLs (DONE)
5. [ ] Test complete user flow

---

## API Routes Summary

### Backend (FastAPI at localhost:8000)
```
/health                              GET     Health check
/api/v1/survey/start                 POST    Start survey
/api/v1/survey/next                  POST    Submit answer
/api/users/me                        GET     Get current user (auth required)
/api/users/me/children               GET     Get children (auth required)
/api/users/children                  POST    Create child (auth required)
/api/users/onboarding/status         GET     Check onboarding (auth required)
/api/users/onboarding/complete       POST    Complete onboarding (auth required)
/api/deposits/confirm                POST    Confirm deposit (webhook)
/api/deposits/{learner_id}/balance   GET     Get balance
```

### Frontend (Next.js API Routes)
```
/api/deposits/create-checkout        POST    Create Stripe session
/api/webhooks/stripe                 POST    Stripe webhook
/api/waitlist                        POST    Join waitlist
```

