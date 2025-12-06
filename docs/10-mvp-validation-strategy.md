# MVP Validation Strategy: Get to Market Fast

## Executive Summary

**Goal**: Validate the "lexicraft.xyz" concept quickly and attract investors

**Timeline**: 4-6 weeks to MVP launch
**Budget**: Minimal (use existing tools, no-code where possible)
**Target**: 50-100 beta families → investor conversations

---

## 🎯 Core Value Proposition (Keep It Simple)

### What We're Validating

1. **Do parents pay upfront for learning motivation?** (Willingness to pay)
2. **Do kids actually learn when there's money involved?** (Effectiveness)
3. **Does financial incentive work?** (Engagement driver)
4. **Is the verification system trusted?** (Platform integrity)

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

### What to BUILD (Essential)

| Feature | Why Essential | Complexity |
|---------|---------------|------------|
| Parent onboarding | Deposit flow | Low |
| Child learning interface | Core product | Medium |
| 6-option MCQ verification | Validates learning | Medium |
| Points tracking | Shows progress | Low |
| **Direct cash withdrawal** | Parent flexibility | Low |

### What to SKIP (For Now)

| Feature | Why Skip | Add Later |
|---------|----------|-----------|
| Full Learning Point Cloud | Complex, validate simple first | Phase 2 |
| Neo4j integration | Use PostgreSQL + JSONB for MVP | Phase 2 |
| **Game currency integration** | **Direct withdrawal simpler** | **Phase 2** |
| Spaced repetition (14 days) | Test with 7-day first | Phase 2 |
| All 7 earning tiers | Start with Tier 1-2 only | Phase 2 |
| Partial unlock/deficit | Complex, test simple first | Phase 2 |

### MVP Feature Set

```
MVP (3-4 Weeks)
├── Parent Flow
│   ├── Sign up (email + password)
│   ├── Add child account
│   └── Deposit (Stripe, NT$500-1,000)
│
├── Child Flow
│   ├── Daily word list (10-20 words)
│   ├── Learn with flashcards
│   ├── 6-option MCQ quiz
│   └── View earned points (converted to NT$)
│
├── Verification
│   ├── Day 1: Learn + immediate test
│   ├── Day 3: Retention test
│   ├── Day 7: Final test → Points unlock
│   └── Simple pass/fail (no partial credit)
│
└── Withdrawal
    ├── Points → NT$ conversion
    ├── Parent requests withdrawal
    └── Bank transfer (Stripe Connect or local payment)
```

---

## 📚 Learning Point System

### Word List Strategy: Combined Standard

**Phase 1 (MVP): 3,000-4,000 words**

| Source | Weight | Coverage |
|--------|--------|----------|
| **CEFR A1-B2** | 40% | European standard, A1-B2 levels |
| **Taiwan MOE Curriculum** | 30% | Elementary + Junior High |
| **Corpus Frequency** | 30% | Google 10K, COCA top 3000 |

**Phase 2 (Expansion): 8,000-10,000 words**

| Source | Weight | Coverage |
|--------|--------|----------|
| **CEFR C1-C2** | 35% | Advanced proficiency |
| **Taiwan Senior High/College** | 25% | Advanced curriculum |
| **Corpus Frequency** | 40% | COCA top 8000 |

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

### Learning Point Cloud Implementation

**For MVP: PostgreSQL + JSONB** (not Neo4j)

```sql
CREATE TABLE learning_points (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    type TEXT DEFAULT 'word',
    tier INTEGER NOT NULL,
    definition TEXT,
    example TEXT,
    frequency_rank INTEGER,
    metadata JSONB DEFAULT '{}'
);
```

**Time to build:** 1-2 hours (vs. days for Neo4j)

---

## 🛡️ Anti-Gaming Analysis

### How Hard to Game the System?

**With daily limit of 20 words/day:**

| Scenario | Time Required | Daily Commitment |
|----------|---------------|------------------|
| 2,000 words | 100+ days | ~1 hour/day |
| 3,000 words | 150+ days | ~1 hour/day |
| 4,000 words | 200+ days | ~1 hour/day |

**Cost-Benefit for Gaming:**
- Time: 100+ days × 1 hour = 100+ hours
- Reward: ~NT$2,000 (if gaming 2,000 words)
- ROI: NT$20/hour (~$0.60/hour)
- **Verdict**: Not worth it for most parents

### Anti-Gaming Measures

1. **Daily word limit**: 20 words/day
2. **Time limits**: 2 hours/day max
3. **Behavioral flags**: Fast answers + perfect scores = review
4. **Human review**: Flag top 5% performers

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

### Secondary Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Words learned per week | 20+ | Learning velocity |
| Avg session time | 10+ min | Engagement depth |
| Parent satisfaction | 8/10+ | Renewal potential |
| Referral rate | 15%+ | Growth potential |

---

## 💰 Investor Pitch Deck Outline

### Slide Structure (10 slides)

1. **Title**: lexicraft.xyz - Kids earn money by learning
2. **Problem**: Kids spend 3+ hours on games, parents struggle to motivate learning
3. **Solution**: Financial incentive = motivated learners
4. **Demo**: 30-second product walkthrough
5. **Market**: $227B EdTech + $47B tutoring market
6. **Business Model**: 8-10% platform fee + premium tiers
7. **Traction**: Beta metrics (after 4-6 weeks)
8. **Team**: Founders + domain expertise
9. **Ask**: Seed round ($500K-$1M) for 18-month runway
10. **Vision**: Every kid earns while learning

### Key Data Points for Investors

- **TAM**: $227B global EdTech
- **SAM**: $47B tutoring/private education
- **SOM**: $1B+ (1% of tutoring market)
- **Unit Economics**: $75 CAC, $500+ LTV (projected)
- **Competition**: No direct competitor with verified learning + financial rewards

