# Integration Needed: MCQ → Verification API → Spaced Repetition

## Current State

✅ **What Exists:**
- MCQ Generator (`mcq_assembler.py`)
- MCQ Adaptive Service (`mcq_adaptive.py`)
- MCQ API (`api/mcq.py`) - GET MCQ, submit answer
- FSRS/SM-2+ Verification API (`api/verification.py`) - Process review, update schedule
- Frontend MCQ components (`MCQCard.tsx`, `MCQSession.tsx`)

❌ **What's Missing:**
- Integration between MCQ submission and verification API
- Frontend verification page that connects everything
- Word explorer/discovery interface

---

## Integration Required

### Backend: Connect MCQ → Verification API

**Current Flow:**
```
MCQ Submit → Records attempt → Returns feedback
(Doesn't update verification schedule's spaced repetition state)
```

**Needed Flow:**
```
MCQ Submit → Records attempt → Call Verification API → Update spaced repetition → Return feedback
```

**What to Build:**

1. **Update MCQ Submit Endpoint** (`api/mcq.py`)
   - After processing MCQ answer, if `verification_schedule_id` is provided:
     - Map MCQ result to performance rating (0-4)
     - Call `/api/v1/verification/review` internally
     - Update verification schedule with spaced repetition state
   - Return combined result (MCQ feedback + next review date)

2. **Or Create Combined Endpoint** (`api/verification.py`)
   - `POST /api/v1/verification/process-mcq`
   - Takes: `verification_schedule_id`, `mcq_id`, `selected_index`, `response_time_ms`
   - Gets MCQ, grades it, processes via spaced repetition
   - Returns: MCQ feedback + verification result

---

## Frontend: Verification Page

**What to Build:**

1. **Verification Page** (`/verify/[scheduleId]` or `/verify/due`)
   - Shows due cards from `/api/v1/verification/due`
   - For each card:
     - Get MCQ via `/api/v1/mcq/get?sense_id=...`
     - Display MCQ using existing `MCQCard` component
     - Submit answer
     - Show feedback + next review date
     - Mark as complete

2. **Word Explorer** (`/explore` or `/dashboard/words`)
   - Search/browse words
   - Connection-based suggestions
   - "Start Learning" → Creates `learning_progress` + `verification_schedule`
   - Shows learning status (learning/verified/mastered)

---

## Recommended Next Steps

### Option 1: Backend Integration First (Recommended)

**What:** Connect MCQ submission to verification API

**Time:** 1-2 days

**Files to Modify:**
- `backend/src/api/mcq.py` - Update submit endpoint
- Or create new endpoint in `backend/src/api/verification.py`

### Option 2: Frontend Verification Page

**What:** Build verification page that uses MCQs

**Time:** 2-3 days

**Files to Create:**
- `landing-page/app/[locale]/verify/page.tsx` - List due cards
- `landing-page/app/[locale]/verify/[scheduleId]/page.tsx` - Take test
- Integration with existing MCQ components

### Option 3: Word Explorer

**What:** Build word discovery/selection interface

**Time:** 2-3 days

**Files to Create:**
- `landing-page/app/[locale]/explore/page.tsx`
- API endpoint for word search/suggestions

---

## Which Should We Build First?

1. **Backend Integration** - Connect MCQ → Verification (1-2 days)
2. **Frontend Verification Page** - Complete user flow (2-3 days)
3. **Word Explorer** - Discovery interface (2-3 days)

**My Recommendation:** Start with #1 (Backend Integration) to connect the systems, then #2 (Frontend) to complete the user experience.

