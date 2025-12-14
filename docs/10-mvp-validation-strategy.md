# MVP Validation Strategy: Enhanced with Industry Best Practices

## Executive Summary

**Goal**: Validate the "lexicraft.xyz" concept quickly and attract investors

**Timeline**: 4-6 weeks to MVP launch
**Budget**: Minimal (use existing tools, no-code where possible)
**Target**: 50-100 beta families → investor conversations

**Key Enhancement**: This version incorporates industry best practices and adds **Connection-Building Scope** strategy for intelligent word selection.

---

## 🎯 Core Value Proposition (Keep It Simple)

### What We're Validating

1. **Do parents pay upfront for learning motivation?** (Willingness to pay)
2. **Do kids actually learn when there's money involved?** (Effectiveness)
3. **Does financial incentive work?** (Engagement driver)
4. **Is the verification system trusted?** (Platform integrity)
5. **Does relationship-based learning improve retention?** (Learning effectiveness)

### The One-Liner

> "Kids earn money by learning vocabulary. Parents pay upfront, kids earn it back."

---

## 🚀 MVP Scope (3-4 Week Build)

### Key Decision: Direct Cash Withdrawal (No Game Integration for MVP)

**Why we're skipping game integration for MVP:**
- ✅ **Faster to build** (3 weeks vs. 4-6 weeks)
- ✅ **Lower legal risk** (no platform ToS issues with game currencies)
- ✅ **Still validates core thesis** (financial incentive → learning motivation)
- ✅ **More parent trust** (parents control how to reward)
- ✅ **Simpler compliance** (no gift card purchase/delivery system)

**MVP Model:**
```
Parent deposits NT$1,000 → Child learns vocabulary → 
Child earns points → Parent withdraws cash → 
Parent decides how to reward (allowance, toys, savings, etc.)
```

**Game integration (Robux, V-Bucks, Minecraft) = Future Phase 2 (NOT MVP)**

---

## 🧠 Connection-Building Scope: The Missing Piece ⭐ NEW

### The Problem

**Current Plan**: Select next 20 words from frequency rank 1-1000 (simple sequential)

**Industry Standard**: 
- Duolingo: Adaptive paths based on prerequisites
- Memrise: Relationship-based learning (learn related words together)
- Anki: Prerequisite chains (learn "direct" before "indirect")

**What We're Missing**: Intelligent word selection that builds semantic networks

### The Solution: Connection-Building Scope Algorithm + Explorer Mode

**Core Principle**: Select words that **connect** to words already learned, building semantic networks rather than random lists.

**Learning Modes**:
1. **Guided Mode**: Follow curriculum, algorithm suggests words
2. **Explorer Mode**: Build your own city, smart suggestions + full freedom

#### Algorithm Overview

```python
def select_daily_words(user_id, daily_limit=20, mode='guided'):
    """
    Select daily words using connection-building scope strategy.
    
    Strategy:
    1. Get child's learned words (verified or learning)
    2. Find words connected to learned words via relationships
    3. Prioritize by connection strength and prerequisites
    4. Mix: 60% connection-based, 40% adaptive level-based
    
    Modes:
    - 'guided': Algorithm selects words (curriculum-focused)
    - 'explorer': Algorithm suggests words (learner chooses)
    """
    learned_words = get_learned_words(user_id)
    vocab_level = get_user_vocab_level(user_id)  # From LexiSurvey
    user_mode = get_user_learning_mode(user_id)
    
    if user_mode == 'explorer':
        # Explorer Mode: Provide suggestions, learner chooses
        return get_explorer_suggestions(user_id, learned_words, daily_limit)
    else:
        # Guided Mode: Algorithm selects
        # Strategy 1: Connection-Based Selection (60%)
        connection_words = select_connection_words(
            learned_words, 
            limit=int(daily_limit * 0.6)
        )
        
        # Strategy 2: Adaptive Level-Based Selection (40%)
        level_words = select_adaptive_words(
            vocab_level,
            learned_words,
            limit=int(daily_limit * 0.4)
        )
        
        return merge_and_prioritize(connection_words, level_words, daily_limit)
```

#### Connection-Based Selection (60% of daily words)

**Priority Order**:

1. **Prerequisites Met** (Highest Priority)
   - Words whose prerequisites are already learned
   - Example: If "direct" is learned → prioritize "indirect"
   - Query: `MATCH (prereq:LearningPoint)-[:PREREQUISITE_OF]->(target:LearningPoint) WHERE prereq.id IN $learned_ids RETURN target`