---

## 🎨 Landing Page (Week 1)

### Above the Fold

```
┌─────────────────────────────────────────────┐
│  💰 Your Kids Learn. They Earn. You Win.    │
│                                             │
│  Kids earn real money by mastering          │
│  vocabulary. You invest upfront, they       │
│  earn it back.                              │
│                                             │
│  Use their earnings for allowance, toys,   │
│  savings, or anything they want!            │
│                                             │
│  [Join the Waitlist - Get 50% off Beta]     │
└─────────────────────────────────────────────┘
```

### Sections

1. **How It Works** (3 steps with icons)
2. **For Parents** (benefits)
3. **For Kids** (earn money for anything they want)
4. **Pricing** (Beta special: NT$500-1,000 deposit)
5. **FAQ**
6. **Waitlist signup** (email + # of kids)

### Legal Requirements (Waitlist Only)

**✅ No company registration needed for waitlist collection**

**Minimum requirements**:
- Basic privacy policy (what data collected, how used, opt-out)
- Email service compliance (ConvertKit/Mailchimp handle this)
- No payments = no payment processor needed

**Can use**:
- Existing cram school entity name (recommended)
- Personal name (if testing first)
- No new registration required

**When company needed**: Only when accepting payments (Week 2+)

See `docs/13-legal-analysis-taiwan.md` for full legal requirements.

---

## 📅 4-Week Go-to-Market Timeline

### Week 1: Foundation
- [ ] Landing page live
- [ ] Waitlist collection started
- [ ] Database schema ready
- [ ] Word list compiled (3,000 words)
- [ ] Draft investor one-pager

### Week 2: Build Core
- [ ] Parent signup + deposit flow
- [ ] Child account linking
- [ ] Learning point data populated
- [ ] Flashcard learning UI
- [ ] Continue landing page marketing

### Week 3: Build Verification
- [ ] 6-option MCQ generator
- [ ] Day 1, 3, 7 test scheduling
- [ ] Points calculation
- [ ] Parent dashboard (basic)
- [ ] Start outreach to parent communities

### Week 4: Build Withdrawal & Launch
- [ ] Withdrawal request flow
- [ ] Parent notification system
- [ ] Child progress view
- [ ] MVP feature complete
- [ ] Invite 20-50 beta families

---

## 💻 Tech Stack (MVP)

### Recommended (Fast)

| Component | Tool | Why |
|-----------|------|-----|
| Frontend | Next.js + Tailwind | Fast, modern |
| Backend | Supabase or Firebase | Auth + DB + fast |
| Learning Point Cloud | Neo4j Aura Free | Relationships, multi-hop queries |
| User Data | PostgreSQL (Supabase) | Transactional data |
| Payments | Stripe | Industry standard |
| Email | Resend or SendGrid | Transactional |
| Hosting | Vercel | Free, fast |
| Analytics | PostHog or Mixpanel | User tracking |

**Note**: See `docs/development/NEO4J_VS_POSTGRESQL_ANALYSIS.md` for why Neo4j for Learning Point Cloud.

**Deployment**: Cloud-based (SaaS) - Internet required. See `docs/development/DEPLOYMENT_ARCHITECTURE.md` for details.

---

## 🏆 Success Criteria (Before Raising)

### Minimum Viable Traction

- [ ] 50+ paying families
- [ ] 70%+ Day 7 completion rate
- [ ] 50%+ 30-day retention
- [ ] $5K+ MRR
- [ ] 10+ testimonials/case studies
- [ ] 40+ NPS score

### Nice-to-Have

- [ ] 100+ paying families
- [ ] Viral coefficient > 0.3
- [ ] Media coverage (1-2 articles)
- [ ] Partnership interest (schools, tutoring centers)

---

## 🔮 Phase 2 Features (Post-Validation)

After validating core concept with 100+ families:

### Add Complexity Gradually

1. **Full Learning Point Cloud** (PostgreSQL → Neo4j if needed)
2. **Spaced repetition** (14-day cycles)
3. **Partial unlock system** (deficit mechanics)
4. **All 7 tiers** (idioms, morphology, register)
5. **Expand to 8,000-10,000 words**

### Game Integration (Future Phase 2 - NOT MVP)

**⚠️ NOT FOR MVP - Add after core validation:**
- Game currency integration (Robux, V-Bucks, Minecraft coins)
- Gift card purchase/delivery system
- Platform partnerships

**Why later:**
- Validates core thesis first (financial incentive works)
- Reduces legal complexity for MVP
- Can pursue platform partnerships with traction data
- See `docs/08-robux-integration-analysis.md` and `docs/09-multi-game-integration-analysis.md` for future planning

---

## ⚠️ Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Kids game the system | Daily limits (20 words), behavioral flags |
| Parents don't pay | Test pricing early, offer money-back |
| Low completion | Gamify more, shorter cycles |
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

1. **Build simple MVP** (3-4 weeks) - learning + MCQ + direct cash withdrawal
2. **Get 50-100 beta families** (Week 4-5)
3. **Track key metrics** (completion, retention, NPS)
4. **Create investor materials** (deck, demo, metrics)
5. **Start investor conversations** (Week 5+)

**Key Decisions:**
- ✅ **Direct cash withdrawal** (no game currency integration for MVP)
- ✅ **3,000-4,000 words** (CEFR + Taiwan + Corpus combined)
- ✅ **PostgreSQL + JSONB** (not Neo4j for MVP)
- ✅ **Tier 1-2 only** (~5,000 learning points for MVP)
- ✅ **Game integration = Phase 2** (NOT MVP - after core validation)

**Focus on the core thesis**: Financial incentive → Learning motivation. That's what we're validating.
