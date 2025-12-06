# Key Decisions Summary

This document consolidates all key decisions made during project planning.

---

## 1. MVP Reward Model: Direct Cash Withdrawal

### Decision
**Use direct cash withdrawal for MVP, NOT game currency integration.**

### Rationale
- **Faster to build**: 3-4 weeks vs. 4-6 weeks
- **Lower legal risk**: No game currency platform ToS violations
- **Still validates core thesis**: Financial incentive → learning motivation
- **More parent trust**: Parents control how to reward children
- **Simpler compliance**: No gift card purchase/delivery complexity

### Implementation
```
Parent deposits → Child learns → Child earns points → 
Parent withdraws cash → Parent decides reward
```

### Game Integration = Future Phase 2 (NOT MVP)
**⚠️ NOT FOR MVP** - Add after validating core concept with 100+ families:
- Game currency integration (Robux, V-Bucks, Minecraft coins)
- Gift card purchase/delivery system
- Platform partnerships
- See `docs/08-robux-integration-analysis.md` and `docs/09-multi-game-integration-analysis.md` for detailed future plans

---

## 2. Word List: Combined Standard

### Decision
**Combine CEFR + Taiwan MOE + Corpus frequency for word lists.**

### Phase 1 (MVP): 3,000-4,000 words

| Source | Weight | Coverage |
|--------|--------|----------|
| CEFR A1-B2 | 40% | European standard |
| Taiwan MOE Curriculum | 30% | Local relevance |
| Corpus Frequency (Top 3000) | 30% | Real-world usage |

### Phase 2 (Expansion): 8,000-10,000 words

| Source | Weight | Coverage |
|--------|--------|----------|
| CEFR C1-C2 | 35% | Advanced proficiency |
| Taiwan Senior High/College | 25% | Advanced curriculum |
| Corpus Frequency (Top 8000) | 40% | Broader coverage |

### Data Sources
- **Google 10K**: https://github.com/first20hours/google-10000-english
- **Oxford 3000 CEFR**: GitHub search "Oxford 3000 CSV"
- **English Vocabulary Profile**: https://www.englishprofile.org/wordlists
- **COCA**: https://www.wordfrequency.info/

---

## 3. Learning Points Estimate

### Decision
**Estimate ~13,700 learning points for 3,000-4,000 words (all tiers).**

### Breakdown

| Tier | Learning Points | Description |
|------|-----------------|-------------|
| Tier 1 | 3,500 | Basic word recognition |
| Tier 2 | 1,500 | Multiple meanings |
| Tier 3 | 6,000 | Phrases/collocations |
| Tier 4 | 500 | Idioms |
| Tier 5 | 1,200 | Morphological relationships |
| Tier 6 | 300 | Register variants |
| Tier 7 | 700 | Advanced contexts |
| **TOTAL** | **~13,700** | All tiers |

### MVP Scope
- **Tier 1-2 only**: ~5,000 learning points
- Add tiers 3-7 in Phase 2

---

## 4. Learning Point Cloud: Neo4j for MVP

### Decision
**Use Neo4j for Learning Point Cloud, PostgreSQL for user data.**

### Rationale
- **Relationships are core**: Even MVP needs relationship discovery bonuses
- **Multi-hop queries essential**: Pattern recognition, relationship discovery
- **Better learning experience**: Fast queries → better UX → higher completion
- **No migration needed**: Start right, avoid technical debt
- **Actually faster to set up**: 8 hours vs 11 hours (when including relationship queries)

### Architecture
```
Learning Point Cloud (Neo4j)
├── Nodes: LearningPoint (word, phrase, idiom, prefix, suffix)
├── Relationships: PREREQUISITE_OF, COLLOCATES_WITH, RELATED_TO, 
│                  PART_OF, OPPOSITE_OF, MORPHOLOGICAL, etc.
└── Queries: Multi-hop traversal, pattern matching

User Data (PostgreSQL)
├── Users, children, progress
├── Points accounts, transactions
└── Verification schedule
```

### Schema (Neo4j)
```cypher
(:LearningPoint {
  id: String,
  type: "word" | "phrase" | "idiom" | "prefix" | "suffix",
  content: String,
  frequency_rank: Integer,
  difficulty: "A1" | "A2" | "B1" | "B2" | "C1" | "C2",
  tier: Integer
})

(:LearningPoint)-[:PREREQUISITE_OF]->(:LearningPoint)
(:LearningPoint)-[:COLLOCATES_WITH]->(:LearningPoint)
(:LearningPoint)-[:RELATED_TO]->(:LearningPoint)
(:LearningPoint)-[:PART_OF]->(:LearningPoint)
(:LearningPoint)-[:OPPOSITE_OF]->(:LearningPoint)
(:LearningPoint)-[:MORPHOLOGICAL {type: "prefix"|"suffix"}]->(:LearningPoint)
(:LearningPoint)-[:REGISTER_VARIANT]->(:LearningPoint)
```

See `docs/development/NEO4J_VS_POSTGRESQL_ANALYSIS.md` for detailed analysis.

---

## 5. Anti-Gaming Measures