2. **Direct Relationships** (High Priority)
   - Words directly related to learned words
   - Types: `RELATED_TO`, `COLLOCATES_WITH`, `OPPOSITE_OF`
   - Example: If "make" is learned → prioritize "decision" (collocation)
   - Query: `MATCH (learned:LearningPoint)-[:RELATED_TO|COLLOCATES_WITH]-(target:LearningPoint) WHERE learned.id IN $learned_ids RETURN target`

3. **Phrase Components** (Medium Priority)
   - Words that complete phrases already started
   - Example: If "beat" and "around" learned → prioritize "bush" (for "beat around the bush")
   - Query: `MATCH (phrase:Phrase)-[:PART_OF]-(word:Word) WHERE phrase.component_words IN $learned_ids RETURN word`

4. **Morphological Patterns** (Medium Priority)
   - Words sharing morphological patterns
   - Example: If "direct" learned → prioritize "indirect", "redirect" (same prefix)
   - Query: `MATCH (learned:LearningPoint)-[:MORPHOLOGICAL]-(target:LearningPoint) WHERE learned.id IN $learned_ids RETURN target`

5. **2-Degree Connections** (Lower Priority)
   - Words connected through one intermediate word
   - Example: If "direct" learned → "indirect" → "indirectly"
   - Query: `MATCH (learned:LearningPoint)-[:RELATED_TO]-(intermediate:LearningPoint)-[:RELATED_TO]-(target:LearningPoint) WHERE learned.id IN $learned_ids RETURN target`

6. **Bridge Words** (Discovery Priority) ⭐ NEW
   - Words that connect multiple learned words
   - Example: "function" connects "algorithm" + "physics"
   - Higher score = more connections
   - Query: Find words connected to 2+ learned words

#### Scoring Function

```python
def score_word_connection(word, learned_words, relationships):
    """
    Score word based on connection strength to learned words.
    
    Scoring:
    - Prerequisite met: +100 points
    - Direct relationship: +50 points
    - Phrase component: +40 points
    - Morphological: +30 points
    - 2-degree connection: +20 points
    - Frequency bonus: +10 points (if high frequency)
    - Difficulty penalty: -10 points (if too hard)
    """
    score = 0
    
    # Check prerequisites
    if all_prerequisites_met(word, learned_words):
        score += 100
    
    # Check direct relationships
    direct_rels = count_direct_relationships(word, learned_words, relationships)
    score += direct_rels * 50
    
    # Check phrase components
    if is_phrase_component(word, learned_words):
        score += 40
    
    # Check morphological patterns
    if shares_morphological_pattern(word, learned_words):
        score += 30
    
    # Check 2-degree connections
    two_degree = count_2degree_connections(word, learned_words)
    score += two_degree * 20
    
    # Frequency bonus (higher frequency = easier)
    if word.frequency_rank < 1000:
        score += 10
    
    # Difficulty penalty (too hard = lower score)
    if word.difficulty > user_level + 1:
        score -= 10
    
    return score
```

#### Example: Connection-Building Flow

**Day 1**: Child learns "direct" (rank 500)
- **Day 2 Selection**:
  - ✅ "indirect" (prerequisite met, RELATED_TO) - Priority 1
  - ✅ "redirect" (morphological pattern) - Priority 2
  - ✅ "direction" (morphological pattern) - Priority 2
  - ✅ "straight" (OPPOSITE_OF) - Priority 3

**Day 3**: Child learns "indirect" + "make"
- **Day 4 Selection**:
  - ✅ "decision" (COLLOCATES_WITH "make") - Priority 1
  - ✅ "indirectly" (morphological from "indirect") - Priority 2
  - ✅ "make a decision" (phrase completion) - Priority 1

**Result**: Child builds semantic network, not random word list

#### Benefits of Connection-Building Scope

1. **Better Retention**: Related words reinforce each other
2. **Faster Learning**: Prerequisites make new words easier
3. **Relationship Discovery Bonuses**: More opportunities for bonuses
4. **Natural Progression**: Learning follows semantic structure
5. **Motivation**: See connections = "aha!" moments

#### Implementation Notes

**For MVP (PostgreSQL)**:
- Store relationships in `learning_points.metadata` JSONB
- Query: `SELECT * FROM learning_points WHERE metadata->'prerequisites' @> '[learned_word_id]'`
- Simple but effective for MVP

