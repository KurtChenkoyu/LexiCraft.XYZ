# Deployment Checklist
## Unified User Model - Pre-Launch Checklist

**Date:** 2024  
**Status:** Pre-Deployment

---

## Pre-Deployment Checklist

### 1. Database Setup ✅

- [ ] **Backup existing database** (if any data exists)
- [ ] **Run Migration 007** in Supabase SQL Editor
  - File: `backend/migrations/007_unified_user_model.sql`
  - Verify: All tables created successfully
- [ ] **Run Migration 008** in Supabase SQL Editor
  - File: `backend/migrations/008_update_trigger_for_roles.sql`
  - Verify: Trigger function updated
- [ ] **Verify trigger works**
  - Test: Sign up a new user
  - Check: User created in `public.users`
  - Check: 'learner' role assigned automatically

**Verification Queries:**
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'user_roles', 'user_relationships');

-- Check trigger exists
SELECT trigger_name FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';
```

---

### 2. Environment Variables

#### Backend
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `NEO4J_URI` - Neo4j connection (for vocabulary graph)
- [ ] `NEO4J_USER` - Neo4j username
- [ ] `NEO4J_PASSWORD` - Neo4j password
- [ ] `BACKEND_URL` - Backend API URL (for webhooks)

#### Frontend
- [ ] `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key
- [ ] `NEXT_PUBLIC_API_URL` - Backend API URL
- [ ] `STRIPE_SECRET_KEY` - Stripe secret key (for deposits)
- [ ] `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret

#### Supabase
- [ ] Supabase project created
- [ ] Database connected
- [ ] Auth providers configured (Google OAuth, Email)
- [ ] Email templates configured (if using email auth)

---

### 3. Backend Deployment

- [ ] **Code deployed** to production server
- [ ] **Dependencies installed**
  ```bash
  pip install -r requirements.txt
  ```
- [ ] **Environment variables set**
- [ ] **API server running**
  - Test: `GET /health` returns 200
- [ ] **CORS configured** for frontend domain
- [ ] **Database connection working**
- [ ] **Neo4j connection working**

**Test Endpoints:**
```bash
# Health check
curl https://api.lexicraft.xyz/health

