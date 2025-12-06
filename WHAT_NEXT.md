# What's Next? - Current Priorities

**Last Updated:** December 2024  
**Status:** 🟢 Ready for Next Phase

---

## ✅ Recently Completed

1. **Level 2 Content Generation** - 100% complete (7,674 senses)
   - All multi-layer examples generated
   - All 11 failed senses fixed and retried
   - System fully operational

2. **Documentation Updates**
   - External resources documentation
   - NGSL phrase list implementation status
   - Future integration task list

---

## 📊 Current Status Summary

| Component | Status | Progress |
|-----------|--------|----------|
| **Level 2 Content** | ✅ Complete | 100% (7,674 senses) |
| **Level 1 Content** | 🟡 In Progress | 35.2% (1,231 words) |
| **LexiSurvey** | ⚠️ Needs Testing | 90% (backend + frontend done) |
| **User Auth** | ❌ Not Started | 0% |
| **MCQ Generator** | ❌ Not Started | 0% |
| **Verification System** | ❌ Not Started | 0% |
| **Learning Interface** | ❌ Not Started | 0% |

**Overall MVP Progress:** ~35% (Foundation complete, core features pending)

---

## 🎯 Recommended Next Steps (Priority Order)

### Priority 1: Test LexiSurvey Integration (1-2 days) ⚠️ HIGH

**Why First:**
- Backend and frontend are complete
- Can validate the concept quickly
- Unblocks demo/testing

**Tasks:**
1. **End-to-End Testing:**
   ```bash
   # Test frontend → backend → database flow
   # Verify survey sessions persist
   # Test results dashboard display
   ```

2. **Verify CONFUSED_WITH Relationships:**
   ```bash
   # Check if they exist in Neo4j
   # Create if missing (needed for survey engine)
   cd backend
   python -c "from src.database.neo4j_connection import Neo4jConnection; 
              conn = Neo4jConnection(); 
              s = conn.get_session(); 
              r = s.run('MATCH ()-[r:CONFUSED_WITH]->() RETURN count(r) as count').single(); 
              print(f'CONFUSED_WITH relationships: {r[\"count\"]}')"
   ```

3. **Deploy Backend API:**
   - Deploy FastAPI backend (Railway, Render, or similar)
   - Update frontend API URL
   - Test live integration

**Files:**
- `backend/src/api/survey.py` - Survey API
- `landing-page/components/survey/` - Frontend components
- `backend/src/survey/lexisurvey_engine.py` - Survey engine

**Estimated Time:** 1-2 days

---

### Priority 2: User Authentication (3-5 days) 🔴 CRITICAL

**Why Critical:**
- Blocks all user-facing features
- Required for MVP
- Enables user accounts and parent/child management

**Tasks:**
1. **Implement Supabase Auth:**
   - Parent signup/login
   - Child account creation
   - JWT token management

2. **Update Database:**
   - Use existing `users` and `children` tables
   - Add auth middleware to API

3. **Frontend Integration:**
   - Login/signup pages
   - Protected routes
   - Session management

**Files:**
- `backend/src/api/users.py` - User API (may need creation)
- `backend/migrations/007_unified_user_model.sql` - User schema
- `landing-page/app/[locale]/auth/` - Auth pages (may need creation)

**Estimated Time:** 3-5 days

---

### Priority 3: MCQ Generator & Verification Interface (1-2 weeks) 🔴 CRITICAL

**Why Critical:**
- **This IS the learning mechanism** (per documentation)
- Users learn through MCQ tests + feedback
- Needed for spaced repetition
- Core MVP feature

**Key Insight from Documentation:**
> "Learning/solidification happens through **verification tests**, not a separate teaching interface. Users learn from MCQ explanations when they get answers wrong."

**Tasks:**
1. **MCQ Generator Service:**
   ```python
   # backend/src/mcq/generator.py
   - Generate questions from enriched senses
   - Use quiz data from Level 1 enrichment
   - Create 6-option MCQs
   - Include distractors from related words
   ```

2. **Verification Interface:**
   - Display MCQ questions
   - Immediate feedback on answers
   - Explanation panel (why correct/incorrect)
   - Show related words and connections
   - Example sentences