**For Phase 2 (Neo4j)**:
- Use full graph queries for multi-hop relationships
- More powerful but requires Neo4j setup

---

## 📚 Enhanced Learning Point System

### Word List Strategy: Combined Standard + Connection-Based

**Phase 1 (MVP): 3,000-4,000 words**

| Source | Weight | Coverage |
|--------|--------|----------|
| **CEFR A1-B2** | 40% | European standard, A1-B2 levels |
| **Taiwan MOE Curriculum** | 30% | Elementary + Junior High |
| **Corpus Frequency** | 30% | Google 10K, COCA top 3000 |

**Connection Data**:
- Prerequisite relationships (CEFR levels)
- Collocation pairs (from corpus)
- Morphological patterns (prefix/suffix)
- Semantic relationships (WordNet)

### Learning Points Estimate

**For 3,000-4,000 words:**

| Tier | Learning Points | Description |
|------|-----------------|-------------|
| Tier 1 (Basic words) | 3,500 | One meaning per word |
| Tier 2 (Multiple meanings) | 1,500 | Additional meanings |
| Tier 3 (Phrases) | 6,000 | Common collocations |
| Tier 4 (Idioms) | 500 | Common idioms |
| Tier 5 (Morphological) | 1,200 | Prefix/suffix relationships |
| Tier 6 (Register) | 300 | Formal/informal variants |
| Tier 7 (Advanced context) | 700 | Specialized contexts |
| **TOTAL** | **~13,700** | All tiers combined |

**MVP (Tier 1-2 only):** ~5,000 learning points

### Data Sources for Word Lists

**Immediate (No Registration)**:
1. **Google 10K English**: https://github.com/first20hours/google-10000-english
2. **Oxford 3000 CEFR**: Search GitHub "Oxford 3000 CSV"
3. **BNC Frequency**: Search GitHub "BNC word frequency"

**With Registration**:
4. **English Vocabulary Profile (EVP)**: https://www.englishprofile.org/wordlists
5. **COCA Frequency**: https://www.wordfrequency.info/

**Relationship Data**:
6. **WordNet**: Semantic relationships (synonyms, antonyms, hypernyms)
7. **Collocation Data**: Common word pairs from corpus
8. **Morphological Patterns**: Prefix/suffix lists

### Learning Point Cloud Implementation

**For MVP: PostgreSQL + JSONB** (with relationship metadata)

```sql
CREATE TABLE learning_points (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word',
    tier INTEGER NOT NULL,
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    difficulty INTEGER,  -- CEFR level (1-6 for A1-C2)
    metadata JSONB DEFAULT '{}'  -- Relationships, prerequisites, etc.
);

-- Add indexes for relationship queries
CREATE INDEX idx_learning_points_metadata ON learning_points USING GIN (metadata);
CREATE INDEX idx_learning_points_frequency ON learning_points(frequency_rank);
CREATE INDEX idx_learning_points_difficulty ON learning_points(difficulty);

-- Example metadata structure:
-- {
--   "prerequisites": ["word_id_1", "word_id_2"],
--   "related_words": ["word_id_3", "word_id_4"],
--   "collocations": ["word_id_5"],
--   "morphological_patterns": ["prefix_in", "suffix_ly"]
-- }
```

**Time to build:** 2-3 hours (includes relationship data)

---

## 🎯 Enhanced Child Learning Interface

### 1. Child Dashboard (/child/dashboard)

**Purpose**: Child's main view of their learning progress

**Must Display**:
- Words learned today (count)
- Total words learned (all time)
- Points earned (available + locked)
- Points converted to NT$ (e.g., "NT$ 150 已解鎖")
- Daily word limit status (e.g., "今天已學 5/20 個單字")
- Upcoming verification tests (e.g., "明天有 3 個測驗")
- Learning streak (consecutive days)
- **Connection Map** (NEW): Visual network of learned words ⭐

**UI Requirements**:
- Child-friendly design (colors, large buttons, emojis)
- Mobile-responsive (kids use phones/tablets)
- Simple navigation
- Points prominently displayed
- **Connection visualization** (simple node graph) ⭐

**Data Needed**:
- `learning_progress` table (words learned)
- `points_accounts` table (points balance)
- `verification_schedule` table (upcoming tests)
- Relationship data for connection map

