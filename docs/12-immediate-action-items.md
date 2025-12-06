# Immediate Action Items - Week 1 Checklist

## Key Decision: Direct Cash Withdrawal (MVP)

**For MVP, we're using direct cash withdrawal, NOT game currency integration.**

Parents withdraw cash and decide how to reward their kids (allowance, toys, savings, etc.).
Game integration = Phase 2 after validation (NOT MVP).

---

## Day 1-2: Foundation

### Landing Page (2-4 hours)
- [ ] Choose tool: **Framer** (recommended) or Carrd
- [ ] Write headline: "Kids Earn Money by Learning Vocabulary"
- [ ] Add 3-step "How it Works" section
- [ ] Create waitlist form (email, # of kids)
- [ ] Set up email collection (ConvertKit or Mailchimp)
- [ ] Add basic privacy policy (waitlist collection only)
- [ ] Use existing cram school entity name (or personal name)
- [ ] **No company registration needed for waitlist**
- [ ] Deploy and test
- [ ] Share link with 5 friends for feedback

### Social Presence (1 hour)
- [ ] Create Twitter/X account
- [ ] Create LinkedIn page (optional)
- [ ] Write announcement post
- [ ] Follow 20+ EdTech/parent accounts

---

## Day 2-3: Tech Setup

### Choose Your Stack

**Option A: Code (Recommended for Full Control)**
```bash
# Next.js + Supabase + Neo4j
npx create-next-app@latest lexicraft-xyz
cd lexicraft-xyz
npm install @supabase/supabase-js neo4j-driver
# Set up Supabase project at supabase.com
# Set up Neo4j Aura Free at neo4j.com/cloud/aura/
```

**Deployment**: Cloud-based (SaaS) - Internet required
- Frontend: Vercel (free)
- Neo4j: Neo4j Aura Free (free tier)
- PostgreSQL: Supabase (free tier)
- See `docs/development/DEPLOYMENT_ARCHITECTURE.md` for details

**Option B: No-Code (Faster MVP)**
- Use **Bubble** or **FlutterFlow**
- Connect **Airtable** for database
- Use **Zapier** for automation
- Note: Neo4j integration may be limited in no-code tools

### Database Schema

**Hybrid Approach**: Neo4j for Learning Point Cloud, PostgreSQL for user data

**Neo4j (Learning Point Cloud)**:
- Learning points (words, phrases, idioms)
- Relationships (PREREQUISITE_OF, RELATED_TO, etc.)
- Multi-hop queries for relationship discovery

**PostgreSQL (User Data)**:
- Users (parents)
- Children
- Learning progress
- Points accounts
- Verification schedule
- Withdrawal requests

See `docs/development/handoffs/HANDOFF_PHASE1_DATABASE_NEO4J.md` for full schema.

---

## Day 3-5: Core Build

### Parent Flow
- [ ] Sign up page (email + password)
- [ ] Add child form (name, age)
- [ ] Deposit amount selection (NT$500-1,000)
- [ ] Stripe checkout ($29/month or $49 one-time)
- [ ] Dashboard (child progress, points balance)

### Child Flow
- [ ] Login (simple pin or parent link)
- [ ] Word of the day view
- [ ] Flashcard component
- [ ] MCQ quiz (6 options)
- [ ] Points display
- [ ] "Claim Reward" button (triggers parent notification)

### 6-Option MCQ Generator

```javascript
// Simple MCQ generator
function generateMCQ(word, correctDefinition, allWords) {
  // Get distractors
  const distractors = allWords
    .filter(w => w.word !== word)
    .sort(() => Math.random() - 0.5)
    .slice(0, 4)
    .map(w => w.definition);
  
  // Create options
  const options = [
    { text: correctDefinition, correct: true },
    ...distractors.map(d => ({ text: d, correct: false })),
    { text: "I don't know", correct: false }
  ];
  
  // Shuffle
  return options.sort(() => Math.random() - 0.5);
}
```

---

## Day 5-7: Content & Outreach

### Word Database (Combined Standard)
- [ ] Download Google 10K list (1 minute)
- [ ] Get Oxford 3000 CEFR list (GitHub)
- [ ] Combine with weighted scoring (CEFR 40%, Taiwan 30%, Corpus 30%)
- [ ] Target: 3,000-4,000 words for Phase 1

**Quick Word Sources**:
- Google 10K: https://github.com/first20hours/google-10000-english
- Oxford 3000 CEFR: Search GitHub "Oxford 3000 CSV"
- English Vocabulary Profile: https://www.englishprofile.org/wordlists
- COCA: https://www.wordfrequency.info/

### Community Outreach
- [ ] Join 5+ parent Facebook groups
- [ ] Join r/parenting, r/daddit, r/homeschool
- [ ] Write introduction post (not salesy)
- [ ] Offer free beta access for feedback
- [ ] DM 10+ parents who seem interested

### Sample Outreach Message

```
Hey [Name]! I'm building a learning app where kids earn 
Money by learning vocabulary. Would love your feedback 
as a parent - looking for 20 beta testers.

Free access in exchange for honest feedback. Interested?
```

---

## Week 2-4: Build & Test

### Daily Routine
- Morning: 2-3 hours building
- Afternoon: User outreach, respond to inquiries
- Evening: Review feedback, plan next day

### Weekly Milestones

**Week 2 End**: 
- Parent signup + Stripe working
- Child can learn 10 words
- Basic quiz working

**Week 3 End**:
- Day 1, 3, 7 test scheduling working
- Points tracking complete
- Parent notifications working

**Week 4 End**:
- MVP feature complete
- 20-50 beta families invited
- First rewards delivered (manually)

---

## Investor Prep (Week 4-6)

### Materials to Create
- [ ] One-pager (use template in docs/11)
- [ ] Pitch deck (10 slides)
- [ ] 2-min Loom demo video
- [ ] Metrics screenshot/dashboard

### Investor List Building
- [ ] AngelList profiles (EdTech, Gaming)
- [ ] LinkedIn: "EdTech investor"
- [ ] Twitter: Follow VCs who invest in EdTech
- [ ] Ask friends for intros

### Outreach Template

```
Subject: Kids earn money by learning - quick demo?

Hi [Name],

I saw you invested in [EdTech company] - we're building
something similar with financial incentives.

lexicraft.xyz: Kids earn real money by learning
vocabulary. Parents pay upfront, kids earn it back.

Traction: [X] beta families, [Y]% completion rate

2-min Loom: [link]

Worth a 15-min call? 

Best,
[Your name]
```

---

## Success Metrics to Track

### Week 1
- Waitlist signups
- Landing page conversion rate
- Social media followers

### Week 2-4
- Beta signups
- Completion rate (Day 7)
- Daily active users
- Bug reports/feedback
- Withdrawal requests processed

### Week 5-6
- NPS score
- Retention (30-day)
- Referrals
- Investor meetings booked

---

## Tools Checklist

| Purpose | Tool | Cost |
|---------|------|------|
| Landing page | Framer/Carrd | Free-$20/mo |
| Email collection | ConvertKit | Free tier |
| Frontend | Next.js | Free |
| Backend/DB | Supabase | Free tier |
| Payments | Stripe | 2.9% + $0.30 |
| Email sending | Resend | Free tier |
| Analytics | PostHog | Free tier |
| Hosting | Vercel | Free tier |
| Video demos | Loom | Free |
| Investor deck | Pitch/Slides | Free |

**Total MVP cost: ~$0-50/month**

---

## Key Decisions to Make Today

1. **Tech stack**: Code (Next.js) or No-code (Bubble)?
2. **Pricing model**: Subscription ($29/mo) or Deposit ($49-99)?
3. **Withdrawal method**: Bank transfer or other payment method?
4. **Beta size**: 20, 50, or 100 families?
5. **Launch timeline**: 4 weeks or 6 weeks?

---

## Remember

> **Done is better than perfect.**
> 
> Your MVP should be embarrassingly simple. If kids are learning and 
> parents are paying, you've validated the core thesis. Everything 
> else can wait.

**Focus on**: 
- Can we get parents to pay?
- Will kids actually complete the learning?
- Does the financial reward motivate them?

**Don't worry about**:
- Beautiful design
- Complex verification
- Game currency integrations (Phase 2 only)
- Scaling issues

You can add complexity after you've proven the model works. 🚀

