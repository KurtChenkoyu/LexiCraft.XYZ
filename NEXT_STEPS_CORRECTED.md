# What's Next? - Corrected Understanding

## The Learning Model (From Documentation)

**Key Insight:** Learning/solidification happens through **verification tests**, not a separate teaching interface. Users typically encounter words elsewhere first (school, books, media). We verify what they've encountered and can facilitate learning through MCQ explanations when they get answers wrong. We are not a school or curriculum that presents words in complete contexts - users learn from outside sources, and we verify/solidify that knowledge.

### The Flow:

1. **Survey** → Assesses baseline vocabulary
2. **Word Discovery** → Users explore/select words (Explorer Mode or Guided Mode)
3. **Verification Tests (MCQ)** → **THIS IS WHERE LEARNING/SOLIDIFICATION HAPPENS**:
   - Question shows word in context
   - Feedback/explanation teaches them
   - Example sentences provided
   - Related words shown
   - Connections explained
4. **Spaced Repetition** → Reinforces through repeated verification
5. **Points Unlock** → After passing verification tests

### From Documentation:

> **Immediate Feedback** (NEW): ⭐
> - Show why answer is correct/incorrect
> - Provide example sentences
> - Show related words
> - Explain connections
> - **Explanation panel**: Shows why answer is correct

**The verification test IS the learning/solidification interface!** We verify what users have encountered elsewhere and facilitate learning when they encounter unknown words or get answers wrong.

---

## What to Build Next

### Option 1: MCQ Generator & Verification Interface (Recommended)

**What:** Generate quiz questions and build the verification test interface where users learn

**Why First:**
- This IS the learning mechanism
- Users learn from the questions + feedback
- Needed for spaced repetition to work
- Core MVP feature

**What to Build:**

1. **MCQ Generator Service** (`backend/src/mcq/generator.py`)
   - Generate 6-option multiple choice questions
   - Use word relationships from Neo4j for distractors
   - Support different question types:
     - Definition questions
     - Context/usage questions
     - Relationship questions
   - Generate feedback/explanation

2. **Verification Test Interface** (`/verify/[wordId]` or `/quiz/[wordId]`)
   - Display MCQ question
   - Show word in context
   - Submit answer
   - **Show feedback/explanation** (this is the learning!)
     - Why answer is correct/incorrect
     - Example sentences
     - Related words
     - Connections
   - Process result using FSRS/SM-2+ algorithm
   - Show next review date

3. **Word Explorer Interface** (`/explore` or `/dashboard/words`)
   - Search/browse words
   - Connection-based suggestions
   - "Start Learning" button → Creates verification schedule
   - Shows which words are in learning/verified/mastered

4. **Integration**
   - Connect to FSRS/SM-2+ verification API
   - Create verification schedules when user selects word
   - Track learning progress

**Estimated Time:** 5-7 days

**Files Needed:**
- Backend: `src/mcq/generator.py`, `src/api/mcq.py`
- Frontend: `app/[locale]/verify/[wordId]/page.tsx`, `app/[locale]/explore/page.tsx`
- Integration: Connect to verification API we built

---

### Option 2: Word Explorer First (Alternative)

**What:** Build word discovery/selection interface first

**Why:**
- Simpler (just displaying/searching words)
- Users can select words to learn
- Then build verification interface

**What to Build:**
1. Word search/browse interface
2. Connection-based suggestions
3. "Start Learning" → Creates verification schedule
4. Integration with Neo4j for word data

**Estimated Time:** 2-3 days

**Then:** Build MCQ Generator & Verification Interface

---

## Recommended Approach

### 🎯 **Start with Option 1: MCQ Generator & Verification Interface**

**Reasoning:**
1. **This IS the learning mechanism** - verification tests teach users
2. **Completes the loop** - Survey → Discovery → Verification (Learning) → Spaced Repetition
3. **Uses what we built** - Leverages FSRS/SM-2+ system
4. **Core feature** - Essential for MVP

### Then: Word Explorer

**Reasoning:**
1. Users need a way to discover/select words
2. Connection-based suggestions enhance learning
3. Simpler once verification is working

---

## Implementation Details

### MCQ Generator Requirements

From documentation:
- **6-option format**:
  - 1 correct answer (100%)
  - 1 close answer (80% - common mistake)
  - 1 partial answer (60%)
  - 1 related answer (40%)
  - 1 distractor (20%)
  - 1 "I don't know" (0%)

- **Question types**:
  - Definition: "What does 'bank' mean?"
  - Context: "What does 'bank' mean in 'I went to the bank'?"
  - Usage: "Which sentence uses 'bank' correctly?"
  - Relationship: "How is 'indirect' related to 'direct'?"

- **Feedback/Explanation**:
  - Why answer is correct/incorrect
  - Example sentences
  - Related words
  - Connections

### Verification Interface Requirements

- Display MCQ question
- Submit answer
- **Show feedback panel** (critical for learning):
  - Correct/incorrect indicator
  - Explanation
  - Examples
  - Related words
  - Connections
- Process result via `/api/v1/verification/review`
- Show next review date
- Track progress

---

## What Would You Like to Build?

1. **MCQ Generator & Verification Interface** (Recommended)
2. **Word Explorer First** (Alternative)
3. **Both Together** (Complete learning flow)

Let me know and I'll start implementing!