### 2. Daily Word List (/child/learn) - ENHANCED

**Purpose**: Show child their words to learn today (with connection context)

**Learning Modes** ⭐ NEW:

**A. Guided Mode** (Follow Curriculum):
- Algorithm selects 20 words/day
- Based on curriculum (Taiwan MOE, CEFR, etc.)
- Learner can still search/override
- Focus on curriculum-aligned words

**B. Explorer Mode** (Build Your Own City) ⭐ NEW:
- Algorithm suggests words (learner chooses)
- Smart suggestions based on:
  - Connection to learned words
  - Prerequisites met
  - Level appropriateness
  - Interest matches
  - Bridge words (connect multiple areas)
- Learner can search any word
- Full freedom to build custom path

**Must Display**:
- List of 10-20 words for today (Guided) OR suggestions (Explorer)
- Word status: "未開始" / "學習中" / "已完成"
- Progress indicator (e.g., "5/20 完成")
- **Connection indicator**: "🔗 與 'direct' 相關" ⭐
- **Prerequisite status**: "✓ 已學會前置單字" ⭐
- **Suggestion reason** (Explorer Mode): "Ready to learn! (prerequisites met)" ⭐
- **Mode toggle**: Switch between Guided/Explorer ⭐
- "開始學習" button for each word

**Word Selection Logic** (ENHANCED):

**Connection-Building Scope Algorithm**:
1. **60% Connection-Based**:
   - Prerequisites met (highest priority)
   - Direct relationships (RELATED_TO, COLLOCATES_WITH)
   - Phrase components
   - Morphological patterns
   - 2-degree connections
   - Bridge words (connect multiple learned words) ⭐ NEW

2. **40% Adaptive Level-Based**:
   - Words at child's vocabulary level (from LexiSurvey)
   - Words slightly above level (challenge)
   - Review words (struggling areas)

3. **Constraints**:
   - Don't show words already learned
   - Don't show words already scheduled for verification
   - Daily limit: 20 words/day maximum
   - Respect prerequisite order

**Data Needed**:
- Word list with relationship metadata
- `learning_progress` table (to filter out learned words)
- User's vocabulary level (from LexiSurvey)
- Relationship discovery history

### 3. Flashcard Component (/child/learn/[wordId]) - ENHANCED

**Purpose**: Child reviews/verifies a word they've encountered (with connection context). This is a review/confirmation step before verification, not a learning step. Users typically encounter words elsewhere first (school, books, media), and this component helps them confirm they've seen the word before starting verification.

**Flow**:
1. Show word (e.g., "indirect")
2. **Show connection context** (NEW): "🔗 與 'direct' 相關" ⭐
3. Child clicks "Show Definition" → Shows definition
4. Child clicks "Show Example" → Shows example sentence
5. **Show related words** (NEW): "相關單字: redirect, direction" ⭐
6. Child clicks "I Know This" → Confirms they've seen it, starts verification quiz
7. Child clicks "I Need Practice" → Shows again later

**UI Requirements**:
- Large, readable text
- Simple flip animation (optional)
- Clear buttons
- Progress indicator (e.g., "單字 3/20")
- **Connection badge** (NEW): Visual indicator of relationships ⭐

**Data Needed**:
- Word definition, example, pronunciation
- Relationship data (for connection context)
- Update `learning_progress` when user confirms they've seen the word and starts verification
- Check for relationship discoveries (bonus points)

### 4. MCQ Quiz Interface (/child/quiz/[wordId]) - ENHANCED

**Purpose**: Verify child knows the word (Day 1 immediate test)

**Question Format**:
- 6-option multiple choice
- Question: "What does 'bank' mean in this sentence: 'I went to the bank'?"
- Options:
  - Correct answer (financial institution)
  - Close answer (money place - 80% correct)
  - Partial answer (place to save - 60% correct)
  - Related answer (building - 40% correct)
  - Distractor (river edge - 20% correct)
  - "I don't know" (0% correct)

**Scoring**:
- Need 2/3 correct on Day 1 to proceed
- If pass: Schedule Day 3 test
- If fail: Can retry after 24 hours

**Immediate Feedback** (NEW): ⭐
- Show why answer is correct/incorrect
- Provide example sentences
- Show related words
- Explain connections

**UI Requirements**:
- Large, touch-friendly buttons
- Clear feedback (correct/incorrect)
- Progress indicator
- "Submit Answer" button
- **Explanation panel** (NEW): Shows why answer is correct ⭐