3. **Integration with Spaced Repetition:**
   - Connect to existing FSRS/SM-2+ system
   - Update card state based on performance
   - Schedule next review

**Files:**
- `backend/src/mcq_assembler.py` - May already exist
- `backend/src/api/mcq.py` - MCQ API (may need creation)
- `backend/docs/core-verification-system/MCQ_SYSTEM.md` - Documentation

**Estimated Time:** 1-2 weeks

---

### Priority 4: Learning Interface (Optional - 1 week) 🟡 MEDIUM

**Note:** According to documentation, learning happens through verification tests. However, a basic learning interface can help users:
- Browse words
- See definitions and examples
- Mark words for verification

**Tasks:**
1. **Word Display Page:**
   - Query Neo4j for learning points
   - Display word, definition, examples
   - Show Level 2 multi-layer examples

2. **Learning Flow:**
   - Next word by frequency_rank
   - Mark words as "learning"
   - Track progress in PostgreSQL

3. **Integration:**
   - Connect to verification system
   - Auto-create verification schedule when word marked

**Files:**
- `landing-page/app/[locale]/learn/page.tsx` - Learning page (needs creation)
- `backend/src/api/words.py` - Word API (may need enhancement)

**Estimated Time:** 1 week

---

## 🔄 Background Tasks (Can Run in Parallel)

### Continue Level 1 Content Generation

**Status:** 35.2% complete (1,231/3,500 words)

**Action:**
```bash
cd backend
source venv/bin/activate
python3 -m src.agent_batched --batch-size 10 --limit 100
```

**Estimated Completion:**
- Free tier: ~2 days (1M tokens/day limit)
- Paid tier: ~6 hours (~$0.28 cost)

**Note:** Can run in background, doesn't block other development

---

## 📋 Decision Points

### 1. Learning Model Approach

**Option A: Verification-First (Recommended)**
- Users learn through MCQ tests
- No separate learning interface needed initially
- Focus on MCQ generator + verification interface

**Option B: Learning Interface First**
- Build word browsing/learning interface
- Then add verification
- More traditional approach

**Recommendation:** Option A (verification-first) aligns with documentation

### 2. LexiSurvey vs Core Features

**Question:** Should we complete LexiSurvey testing first, or jump to core MVP features?

**Recommendation:** 
- Quick LexiSurvey test (1-2 days) to validate concept
- Then focus on core features (Auth, MCQ, Verification)

---

## 🎯 Immediate Action Plan

### This Week:
1. **Day 1-2:** Test LexiSurvey integration
2. **Day 3-5:** Start User Authentication

### Next Week:
3. **Week 2:** Complete User Auth + Start MCQ Generator

### Week 3-4:
4. **Week 3:** Complete MCQ Generator
5. **Week 4:** Verification Interface + Integration

---

## 📚 Key Files Reference

### Status Documents
- `CURRENT_STATUS.md` - Overall project status
- `backend/NEXT_STEPS_PLAN.md` - Content generation next steps
- `NEXT_STEPS_OPTIONS.md` - Feature options

### Code
- `backend/src/api/survey.py` - Survey API
- `backend/src/api/mcq.py` - MCQ API (may need creation)
- `backend/src/mcq_assembler.py` - MCQ generator (may exist)
- `backend/docs/core-verification-system/` - Verification docs

### Documentation
- `NEXT_STEPS_CORRECTED.md` - Learning model explanation
- `backend/docs/core-verification-system/MCQ_SYSTEM.md` - MCQ system docs

---

## 💡 Key Insights

1. **Verification IS Learning:** Users learn through MCQ tests + feedback, not a separate interface
2. **Level 2 Complete:** All multi-layer examples generated - ready for MCQ generation
3. **Foundation Solid:** Database, enrichment pipeline, survey system all working
4. **Focus Areas:** Auth, MCQ Generator, Verification Interface are critical path

---

## ✅ Success Criteria for Next Phase

- [ ] LexiSurvey tested end-to-end
- [ ] User authentication working
- [ ] MCQ generator creating questions from enriched senses
- [ ] Verification interface showing questions + feedback
- [ ] Spaced repetition integrated with verification
- [ ] Users can complete full learning loop: Discover → Verify → Learn → Repeat

---

**Next Action:** Start with LexiSurvey integration testing, then proceed to User Authentication.