# Test onboarding status (will fail without auth, but should return 401, not 500)
curl https://api.lexicraft.xyz/api/users/onboarding/status?user_id=test
```

---

### 4. Frontend Deployment

- [ ] **Code deployed** to hosting (Vercel/Netlify/etc.)
- [ ] **Environment variables set** in hosting platform
- [ ] **Build successful** (no errors)
- [ ] **Supabase client configured**
- [ ] **API URL configured** correctly

**Test Pages:**
- [ ] `/` - Landing page loads
- [ ] `/signup` - Signup page loads
- [ ] `/login` - Login page loads
- [ ] `/onboarding` - Onboarding page loads (redirects if not authenticated)
- [ ] `/dashboard` - Dashboard loads (redirects if not authenticated)

---

### 5. Integration Testing

#### Signup Flow
- [ ] **Email signup works**
  - User can sign up with email/password
  - User created in Supabase Auth
  - User created in `public.users` (via trigger)
  - Redirected to `/onboarding`

- [ ] **Google OAuth works**
  - User can sign up with Google
  - OAuth callback works
  - User created in database
  - Redirected to `/onboarding`

#### Onboarding Flow
- [ ] **Parent account creation**
  - Can select "家長帳戶"
  - Can enter parent age
  - Can create child account
  - Roles assigned correctly
  - Redirected to `/dashboard`

- [ ] **Learner account creation**
  - Can select "學習者帳戶"
  - Can enter age
  - Role assigned correctly
  - Redirected to `/dashboard`

- [ ] **Both account creation**
  - Can select "家長 + 學習者"
  - Can enter both ages
  - Both roles assigned
  - Redirected to `/dashboard`

#### Dashboard Flow
- [ ] **Children load from API**
  - Dashboard fetches children
  - Children displayed correctly
  - Child selector works (if multiple)

- [ ] **Deposit flow**
  - Can select deposit amount
  - Stripe checkout created
  - Payment redirects correctly
  - Webhook confirms deposit
  - Points account updated

---

### 6. Error Handling

- [ ] **404 errors** handled gracefully
- [ ] **401 errors** redirect to login
- [ ] **403 errors** show appropriate message
- [ ] **500 errors** show user-friendly message
- [ ] **Network errors** handled in frontend
- [ ] **Validation errors** displayed clearly

---

### 7. Security

- [ ] **CORS configured** correctly (not `*` in production)
- [ ] **Environment variables** not exposed in frontend
- [ ] **API keys** secured (not in code)
- [ ] **Supabase RLS policies** configured (if using)
- [ ] **SQL injection** prevented (using parameterized queries)
- [ ] **XSS protection** in place
- [ ] **HTTPS** enabled (required for OAuth)

---

### 8. Monitoring & Logging

- [ ] **Error logging** configured
  - Backend: Log errors to console/file/service
  - Frontend: Log errors to console/analytics
- [ ] **Analytics** configured (if using)
- [ ] **Uptime monitoring** set up (if using)
- [ ] **Database monitoring** set up (Supabase dashboard)

---

### 9. Documentation

- [ ] **API documentation** available (if using OpenAPI/Swagger)
- [ ] **Environment setup** documented
- [ ] **Deployment process** documented
- [ ] **Troubleshooting guide** available

---

### 10. Rollback Plan

- [ ] **Database backup** created before migration
- [ ] **Code version** tagged in git
- [ ] **Rollback procedure** documented
- [ ] **Previous version** can be deployed quickly

---

## Post-Deployment Verification

### Day 1 Checks

- [ ] **Monitor error logs** for any issues
- [ ] **Check user signups** - Are users being created?
- [ ] **Check onboarding** - Are users completing onboarding?
- [ ] **Check database** - Are relationships being created?
- [ ] **Test deposits** - Do payments work?
- [ ] **Check webhooks** - Are Stripe webhooks being received?

### Week 1 Checks

- [ ] **User feedback** collected
- [ ] **Performance metrics** reviewed
- [ ] **Error rates** monitored
- [ ] **Database performance** checked
- [ ] **API response times** acceptable

---

## Common Issues & Solutions

### Issue: Users not created in database

**Symptoms:** User signs up but not in `public.users`

**Solutions:**
1. Check trigger exists: `SELECT * FROM information_schema.triggers WHERE trigger_name = 'on_auth_user_created'`
2. Check function exists: `SELECT routine_name FROM information_schema.routines WHERE routine_name = 'handle_new_user'`
3. Check Supabase logs for errors
4. Verify RLS policies allow insert

### Issue: Onboarding redirect loop

**Symptoms:** User keeps getting redirected to `/onboarding`

**Solutions:**
1. Check onboarding status API: `GET /api/users/onboarding/status?user_id=...`
2. Verify user has age set
3. Verify user has at least one role
4. Check browser console for errors

### Issue: Children not loading

**Symptoms:** Dashboard shows loading forever

**Solutions:**
1. Check API endpoint: `GET /api/users/me/children?user_id=...`
2. Verify user has 'parent' role
3. Check browser network tab for API errors
4. Verify `user_id` is being passed correctly

### Issue: Stripe webhook not working

**Symptoms:** Payment succeeds but points not credited

**Solutions:**
1. Check Stripe webhook logs
2. Verify webhook secret is correct
3. Check backend logs for webhook processing
4. Verify webhook endpoint is accessible
5. Check database for deposit confirmation

---

## Quick Deployment Commands

### Backend
```bash
# Deploy to production
git push production main

# Or if using Docker
docker build -t lexicraft-api .
docker push lexicraft-api:latest

# Or if using cloud platform
# (Follow platform-specific instructions)
```

### Frontend
```bash
# Deploy to Vercel
vercel --prod

# Or if using Netlify
netlify deploy --prod

# Or if using other platform
# (Follow platform-specific instructions)
```

---

## Environment-Specific Notes

### Development
- Use local database
- Use local API (`http://localhost:8000`)
- Use test Stripe keys
- Enable debug logging

### Staging
- Use staging database
- Use staging API URL
- Use test Stripe keys
- Enable error logging

### Production
- Use production database
- Use production API URL
- Use live Stripe keys
- Enable error logging + monitoring
- Disable debug logging

---

## Success Criteria

✅ **Deployment is successful when:**
1. All migrations run without errors
2. Users can sign up successfully
3. Users can complete onboarding
4. Dashboard loads and displays children
5. Deposit flow works end-to-end
6. No critical errors in logs
7. API response times < 500ms
8. Frontend loads < 3 seconds

---

## Emergency Contacts

- **Database Issues:** [Your DBA/DevOps contact]
- **API Issues:** [Your Backend Developer]
- **Frontend Issues:** [Your Frontend Developer]
- **Stripe Issues:** Stripe Support
- **Supabase Issues:** Supabase Support

---

**Status:** Ready for deployment when checklist is complete