**Data Needed**:
- Generate MCQ questions (need algorithm)
- Store answers in `verification_schedule` table
- Update `learning_progress` status
- Relationship data (for better distractors)

### 5. Verification Test Interface (/child/verify/[wordId])

**Purpose**: Day 3, 7, 14 retention tests

**Flow**:
- Show same MCQ format as Day 1 quiz
- Must pass (1/1 correct) to unlock points
- If pass Day 7: Unlock 70% of points
- If pass Day 14: Unlock remaining 30% of points

**UI Requirements**:
- Same as MCQ quiz interface
- Show which test day (e.g., "第 3 天測驗")
- Show points that will unlock if passed
- **Connection reminder** (NEW): "還記得 'direct' 嗎？" ⭐

### 6. Word List Database - ENHANCED

**Current State**: Need to create word list with relationship data

**MVP Approach** (Enhanced):

**Schema**:
```sql
CREATE TABLE learning_points (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word',
    tier INTEGER NOT NULL,
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    difficulty INTEGER,  -- CEFR level
    metadata JSONB DEFAULT '{}'  -- Relationships
);

-- Metadata structure:
{
  "prerequisites": ["word_id_1", "word_id_2"],
  "related_words": ["word_id_3"],
  "collocations": ["word_id_4"],
  "morphological_patterns": ["prefix_in"],
  "opposites": ["word_id_5"]
}
```

**Populate with**:
- 3,000-4,000 words (Tier 1-2 only)
- Relationship data (prerequisites, collocations, morphological)
- Each word needs: word, definition, example, tier, frequency_rank, difficulty, metadata

**Word Sources**:
- Google 10K: https://github.com/first20hours/google-10000-english
- Oxford 3000 CEFR: Search GitHub "Oxford 3000 CSV"
- English Vocabulary Profile: https://www.englishprofile.org/wordlists
- WordNet: For semantic relationships

**MVP Scope**: Tier 1-2 only (~5,000 learning points)

---

## 🎮 Enhanced Features (Industry Best Practices)

### 1. Adaptive Learning ⭐ NEW

**What**: Adjust word selection based on child's performance

**Implementation**:
- Use LexiSurvey results to determine vocabulary level
- Select words at appropriate difficulty level
- Adjust based on quiz performance
- Track ease factor per word (like Anki)

**Benefits**:
- Prevents frustration (too hard)
- Prevents boredom (too easy)
- Optimizes learning speed

### 2. Immediate Feedback ⭐ NEW

**What**: Show explanations after quiz answers

**Implementation**:
- After each answer: Show why correct/incorrect
- Provide example sentences
- Show related words
- Explain connections

**Benefits**:
- Reinforces learning
- Reduces confusion
- Builds understanding

### 3. Basic Gamification ⭐ NEW

**What**: Non-financial rewards to complement money

**Implementation**:
- Learning streaks (consecutive days)
- Achievement badges ("100 Words Master", "Week Warrior")
- Progress visualization (tree, map, or level system)
- Daily challenges

**Benefits**:
- Balances intrinsic/extrinsic motivation
- Increases engagement
- Provides sense of progress

### 4. Enhanced Parent Dashboard ⭐ NEW

**What**: Detailed insights and analytics

**Implementation**:
- Learning analytics (time spent, words learned, retention rate)
- Progress visualization (charts showing growth)
- Areas of strength/weakness
- Recommendations for supporting learning
- Connection map visualization

**Benefits**:
- Parent engagement
- Transparency
- Trust building

### 5. Question Quality Improvements ⭐ NEW

**What**: Better distractor generation

**Implementation**:
- Use common mistakes (from error patterns)
- Use semantically similar words (from relationships)
- Avoid obviously wrong distractors
- Question variation (different contexts)

**Benefits**:
- More accurate assessment
- Prevents memorization
- Tests understanding

---

## 🛡️ Anti-Gaming Analysis

### How Hard to Game the System?

**With daily limit of 20 words/day + connection-building scope:**

| Scenario | Time Required | Daily Commitment |
|----------|---------------|------------------|
| 2,000 words | 100+ days | ~1 hour/day |
| 3,000 words | 150+ days | ~1 hour/day |
| 4,000 words | 200+ days | ~1 hour/day |

**Connection-building scope makes gaming harder**:
- Can't skip prerequisites
- Must learn in order
- Relationships must be genuine

