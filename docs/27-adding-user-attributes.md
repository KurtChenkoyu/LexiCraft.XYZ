# Adding User Attributes Later
## Easy Schema Extensions in PostgreSQL

**Date:** 2024  
**Status:** Reference Guide

---

## ✅ Good News: It's Very Easy!

PostgreSQL makes adding columns to existing tables **extremely simple**. Unlike graph databases where you might need to restructure relationships, relational databases allow you to add columns with a simple `ALTER TABLE` statement.

---

## Current Users Table

```sql
users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    name TEXT,
    phone TEXT,
    country TEXT DEFAULT 'TW',
    age INTEGER,
    email_confirmed BOOLEAN DEFAULT FALSE,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## How to Add Attributes Later

### Method 1: Simple ALTER TABLE (Recommended)

```sql
-- Add a single column
ALTER TABLE users 
ADD COLUMN avatar_url TEXT;

-- Add multiple columns at once
ALTER TABLE users 
ADD COLUMN timezone TEXT DEFAULT 'Asia/Taipei',
ADD COLUMN language TEXT DEFAULT 'zh-TW',
ADD COLUMN last_login TIMESTAMP;

-- Add with constraints
ALTER TABLE users 
ADD COLUMN status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended'));
```

**That's it!** No downtime, no data loss, works on existing data.

### Method 2: Using JSONB for Flexible Attributes

For attributes that might vary or you're not sure about yet:

```sql
-- Add a JSONB column for flexible metadata
ALTER TABLE users 
ADD COLUMN preferences JSONB DEFAULT '{}';

-- Then you can store anything:
-- preferences: {"theme": "dark", "notifications": true, "cefr_level": "B1"}
-- preferences: {"school": "Taipei Elementary", "grade": 5}
```

**Benefits:**
- ✅ No schema changes needed for new preferences
- ✅ Can query JSONB efficiently in PostgreSQL
- ✅ Flexible for different user types

**Example Usage:**
```sql
-- Store preferences
UPDATE users 
SET preferences = jsonb_set(
    preferences, 
    '{theme}', 
    '"dark"'
) 
WHERE id = '...';

-- Query preferences
SELECT * FROM users 
WHERE preferences->>'theme' = 'dark';
```

---

## Common Attributes You Might Want

### Profile & Display
```sql
ALTER TABLE users 
ADD COLUMN avatar_url TEXT,
ADD COLUMN bio TEXT,
ADD COLUMN display_name TEXT;  -- Different from legal name
```

### Localization
```sql
ALTER TABLE users 
ADD COLUMN timezone TEXT DEFAULT 'Asia/Taipei',
ADD COLUMN language TEXT DEFAULT 'zh-TW',
ADD COLUMN locale TEXT DEFAULT 'zh-TW';
```

### Activity Tracking
```sql
ALTER TABLE users 
ADD COLUMN last_login TIMESTAMP,
ADD COLUMN last_active TIMESTAMP,
ADD COLUMN login_count INTEGER DEFAULT 0;
```

### Status & Flags
```sql
ALTER TABLE users 
ADD COLUMN status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'banned')),
ADD COLUMN is_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN is_premium BOOLEAN DEFAULT FALSE;
```

### Preferences (JSONB - Recommended)
```sql
ALTER TABLE users 
ADD COLUMN preferences JSONB DEFAULT '{}';

-- Can store:
-- {
--   "notifications": {"email": true, "push": false},
--   "theme": "dark",
--   "cefr_level": "B1",
--   "learning_goals": ["vocabulary", "grammar"],
--   "daily_target": 50
-- }
```

### Education (for learners)
```sql
ALTER TABLE users 
ADD COLUMN school_name TEXT,
ADD COLUMN grade_level INTEGER,
ADD COLUMN education_level TEXT;  -- 'elementary', 'middle', 'high', 'university'
```

### Social
```sql
ALTER TABLE users 
ADD COLUMN social_links JSONB DEFAULT '{}';
-- {"twitter": "@username", "instagram": "@handle"}
```

---

## Migration Pattern

When you need to add attributes, create a migration file:

**File:** `backend/migrations/009_add_user_attributes.sql`

```sql
-- Migration: Add User Attributes
-- Created: 2024
-- Description: Add common user attributes

-- Add profile attributes
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'Asia/Taipei',
ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'zh-TW';

-- Add activity tracking
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_active TIMESTAMP;

-- Add preferences (flexible JSONB)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';

-- Add indexes if needed
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status) WHERE status IS NOT NULL;

-- Update existing users with defaults if needed
UPDATE users 
SET preferences = '{}' 
WHERE preferences IS NULL;
```

Then update your SQLAlchemy model:

```python
# backend/src/database/models.py

class User(Base, BaseModel):
    # ... existing fields ...
    
    # New attributes
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(Text, default='Asia/Taipei')
    language = Column(Text, default='zh-TW')
    last_login = Column(DateTime, nullable=True)
    last_active = Column(DateTime, nullable=True)
    preferences = Column(JSONB, default={})  # Flexible preferences
```

---

## Best Practices

### 1. Use NULL for Optional Attributes
```sql
-- Good: NULL means "not set"
ALTER TABLE users ADD COLUMN avatar_url TEXT;

