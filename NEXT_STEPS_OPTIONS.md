# What's Next? - Options & Recommendations

## Current Status

✅ **Completed:**
- FSRS/SM-2+ spaced repetition backend
- User authentication & onboarding
- Survey system
- Database schema (unified user model)
- Progressive Survey Model

❌ **Missing (Core MVP Features):**
- Learning interface (where users learn words)
- MCQ generator (for verification tests)
- Verification/test interface (where users take quizzes)
- Integration between learning → verification → spaced repetition

---

## Option 1: Build Learning Interface (Recommended First)

**What:** Users can browse and learn words from the vocabulary database

**Why First:**
- Core MVP feature - users need to learn words before verifying
- Relatively straightforward (display word data from Neo4j)
- Enables the full learning loop

**What to Build:**
1. **Word Learning Page** (`/learn` or `/dashboard/learn`)
   - Display word, definition, examples, pronunciation
   - "Mark as Learning" button
   - Progress tracking
   - Next/Previous word navigation

2. **Learning Progress Tracking**
   - Create `learning_progress` entries
   - Track which words user is learning
   - Show learning statistics

3. **Integration with Verification**
   - When user marks word as "learning", automatically create verification schedule
   - Use the FSRS/SM-2+ system we just built

**Estimated Time:** 3-5 days

**Files Needed:**
- Frontend: `app/[locale]/learn/page.tsx`
- Backend: API endpoints for word data, learning progress
- Integration: Connect to existing `learning_progress` and `verification_schedule` tables

---

## Option 2: Build MCQ Generator & Verification Interface

**What:** Generate quiz questions and let users take verification tests

**Why:**
- Needed for spaced repetition verification
- Users need to pass tests to unlock points
- Core verification mechanism

**What to Build:**
1. **MCQ Generator Service**
   - Generate 6-option multiple choice questions
   - Use word relationships from Neo4j for distractors
   - Support different question types (definition, usage, context)

2. **Verification Test Interface** (`/verify/[wordId]`)
   - Display MCQ question
   - Submit answer
   - Process result using FSRS/SM-2+ algorithm
   - Show feedback and next review date

3. **Integration with Spaced Repetition**
   - Use `/api/v1/verification/review` endpoint we built
   - Update verification schedule
   - Track performance ratings

**Estimated Time:** 5-7 days

**Files Needed:**
- Backend: `src/mcq/generator.py` (MCQ generation logic)
- Backend: `src/api/mcq.py` (MCQ API endpoints)
- Frontend: `app/[locale]/verify/[wordId]/page.tsx`
- Integration: Connect to verification API

---

## Option 3: Test & Deploy FSRS System

**What:** Actually run the migration and test the FSRS implementation

**Why:**
- Verify everything works before building on top of it
- Catch any issues early
- Get A/B testing data flowing

**What to Do:**
1. Run database migration (`011_fsrs_support.sql`)
2. Install FSRS library (`pip install fsrs`)
3. Run verification script (`verify_fsrs_setup.py`)
4. Test API endpoints manually
5. Create test users and simulate reviews

**Estimated Time:** 1-2 days

**Files Needed:**
- Migration script (already created)
- Test script (already created)
- Manual testing

---

## Option 4: Build Complete Verification Flow (All-in-One)

**What:** Build learning interface + MCQ generator + verification in one go

**Why:**
- Complete user experience from start to finish
- See the full flow working together
- Better for demos/testing

**What to Build:**
1. Learning interface (Option 1)
2. MCQ generator (Option 2)
3. Verification interface (Option 2)
4. Integration between all three

**Estimated Time:** 10-14 days

---

## My Recommendation

### 🎯 **Start with Option 1: Learning Interface**

**Reasoning:**
1. **Foundation First:** Users need to learn words before verifying them
2. **Simpler:** Just displaying data, no complex logic
3. **Enables Testing:** Once users can learn words, you can test the verification system
4. **Quick Win:** Can be built in 3-5 days

### Then Option 2: MCQ Generator & Verification

**Reasoning:**
1. **Completes the Loop:** Learning → Verification → Spaced Repetition
2. **Uses What We Built:** Leverages the FSRS/SM-2+ system
3. **Core Feature:** Essential for MVP

### Finally Option 3: Test & Deploy

**Reasoning:**
1. **Validate Everything:** Make sure it all works together
2. **Real Data:** Get actual user data flowing
3. **A/B Testing:** Start collecting FSRS vs SM-2+ comparison data

---

## Alternative: Quick Integration Test

If you want to see the FSRS system working immediately:

1. **Create a simple test script** that:
   - Creates a test user
   - Creates a learning progress entry
   - Creates a verification schedule
   - Simulates reviews using the API
   - Shows how intervals change

2. **This would:**
   - Verify FSRS works end-to-end
   - Show the algorithm in action
   - Take 1-2 hours

Then proceed with Option 1.

---

## What Would You Like to Do?

1. **Build Learning Interface** (Option 1) - Recommended
2. **Build MCQ Generator** (Option 2)
3. **Test FSRS System** (Option 3)
4. **Quick Integration Test** (Alternative)
5. **Something Else?**

Let me know and I'll start implementing!