**Cost-Benefit for Gaming**:
- Time: 100+ days × 1 hour = 100+ hours
- Reward: ~NT$2,000 (if gaming 2,000 words)
- ROI: NT$20/hour (~$0.60/hour)
- **Verdict**: Not worth it for most parents

### Anti-Gaming Measures

1. **Daily word limit**: 20 words/day
2. **Time limits**: 2 hours/day max
3. **Behavioral flags**: Fast answers + perfect scores = review
4. **Human review**: Flag top 5% performers
5. **Prerequisite enforcement**: Can't skip prerequisites ⭐ NEW
6. **Connection validation**: Must show understanding of relationships ⭐ NEW

---

## 📊 Validation Metrics

### Primary Metrics (Must Track)

| Metric | Target | Why |
|--------|--------|-----|
| Parent conversion rate | 10%+ | Willingness to pay |
| Child completion rate (Day 7) | 70%+ | Product-market fit |
| Daily active users | 60%+ | Engagement |
| Retention (30 days) | 50%+ | Stickiness |
| NPS score | 40+ | Word of mouth potential |
| **Connection discovery rate** | **30%+** | **Relationship learning effectiveness** ⭐ NEW |

### Secondary Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Words learned per week | 20+ | Learning velocity |
| Avg session time | 10+ min | Engagement depth |
| Parent satisfaction | 8/10+ | Renewal potential |
| Referral rate | 15%+ | Growth potential |
| **Relationship bonus rate** | **20%+** | **Connection-building success** ⭐ NEW |
| **Prerequisite completion rate** | **80%+** | **Learning path effectiveness** ⭐ NEW |

---

## 📅 Enhanced 4-Week Go-to-Market Timeline

### Week 1: Foundation
- [ ] Landing page live
- [ ] Waitlist collection started
- [ ] Database schema ready (with relationship metadata)
- [ ] Word list compiled (3,000 words + relationships)
- [ ] Draft investor one-pager
- [ ] **Connection-building algorithm designed** ⭐ NEW

### Week 2: Build Core
- [ ] Parent signup + deposit flow
- [ ] Child account linking
- [ ] Learning point data populated (with relationships)
- [ ] Flashcard learning UI (with connection context)
- [ ] **Connection-building word selection** ⭐ NEW
- [ ] Continue landing page marketing

### Week 3: Build Verification
- [ ] 6-option MCQ generator (with relationship-based distractors)
- [ ] Day 1, 3, 7 test scheduling
- [ ] Points calculation
- [ ] Parent dashboard (enhanced with analytics)
- [ ] **Immediate feedback system** ⭐ NEW
- [ ] **Relationship discovery bonus system** ⭐ NEW
- [ ] Start outreach to parent communities

### Week 4: Build Withdrawal & Launch
- [ ] Withdrawal request flow
- [ ] Parent notification system
- [ ] Child progress view (with connection map)
- [ ] **Basic gamification** (streaks, badges) ⭐ NEW
- [ ] MVP feature complete
- [ ] Invite 20-50 beta families

---

## 💻 Tech Stack (MVP)

### Recommended (Fast)

| Component | Tool | Why |
|-----------|------|-----|
| Frontend | Next.js + Tailwind | Fast, modern |
| Backend | Supabase or Firebase | Auth + DB + fast |
| Learning Point Cloud | PostgreSQL + JSONB (MVP) | Relationships in metadata |
| User Data | PostgreSQL (Supabase) | Transactional data |
| Payments | Stripe | Industry standard |
| Email | Resend or SendGrid | Transactional |
| Hosting | Vercel | Free, fast |
| Analytics | PostHog or Mixpanel | User tracking |

**Note**: For MVP, use PostgreSQL + JSONB for relationships. Neo4j can be added in Phase 2 if needed.

**Deployment**: Cloud-based (SaaS) - Internet required.

---

## 🏆 Success Criteria (Before Raising)

### Minimum Viable Traction

- [ ] 50+ paying families
- [ ] 70%+ Day 7 completion rate
- [ ] 50%+ 30-day retention
- [ ] $5K+ MRR
- [ ] 10+ testimonials/case studies
- [ ] 40+ NPS score
- [ ] **30%+ connection discovery rate** ⭐ NEW

### Nice-to-Have

