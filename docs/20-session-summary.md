# Session Summary: Unified User Model & Relationship Ecosystem Design
## Context & Decisions Made

**Date:** 2024  
**Session Focus:** User model redesign, signup flow, relationship ecosystem

---

## Key Decisions Made

### 1. Unified User Model ✅

**Decision:** Everyone is a `user` - roles are attributes, not separate entities.

**Before:**
- Separate `users` (parents) and `children` tables
- Children couldn't be users
- Rigid parent-child model

**After:**
- Single `users` table
- `user_roles` table for RBAC
- `user_relationships` table for all relationships
- Flexible: user can be parent AND learner

**Status:** ✅ Schema designed, migration created, models updated, CRUD updated

---

### 2. Placeholder Email for Child Accounts ✅

**Decision:** Use placeholder emails (`child-{uuid}@lexicraft.xyz`) for MVP.

**Why:**
- No email infrastructure needed
- No UNIQUE constraint violations
- Simple to implement
- Can upgrade to real emails later

**Alternative Considered:** Real email accounts (too complex/costly for MVP)

**Status:** ✅ Design complete, ready to implement

---

### 3. Comprehensive Relationship Ecosystem ✅

**Decision:** Generic `user_relationships` table supporting multiple relationship types.

**Relationship Types:**
- `parent_child` - Legal guardian
- `coach_student` - Teaching relationship (adult or peer)
- `sibling` - Siblings learning together
- `friend` - Friends studying together
- `classmate` - Students in same class
- `tutor_student` - Professional tutoring

**Key Innovation:** Support kids coaching kids (with parent approval)

**Status:** ✅ Design documented, schema designed

---

### 4. Signup Flow Design ✅

**Decision:** Progressive onboarding after authentication.

**Flow:**
1. Signup (Google OAuth or Email) → User created
2. Onboarding: "Who is this account for?"
   - For my child
   - For myself
   - Both
3. Collect necessary info (age, child info, etc.)
4. Assign roles and create relationships
5. Redirect to dashboard

**Status:** ✅ Design complete, ready to implement

---

## Current State

### Completed ✅

1. **Database Schema:**
   - Migration `007_unified_user_model.sql` created
   - Unified `users` table with `age` field
   - `user_roles` table for RBAC
   - `user_relationships` table designed (not yet in migration)

2. **SQLAlchemy Models:**
   - Removed `Child` model
   - Added `UserRole` model
   - Added `ParentChildRelationship` model
   - Updated all models to use `user_id` instead of `child_id`

3. **CRUD Functions:**
   - Updated all CRUD to use `user_id`
   - Added role management functions
   - Added relationship management functions

4. **Documentation:**
   - `docs/18-signup-flow-design.md` - Signup flow design
   - `docs/19-relationship-ecosystem-design.md` - Relationship ecosystem
   - `backend/UNIFIED_USER_MODEL_MIGRATION.md` - Migration guide

### Pending ⏳

1. **Database Migration:**
   - Run `007_unified_user_model.sql` (fresh start)
   - Update trigger to assign default role

2. **API Endpoints:**
   - Create onboarding endpoint
   - Update deposits/withdrawals to use new model
   - Add relationship management endpoints

3. **Frontend:**
   - Build onboarding wizard
   - Update signup flow
   - Update dashboard for new model

4. **Schema Update:**
   - Replace `parent_child_relationships` with `user_relationships` (Phase 2)

---

## Architecture Decisions

### User Model

```
users (everyone)
  ├── user_roles (RBAC)
  │   └── 'parent', 'learner', 'coach', 'tutor', 'admin'
  └── user_relationships (all relationships)
      ├── parent_child
      ├── coach_student
      ├── sibling
      ├── friend
      ├── classmate
      └── tutor_student
```

### Data Flow

```
Signup → Auth (Supabase) → Trigger creates user → Onboarding → Roles assigned → Relationships created
```

### Email Strategy

**MVP:** Placeholder emails (`child-{uuid}@lexicraft.xyz`)  
**Future:** Real email accounts (if needed)

---

## Key Files

### Database
- `backend/migrations/007_unified_user_model.sql` - Main migration
- `backend/src/database/models.py` - Updated models
- `backend/src/database/postgres_crud/users.py` - Updated CRUD

### Documentation
- `docs/18-signup-flow-design.md` - Signup flow
- `docs/19-relationship-ecosystem-design.md` - Relationships
- `backend/UNIFIED_USER_MODEL_MIGRATION.md` - Migration guide

---

## Next Implementation Steps

1. **Run Migration:**
   ```bash
   # In Supabase SQL Editor
   # Run: backend/migrations/007_unified_user_model.sql
   ```

2. **Update Trigger:**
   - Update `handle_new_user()` to assign default 'learner' role

3. **Create Onboarding API:**
   - `backend/src/api/onboarding.py`
   - Endpoint: `POST /api/users/onboarding/complete`

4. **Build Onboarding UI:**
   - `landing-page/app/[locale]/onboarding/page.tsx`
   - Multi-step wizard

5. **Update Signup Flow:**
   - Redirect to `/onboarding` instead of `/dashboard`

---

## Open Questions

1. **Child Email:** Placeholder confirmed ✅
2. **Coaching Rewards:** TBD (10-20% recommended)
3. **Age Limits for Coaching:** TBD (no hard limit, parent approval required)
4. **Multiple Children:** Phase 2 feature
5. **Email Infrastructure:** Phase 2 (if needed)

---

## Industry Alignment

✅ **Unified user model** - Matches Duolingo, Khan Academy  
✅ **RBAC** - Industry standard  
✅ **Flexible relationships** - Similar to ClassDojo  
✅ **Parent approval** - COPPA compliant  
✅ **Peer coaching** - Innovative (not common in industry)

---

**Status:** Design complete, ready for implementation

