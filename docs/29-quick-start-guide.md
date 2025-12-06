# Quick Start Guide
## Getting LexiCraft Running Locally

**Date:** 2024  
**Status:** Development Setup

---

## Prerequisites

- ✅ Python 3.9+ installed
- ✅ Node.js 18+ installed
- ✅ PostgreSQL database (via Supabase)
- ✅ Neo4j database (for vocabulary graph)
- ✅ Supabase account
- ✅ Stripe account (for payments)

---

## Step 1: Clone & Setup

```bash
# Clone repository
git clone <your-repo-url>
cd LexiCraft-AG

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../landing-page
npm install
```

---

## Step 2: Environment Variables

### Backend (`.env` or environment)

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# API
BACKEND_URL=http://localhost:8000
```

### Frontend (`.env.local`)

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe (for deposits)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## Step 3: Database Setup

### 3.1 Supabase Setup

1. **Create Supabase project**
   - Go to https://supabase.com
   - Create new project
   - Note your project URL and anon key

2. **Run Migrations**
   - Open Supabase SQL Editor
   - Run `backend/migrations/007_unified_user_model.sql`
   - Run `backend/migrations/008_update_trigger_for_roles.sql`

3. **Configure Auth**
   - Enable Email provider
   - Enable Google OAuth (optional)
   - Set redirect URLs: `http://localhost:3000/**`

### 3.2 Neo4j Setup

1. **Install Neo4j** (or use Neo4j Aura)
2. **Create database**
3. **Load vocabulary graph** (if you have data)
4. **Note connection details**

---

## Step 4: Run Backend

```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Verify:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok", "version": "7.1"}
```

---

## Step 5: Run Frontend

```bash
cd landing-page
npm run dev
```

**Verify:**
- Open http://localhost:3000
- Should see landing page

---

## Step 6: Test Signup Flow

1. **Go to** http://localhost:3000/signup
2. **Sign up** with email or Google
3. **Should redirect** to `/onboarding`
4. **Complete onboarding:**
   - Select account type
   - Enter age
   - (Optional) Create child account
5. **Should redirect** to `/dashboard`

**Verify in Database:**
```sql
-- Check user created
SELECT id, email, name, age FROM users ORDER BY created_at DESC LIMIT 1;

-- Check role assigned
SELECT ur.role, u.email 
FROM user_roles ur 
JOIN users u ON ur.user_id = u.id 
ORDER BY ur.created_at DESC LIMIT 1;

-- Should show role = 'learner' (or 'parent' if parent account)
```

---

## Step 7: Test Dashboard

1. **Login** to dashboard
2. **Should see:**
   - Children list (if parent)
   - Deposit form
   - Balance card

**Verify API:**
```bash
# Get children (replace USER_ID)
curl "http://localhost:8000/api/users/me/children?user_id=USER_ID"
```

---

## Common Issues

### Backend won't start

**Check:**
- Database connection: `DATABASE_URL` correct?
- Neo4j connection: `NEO4J_URI` correct?
- Port 8000 available?

**Solution:**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Test Neo4j connection
# (Use Neo4j browser or cypher-shell)
```

### Frontend won't start

**Check:**
- Node modules installed: `npm install`
- Environment variables set
- Port 3000 available?

**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

### Signup doesn't create user

**Check:**
- Supabase configured correctly?
- Trigger exists?
- RLS policies allow insert?

**Solution:**
```sql
-- Check trigger
SELECT * FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- Check function
SELECT routine_name FROM information_schema.routines 
WHERE routine_name = 'handle_new_user';
```

### Onboarding redirect loop

**Check:**
- User has age set?
- User has role?
- API endpoint working?

**Solution:**
```bash
# Check onboarding status
curl "http://localhost:8000/api/users/onboarding/status?user_id=USER_ID"
```

---

## Development Workflow

### Making Changes

1. **Backend changes:**
   ```bash
   cd backend
   # Make changes
   # Backend auto-reloads (if using --reload)
   ```

2. **Frontend changes:**
   ```bash
   cd landing-page
   # Make changes
   # Frontend auto-reloads (Next.js hot reload)
   ```

3. **Database changes:**
   - Create new migration file
   - Run in Supabase SQL Editor
   - Update SQLAlchemy models

### Testing Changes

1. **Test locally** first
2. **Check browser console** for errors
3. **Check backend logs** for errors
4. **Test full flow** (signup → onboarding → dashboard)

---

## Useful Commands

### Backend
```bash
# Run backend
uvicorn src.main:app --reload

# Run with specific port
uvicorn src.main:app --reload --port 8001

# Check API docs
# Open: http://localhost:8000/docs
```

### Frontend
```bash
# Run frontend
npm run dev

# Build for production
npm run build

# Run production build locally
npm start
```

### Database
```sql
-- Check users
SELECT id, email, name, age FROM users;

-- Check roles
SELECT u.email, ur.role 
FROM users u 
JOIN user_roles ur ON u.id = ur.user_id;

-- Check relationships
SELECT 
  u1.email as from_user,
  u2.email as to_user,
  ur.relationship_type
FROM user_relationships ur
JOIN users u1 ON ur.from_user_id = u1.id
JOIN users u2 ON ur.to_user_id = u2.id;
```

---

## Next Steps

1. ✅ **Setup complete** - You're ready to develop!
2. ⏳ **Add features** - Build new functionality
3. ⏳ **Test thoroughly** - Use testing guide
4. ⏳ **Deploy** - Follow deployment checklist

---

## Getting Help

- **Documentation:** Check `docs/` folder
- **API Docs:** http://localhost:8000/docs (when backend running)
- **Supabase Docs:** https://supabase.com/docs
- **Next.js Docs:** https://nextjs.org/docs

---

**Status:** Ready for development! 🚀