- [ ] 100+ paying families
- [ ] Viral coefficient > 0.3
- [ ] Media coverage (1-2 articles)
- [ ] Partnership interest (schools, tutoring centers)
- [ ] **80%+ prerequisite completion rate** ⭐ NEW

---

## 🔮 Phase 2 Features (Post-Validation)

After validating core concept with 100+ families:

### Add Complexity Gradually

1. **Full Learning Point Cloud** (PostgreSQL → Neo4j if needed)
2. **Spaced repetition** (14-day cycles)
3. **Partial unlock system** (deficit mechanics)
4. **All 7 tiers** (idioms, morphology, register)
5. **Expand to 8,000-10,000 words**
6. **Advanced connection visualization** (interactive graph)
7. **AI-powered learning path recommendations**

### Game Integration (Future Phase 2 - NOT MVP)

**⚠️ NOT FOR MVP - Add after core validation:**
- Game currency integration (Robux, V-Bucks, Minecraft coins)
- Gift card purchase/delivery system
- Platform partnerships

**Why later:**
- Validates core thesis first (financial incentive works)
- Reduces legal complexity for MVP
- Can pursue platform partnerships with traction data

---

## ⚠️ Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Kids game the system | Daily limits (20 words), behavioral flags, prerequisite enforcement |
| Parents don't pay | Test pricing early, offer money-back |
| Low completion | Gamify more, shorter cycles, connection-building motivation |
| **Connection algorithm too complex** | **Start simple (PostgreSQL), iterate based on data** ⭐ NEW |
| **Relationship data quality** | **Validate with 50-word pilot, manual review** ⭐ NEW |
| **Legal compliance (Taiwan)** | **Parent as account owner, direct withdrawal** |

---

## 🇹🇼 Taiwan-Specific Legal Requirements

**CRITICAL**: If launching in Taiwan, see full legal analysis: `docs/13-legal-analysis-taiwan.md`

### Top 5 Legal Issues for Taiwan

1. **Age of Majority = 20** (not 18)
   - Parent must be account owner
   - Child cannot legally enter contracts

2. **Direct Withdrawal Model** (MVP)
   - Simpler than game currency integration
   - No platform ToS issues
   - Parent controls reward distribution

3. **Tax Reporting** (NT$1,000+)
   - Collect ID for rewards ≥NT$1,000
   - Withhold 10% tax for rewards ≥NT$20,010

4. **FTC Reward Limits**
   - Startups: NT$150M annual max
   - Individual prize: NT$5M max

5. **7-Day Refund Right**
   - Consumer Protection Act requires 7-day cooling-off
   - Full refund for unused points

### MVP Legal Compliance (Taiwan)

**Before Launch**:
- [ ] Register Taiwan business entity
- [ ] Engage Taiwan legal counsel
- [ ] Draft Taiwan-compliant Terms of Service
- [ ] Implement parental consent system
- [ ] Set up tax reporting system

**Estimated Legal Cost**: NT$1M-2M (~$30K-60K USD) first year

**Quick Reference**: See `docs/14-legal-quick-reference-taiwan.md`

---

## Summary

**The fastest path to validation:**

1. **Build enhanced MVP** (3-4 weeks) - learning + MCQ + connection-building + direct cash withdrawal
2. **Get 50-100 beta families** (Week 4-5)
3. **Track key metrics** (completion, retention, NPS, connection discovery)
4. **Create investor materials** (deck, demo, metrics)
5. **Start investor conversations** (Week 5+)

**Key Decisions:**
- ✅ **Direct cash withdrawal** (no game currency integration for MVP)
- ✅ **3,000-4,000 words** (CEFR + Taiwan + Corpus combined)
- ✅ **PostgreSQL + JSONB** (with relationship metadata for MVP)
- ✅ **Tier 1-2 only** (~5,000 learning points for MVP)
- ✅ **Connection-building scope** (60% connection-based, 40% adaptive) ⭐ NEW
- ✅ **Game integration = Phase 2** (NOT MVP - after core validation)

**Key Enhancements:**
- ✅ **Connection-building scope algorithm** (the missing piece!)
- ✅ **Adaptive learning** (based on vocabulary level)
- ✅ **Immediate feedback** (explanations after answers)
- ✅ **Basic gamification** (streaks, badges)
- ✅ **Enhanced parent dashboard** (analytics, insights)
- ✅ **Question quality improvements** (relationship-based distractors)

**Focus on the core thesis**: Financial incentive → Learning motivation. Connection-building scope makes learning more effective and engaging.