-- Avoid: Using empty strings or special values
-- Bad: avatar_url TEXT DEFAULT ''  -- Hard to distinguish from "not set"
```

### 2. Use JSONB for Flexible/Unknown Attributes
```sql
-- If you're not sure what attributes you'll need:
ALTER TABLE users ADD COLUMN metadata JSONB DEFAULT '{}';

-- Store anything:
-- metadata: {"favorite_color": "blue", "hobbies": ["reading", "coding"]}
```

### 3. Add Indexes for Frequently Queried Attributes
```sql
-- If you'll query by status often:
CREATE INDEX idx_users_status ON users(status);

-- If you'll query by last_login:
CREATE INDEX idx_users_last_login ON users(last_login);
```

### 4. Use CHECK Constraints for Enums
```sql
-- Instead of just TEXT, use CHECK constraint:
ALTER TABLE users 
ADD COLUMN status TEXT DEFAULT 'active' 
CHECK (status IN ('active', 'inactive', 'suspended'));
```

### 5. Set Sensible Defaults
```sql
-- Good defaults for new columns:
ALTER TABLE users 
ADD COLUMN timezone TEXT DEFAULT 'Asia/Taipei',
ADD COLUMN language TEXT DEFAULT 'zh-TW',
ADD COLUMN preferences JSONB DEFAULT '{}';
```

---

## Performance Considerations

### Adding Columns is Fast
- ✅ Adding a column to a table with millions of rows is still fast
- ✅ PostgreSQL doesn't rewrite the table (for most column types)
- ✅ No downtime required
- ✅ Existing queries continue to work

### When to Be Careful
- ⚠️ Adding NOT NULL columns without defaults requires data migration
- ⚠️ Adding indexes on large tables can take time (but doesn't block reads)
- ⚠️ Very wide tables (100+ columns) can impact performance

### Best Approach
```sql
-- Step 1: Add column as nullable
ALTER TABLE users ADD COLUMN new_attribute TEXT;

-- Step 2: Backfill data (if needed)
UPDATE users SET new_attribute = 'default_value' WHERE new_attribute IS NULL;

-- Step 3: Add NOT NULL constraint (if needed)
ALTER TABLE users ALTER COLUMN new_attribute SET NOT NULL;
```

---

## Example: Adding User Preferences

### Step 1: Create Migration
```sql
-- backend/migrations/009_add_user_preferences.sql
ALTER TABLE users 
ADD COLUMN preferences JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_users_preferences ON users USING GIN (preferences);
```

### Step 2: Update Model
```python
# backend/src/database/models.py
from sqlalchemy.dialects.postgresql import JSONB

class User(Base, BaseModel):
    # ... existing fields ...
    preferences = Column(JSONB, default={})
```

### Step 3: Update CRUD (Optional)
```python
# backend/src/database/postgres_crud/users.py

def update_user_preferences(
    session: Session,
    user_id: UUID,
    preferences: dict
) -> Optional[User]:
    """Update user preferences."""
    user = get_user_by_id(session, user_id)
    if not user:
        return None
    
    # Merge with existing preferences
    current = user.preferences or {}
    user.preferences = {**current, **preferences}
    
    session.commit()
    session.refresh(user)
    return user
```

### Step 4: Use in API
```python
# backend/src/api/users.py

@router.patch("/me/preferences")
async def update_preferences(
    preferences: dict,
    user_id: str = Query(...),
    db: Session = Depends(get_db_session)
):
    user = user_crud.update_user_preferences(db, UUID(user_id), preferences)
    return {"preferences": user.preferences}
```

---

## Comparison: Relational vs Graph Database

### Relational Database (PostgreSQL) ✅
- ✅ Easy to add columns: `ALTER TABLE users ADD COLUMN ...`
- ✅ No restructuring needed
- ✅ Works with existing data
- ✅ Fast and efficient
- ✅ Well-supported by ORMs

### Graph Database (Neo4j) ⚠️
- ⚠️ Properties are more flexible (no schema)
- ⚠️ But relationships are harder to change
- ⚠️ Different query language
- ⚠️ Less common in web apps

**For LexiCraft:** PostgreSQL is perfect! You can add attributes anytime.

---

## Recommended Approach for LexiCraft

### Phase 1: MVP (Current)
Keep it simple:
- ✅ Basic attributes: name, email, age, country
- ✅ No extra attributes needed yet

### Phase 2: Add as Needed
When you need an attribute:
1. Create migration: `009_add_<attribute>.sql`
2. Update model
3. Update API if needed
4. Deploy

### Phase 3: Use JSONB for Flexibility
For attributes you're not sure about:
```sql
ALTER TABLE users ADD COLUMN metadata JSONB DEFAULT '{}';
```

Store anything:
- User preferences
- Custom fields
- Feature flags
- A/B test assignments
- etc.

---

## Summary

✅ **Yes, you can easily add attributes later!**

**How:**
1. `ALTER TABLE users ADD COLUMN ...` - Simple!
2. Update SQLAlchemy model
3. Update API if needed
4. Done!

**No need to:**
- ❌ Restructure relationships
- ❌ Migrate data (usually)
- ❌ Downtime
- ❌ Complex migrations

**Recommendation:**
- Start with minimal attributes (current state is good)
- Add attributes as you discover you need them
- Use JSONB for flexible/preference data
- Create migrations for each addition

---

**Bottom Line:** PostgreSQL makes this trivial. Add attributes when you need them, not before! 🎉