### Decision
**Implement daily limits to make gaming impractical.**

### Limits
| Limit | Value | Impact |
|-------|-------|--------|
| Words per day | 20 | 2,000 words = 100+ days |
| Tests per day | 50 | Prevents bulk testing |
| Minimum time between tests | 24 hours | Prevents same-day completion |
| Daily time limit | 2 hours | Prevents excessive use |

### Gaming Analysis
- **Time to game 2,000 words**: 100+ days
- **Time investment**: 100+ hours
- **Financial gain**: ~NT$2,000
- **ROI**: NT$20/hour (~$0.60/hour)
- **Verdict**: Not worth it for most parents

---

## 6. Verification Strategy

### Decision
**6-option MCQ with 99.54% confidence (3 correct over 7 days).**

### Schedule
- **Day 1**: Learn + immediate test (3 questions, need 2/3)
- **Day 3**: Retention test (1 question, must pass)
- **Day 7**: Final test (1 question, must pass) → Points unlock

### Statistical Confidence
- 3 correct answers = 0.46% chance of guessing
- 99.54% confidence they actually know the material

---

## 7. Taiwan Legal Compliance

### Decision
**Design MVP for Taiwan legal compliance from day 1.**

### Key Requirements
1. **Age of Majority = 20**: Parent must be account owner
2. **Direct withdrawal model**: Simpler than game currency
3. **Tax reporting**: Track rewards ≥NT$1,000
4. **FTC limits**: NT$150M annual max for startups
5. **7-day refund right**: Consumer Protection Act

### Cost Estimate
- Legal setup: NT$200K-500K
- First year total: NT$1M-2M (~$30K-60K USD)

---

## 8. Timeline

### Decision
**4-week MVP build, then beta launch.**

| Week | Focus |
|------|-------|
| 1 | Foundation (landing page, word list, schema) |
| 2 | Core build (signup, deposit, learning UI) |
| 3 | Verification (MCQ, scheduling, points) |
| 4 | Withdrawal + Beta launch |

### Success Criteria
- 50+ paying families
- 70%+ Day 7 completion rate
- 50%+ 30-day retention
- $5K+ MRR

---

## 9. Tech Stack & Deployment

### Decision
**Cloud-based SaaS (not standalone app). Neo4j + PostgreSQL hybrid approach.**

| Component | Tool | Cost (MVP) |
|-----------|------|------------|
| Frontend | Next.js + Tailwind | Free (Vercel) |
| Backend | Supabase Edge Functions | Free |
| Learning Point Cloud | Neo4j Aura Free | Free (50K nodes) |
| User Data | PostgreSQL (Supabase) | Free (500MB) |
| Payments | Stripe | 2.9% + $0.30 |
| Hosting | Vercel | Free |
| Email | Resend | Free tier |
| Analytics | PostHog | Free tier |

**Deployment**: Cloud-based (SaaS) - Internet required. See `docs/development/DEPLOYMENT_ARCHITECTURE.md`.

**Distraction Mitigation**: Full-screen mode, session timers, parental controls. See `docs/development/DISTRACTION_MITIGATION.md`.

---

## 10. Company Registration & Legal Setup

### Decision
**Use existing cram school entity for MVP. No company needed for landing page waitlist.**

**Landing Page (Week 1)**:
- ✅ No company registration needed for waitlist collection
- ✅ Can use existing cram school entity name or personal name
- ✅ Basic privacy policy only
- ✅ Cost: $0-20/month (Framer/Carrd)

**MVP (Week 2+)**:
- ✅ Use existing cram school entity (recommended)
  - Faster to start
  - No new registration
  - Can separate later if needed
- ⚠️ Or register new Taiwan entity (if scope doesn't match)
  - Cost: NT$50K-100K (~$1,500-3,000 USD)
  - Cleaner for investors
  - Better for Phase 2+

**Stripe Setup**:
- ✅ Don't need US company
- ✅ Use Taiwan entity (cram school or new)
- ✅ Stripe available in Taiwan

See `docs/13-legal-analysis-taiwan.md` for full legal requirements.

---

## 11. Roadmap Summary

### Phase 1: MVP (Weeks 1-4)
- Direct cash withdrawal model
- 3,000-4,000 words (Tier 1-2)
- Neo4j (Learning Point Cloud) + PostgreSQL (user data)
- Cloud-based deployment (Internet required)
- Use existing cram school entity
- 50-100 beta families

### Phase 2: Expansion (Months 2-4)
- Game currency integration (if validated - NOT MVP)
- Expand to 8,000-10,000 words
- All 7 tiers
- 500+ families

### Phase 3: Scale (Months 4-12)
- Full Learning Point Cloud
- Mobile apps
- B2B expansion
- International markets

---

## Document References

| Document | Purpose |
|----------|---------|
| `docs/10-mvp-validation-strategy.md` | Complete MVP plan |
| `docs/11-investor-one-pager.md` | Investor summary |
| `docs/13-legal-analysis-taiwan.md` | Taiwan legal details |
| `docs/14-legal-quick-reference-taiwan.md` | Legal quick reference |

---

*Last updated: Based on planning discussions*

