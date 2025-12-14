# Survey Page Fix - Authentication & API Configuration

## Problem
After registering, users were redirected back to the landing page, and when trying to access the survey, it failed with "SURVEY INITIALIZATION FAILED".

## Root Causes

1. **Missing Authentication Check**: The survey page didn't verify if the user was authenticated or had completed onboarding.
2. **Missing User ID**: The survey API wasn't receiving the user ID, which is needed for tracking progress.
3. **API URL Configuration**: In production (Vercel), the `NEXT_PUBLIC_API_URL` environment variable might not be set, causing the app to try connecting to `localhost:8000` which won't work.

## Fixes Applied

### 1. Added Authentication & Onboarding Checks to Survey Page

**File**: `landing-page/app/[locale]/survey/page.tsx`

- Added `useAuth` hook to check if user is authenticated
- Added `checkOnboardingStatus` to verify onboarding completion
- Redirects to login if not authenticated
- Redirects to onboarding if onboarding not completed
- Passes `userId` to `SurveyEngine` component

### 2. Updated SurveyEngine to Accept and Use User ID

**File**: `landing-page/components/survey/SurveyEngine.tsx`

- Added `userId` prop to `SurveyEngineProps` interface
- Passes `userId` to `surveyApi.start()` call
- Improved error handling with more detailed logging
- Enhanced error display to show API URL and configuration status

### 3. Improved Error Messages

The error screen now shows:
- Selected CEFR Level
- Calibration status
- User ID
- API URL being used
- Warning if using localhost in production

## Required Configuration

### For Production (Vercel)

You **must** set the `NEXT_PUBLIC_API_URL` environment variable in Vercel:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add:
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://api.lexicraft.xyz  (or your backend URL)
   Environment: Production, Preview, Development
   ```
3. Redeploy the application

### For Local Development

If running locally, ensure:
- Backend is running on `http://localhost:8000`
- Or set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`

## Testing Checklist

After deploying the fix:

- [ ] Register a new user
- [ ] Verify redirect to `/onboarding` after signup
- [ ] Complete onboarding
- [ ] Verify redirect to `/dashboard` after onboarding
- [ ] Navigate to `/survey`
- [ ] Verify survey starts successfully
- [ ] Check browser console for any errors
- [ ] Verify user ID is being passed to API

## Expected Flow

1. **Signup** → Creates user in database (via Supabase trigger)
2. **Auth Callback** → Checks onboarding status → Redirects to `/onboarding` if incomplete
3. **Onboarding** → Collects user info, assigns roles → Redirects to `/dashboard`
4. **Survey** → Checks auth & onboarding → Starts survey with user ID

## Troubleshooting

### Survey Still Fails

1. **Check Browser Console**:
   - Look for API errors
   - Verify API URL is correct (not localhost in production)
   - Check if user ID is present

2. **Check Network Tab**:
   - Verify API request is being made
   - Check response status code
   - Look for CORS errors

3. **Verify Backend**:
   - Ensure backend is running and accessible
   - Test `/health` endpoint
   - Verify `/api/v1/survey/start` endpoint works

4. **Check Environment Variables**:
   - Verify `NEXT_PUBLIC_API_URL` is set in Vercel
   - Ensure it's deployed (not just saved)
   - Check if variable is available in the correct environment

### User Not Redirected to Onboarding

1. Check Supabase trigger `handle_new_user()` is working
2. Verify `user_roles` table has entry for new user
3. Check `checkOnboardingStatus` API endpoint is working
4. Verify user has `age` set (indicates onboarding completion)

## Files Changed

- `landing-page/app/[locale]/survey/page.tsx` - Added auth/onboarding checks
- `landing-page/components/survey/SurveyEngine.tsx` - Added userId prop and improved error handling

## Next Steps

1. Deploy to Vercel with `NEXT_PUBLIC_API_URL` environment variable set
2. Test the complete flow end-to-end
3. Monitor error logs for any remaining issues

