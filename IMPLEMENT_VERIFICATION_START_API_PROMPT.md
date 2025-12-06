# Implementation Prompt: Verification Start API

## Context & Vision

LexiCraft is a **vocabulary verification and solidification platform**. The system verifies and solidifies vocabulary knowledge that users have encountered elsewhere (school, books, media). Learning/solidification happens primarily through detailed MCQ explanations when users get answers wrong, especially with FSRS spaced repetition. We are **not a school or curriculum** - we don't present words in complete contexts. Users learn from outside sources, and we verify/solidify that knowledge. There is no separate "learn word" step.

## Critical Gap: Missing Verification Start API

**Problem:** There is **NO API endpoint** to start verification for words. Users cannot start verification quizzes through the API.

**Evidence:**
- ✅ `create_learning_progress()` function exists in `backend/src/database/postgres_crud/progress.py`
- ✅ `create_verification_schedule()` function exists in `backend/src/database/postgres_crud/verification.py`
- ❌ **NO API endpoint calls these functions**
- ❌ Only found in test scripts

## Required Implementation

### Endpoint Specification

**Create:** `POST /api/v1/words/start-verification`

**Request Body:**
```python
{
    "learning_point_id": str,  # Required: The word/learning point ID
    "tier": int,                # Required: Initial tier (1-5, typically 1 for new words)
    "initial_difficulty": float # Optional: Default 0.5, used by algorithm
}
```

**Response:**
```python
{
    "success": bool,
    "learning_progress_id": int,
    "verification_schedule_id": int,
    "learning_point_id": str,
    "status": str,  # Should be "pending"
    "scheduled_date": str,  # ISO date format
    "algorithm_type": str,  # "sm2_plus" or "fsrs"
    "mastery_level": str,
    "message": str
}
```

### Implementation Steps

1. **Create new file:** `backend/src/api/words.py`
   - Follow the pattern from `backend/src/api/verification.py`
   - Use FastAPI router with prefix `/api/v1/words`
   - Include authentication middleware: `Depends(get_current_user_id)`
   - Use database session dependency pattern from verification.py

2. **Import required functions:**
   - `from src.database.postgres_crud.progress import create_learning_progress`
   - `from src.database.postgres_crud.verification import create_verification_schedule`
   - `from src.middleware.auth import get_current_user_id`
   - Database connection pattern from `verification.py`

3. **Implement the endpoint:**
   - Validate request (learning_point_id, tier required)
   - Check if learning_progress already exists for this user + learning_point_id (avoid duplicates)
   - Create `learning_progress` entry with `status='pending'` (NOT 'learning')
   - Create `verification_schedule` entry using the existing function (it handles algorithm selection automatically)
   - Return success response with both IDs and schedule info

4. **Error Handling:**
   - Handle duplicate entries (if learning_progress already exists, return appropriate error)
   - Handle invalid learning_point_id
   - Handle invalid tier values
   - Use HTTPException with appropriate status codes

5. **Register router in `backend/src/main.py`:**
   - Add: `from src.api import words as words_router`
   - Add: `app.include_router(words_router.router)`

## Key Implementation Details

### Function Signatures (from existing code):

**`create_learning_progress()`:**
```python
def create_learning_progress(
    session: Session,
    user_id: UUID,
    learning_point_id: str,
    tier: int,
    status: str = 'learning'  # Use 'pending' for new entries
) -> LearningProgress
```

**`create_verification_schedule()`:**
```python
def create_verification_schedule(
    session: Session,
    user_id: UUID,
    learning_progress_id: int,
    learning_point_id: str,
    initial_difficulty: float = 0.5,
    test_day: Optional[int] = None,
    scheduled_date: Optional[date] = None
) -> VerificationSchedule
```

**Important:** The `create_verification_schedule()` function automatically:
- Gets the user's assigned algorithm (SM-2+ or FSRS)
- Initializes the card state using the algorithm
- Sets the scheduled_date based on algorithm calculations
- Handles all algorithm-specific state (stability, difficulty, etc.)

### Status Field Clarification

- Use `status='pending'` when creating learning_progress (NOT 'learning')
- The status indicates the word is ready for verification quizzes
- Learning/solidification happens through MCQ explanations during verification

### Duplicate Prevention

Before creating, check if a learning_progress entry already exists:
- Query by `user_id` + `learning_point_id`
- If exists, return appropriate error (409 Conflict) or return existing entry info
- Reference: `get_learning_progress_by_learning_point()` in `progress.py`

## Code Patterns to Follow

### Router Setup (from verification.py):
```python
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/words", tags=["Words"])

# Database connection pattern
_postgres_conn: Optional[PostgresConnection] = None

def get_postgres_conn() -> PostgresConnection:
    global _postgres_conn
    if _postgres_conn is None:
        _postgres_conn = PostgresConnection()
    return _postgres_conn

def get_db_session() -> Generator[Session, None, None]:
    conn = get_postgres_conn()
    session = conn.get_session()
    try:
        yield session
    finally:
        session.close()
```

### Request/Response Models (follow verification.py pattern):
```python
from pydantic import BaseModel, Field

class StartVerificationRequest(BaseModel):
    learning_point_id: str = Field(..., description="The learning point ID")
    tier: int = Field(..., ge=1, le=5, description="Initial tier (1-5)")
    initial_difficulty: float = Field(0.5, ge=0.0, le=1.0, description="Initial difficulty")

class StartVerificationResponse(BaseModel):
    success: bool
    learning_progress_id: int
    verification_schedule_id: int
    learning_point_id: str
    status: str
    scheduled_date: str
    algorithm_type: str
    mastery_level: str
    message: str
```

## Testing Requirements

After implementation, test:
1. ✅ Create verification for a new word
2. ✅ Verify duplicate prevention (try to create same word twice)
3. ✅ Verify algorithm assignment (should use user's assigned algorithm)
4. ✅ Verify scheduled_date is set correctly
5. ✅ Verify learning_progress status is 'pending'
6. ✅ Verify error handling for invalid inputs

## Reference Files

- **Existing CRUD functions:** `backend/src/database/postgres_crud/progress.py`, `backend/src/database/postgres_crud/verification.py`
- **API pattern:** `backend/src/api/verification.py`
- **Main app:** `backend/src/main.py`
- **Documentation:** `backend/docs/core-verification-system/SPRINT_COORDINATOR_REFERENCE.md`

## Success Criteria

✅ Endpoint exists at `POST /api/v1/words/start-verification`  
✅ Creates learning_progress with status='pending'  
✅ Creates verification_schedule using user's algorithm  
✅ Returns proper response with IDs and schedule info  
✅ Handles duplicates and errors gracefully  
✅ Router registered in main.py  
✅ Follows existing code patterns and conventions  

---

**Priority:** 🔴 CRITICAL - This is a blocking issue preventing users from starting verification.

