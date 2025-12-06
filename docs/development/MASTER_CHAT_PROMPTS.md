# Master Chat Prompts: LexiCraft MVP

**For:** Copy-paste prompts to use in implementation chats  
**Role:** Master Planner (you) → Implementation Chats (others)  
**Date:** January 2025

---

## Quick Start

Copy the prompt below for **Phase 1 - Database Schema** (first implementation chat), then proceed sequentially through each phase.

---

## Phase 1 - Database Schema

**Note**: Database Schema is coordinated by Master Schema Planner Chat. See `docs/development/MASTER_SCHEMA_PLANNER.md` for coordination.

**Implementation chats are assigned by Master Schema Planner**:
- Phase 1 - Neo4j Setup
- Phase 1 - PostgreSQL Setup  
- Phase 1 - Schema Integration

See `docs/development/MASTER_SCHEMA_PLANNER.md` for implementation chat prompts.

---

## Phase 1 - Word List Compilation

**Copy this prompt into a new chat (can run in parallel with Database Schema):**

```
You're building the LexiCraft MVP. This is Phase 1 - Word List Compilation.

CONTEXT:
- Need 3,000-4,000 words for MVP
- Combine: CEFR A1-B2 (40%) + Taiwan MOE (30%) + Corpus (30%)
- Target: ~5,000 learning points (Tier 1-2 only for MVP)
- Estimated time: Day 5-7

TASKS:
1. Download word lists (quick sources):
   - [ ] Google 10K: https://github.com/first20hours/google-10000-english (1 minute)
   - [ ] Oxford 3000 CEFR: Search GitHub "Oxford 3000 CSV"
   - [ ] English Vocabulary Profile: https://www.englishprofile.org/wordlists
   - [ ] COCA: https://www.wordfrequency.info/
   - [ ] Taiwan curriculum words (if available)

2. Create combination script:
   - Weighted scoring (CEFR 40%, Taiwan 30%, Corpus 30%)
   - Deduplication
   - Frequency ranking
   - Export to CSV/JSON
   - Target: 3,000-4,000 words for Phase 1

3. Populate learning_points table:
   - Use WordNet for definitions/examples
   - Tier 1: First meaning per word
   - Tier 2: Additional meanings
   - Store in database

4. Create word list API endpoint

SUCCESS CRITERIA:
- [ ] 3,000-4,000 words compiled
- [ ] Weighted combination working
- [ ] Learning points populated in database
- [ ] API endpoint returns word list
- [ ] ~5,000 learning points created (Tier 1-2)

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE1_WORDLIST.md
docs/12-immediate-action-items.md (Day 5-7: Word Database section)

Report back when complete with:
- Word count
- Learning points count
- API endpoint status
- Sources used
- Any issues discovered
```

---

## Phase 1 - Landing Page

**Copy this prompt into a new chat (can run in parallel):**

```
You're building the LexiCraft MVP. This is Phase 1 - Landing Page.

CONTEXT:
- Need landing page for waitlist collection
- Direct cash withdrawal model (not game currency for MVP)
- Target: Taiwan market
- Estimated time: 2-4 hours

TASKS:
1. Choose tool: **Framer** (recommended) or Carrd
2. Create landing page:
   - Headline: "Kids Earn Money by Learning Vocabulary"
   - 3-step "How It Works" section
   - Benefits for parents
   - Benefits for kids
   - Pricing (Beta special)
   - Waitlist form (email + # of kids)

3. Set up email collection:
   - ConvertKit or Mailchimp
   - Connect form to email service
   - Test email collection

4. Deploy:
   - Vercel/Netlify (if using Framer)
   - Or use Carrd hosting

5. Add analytics:
   - PostHog or Mixpanel
   - Track page views, form submissions

6. Test on mobile:
   - Responsive design
   - Form works on mobile
   - Share link with 5 friends for feedback

SUCCESS CRITERIA:
- [ ] Landing page live
- [ ] Waitlist form working
- [ ] Email collection set up
- [ ] Mobile responsive
- [ ] Analytics tracking
- [ ] Feedback collected from 5+ people

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE1_LANDING.md
docs/12-immediate-action-items.md (Day 1-2: Landing Page section)

Report back when complete with:
- Landing page URL
- Email collection status
- Analytics setup
- Feedback received
- Any issues discovered
```

---

## Phase 1 - Social Presence

**Copy this prompt into a new chat (can run in parallel with Landing Page):**

```
You're building the LexiCraft MVP. This is Phase 1 - Social Presence.

CONTEXT:
- Need social media presence for outreach
- Target: Parents, EdTech community
- Estimated time: 1 hour

TASKS:
1. Create Twitter/X account:
   - Choose handle
   - Write bio
   - Add profile picture

2. Create LinkedIn page (optional):
   - Company page or personal
   - Add description

3. Write announcement post:
   - Introduce the concept
   - Link to landing page
   - Not salesy, focus on value

4. Follow accounts:
   - 20+ EdTech accounts
   - 20+ Parent/education accounts
   - Engage with their content

SUCCESS CRITERIA:
- [ ] Twitter/X account created
- [ ] LinkedIn page created (optional)
- [ ] Announcement post published
- [ ] Following 20+ relevant accounts

READ THE FULL HANDOFF:
docs/12-immediate-action-items.md (Day 1-2: Social Presence section)

Report back when complete with:
- Social media handles
- Post engagement
- Any issues discovered
```

---

## Phase 1 - Tech Stack Setup

**Copy this prompt into a new chat (Day 2-3):**

```
You're building the LexiCraft MVP. This is Phase 1 - Tech Stack Setup.

CONTEXT:
- Need to choose and set up tech stack
- Option A: Code (Next.js + Supabase) - Recommended
- Option B: No-code (Bubble/FlutterFlow) - Faster MVP
- Estimated time: 2-3 hours

TASKS:
1. Choose stack:
   - Option A: Next.js + Supabase (recommended for full control)
   - Option B: Bubble/FlutterFlow + Airtable (faster MVP)

2. If Option A (Code):
   ```bash
   npx create-next-app@latest lexicraft
   cd lexicraft
   npm install @supabase/supabase-js
   ```
   - Set up Supabase project at supabase.com
   - Get API keys
   - Configure environment variables

3. If Option B (No-code):
   - Set up Bubble or FlutterFlow account
   - Connect Airtable for database
   - Set up Zapier for automation (if needed)

4. Set up development environment:
   - Git repository
   - Environment variables
   - Local development server

5. Test basic setup:
   - Can create a page
   - Can connect to database
   - Can deploy to staging

SUCCESS CRITERIA:
- [ ] Tech stack chosen
- [ ] Development environment set up
- [ ] Database connection working
- [ ] Can deploy to staging
- [ ] Basic "Hello World" page working

READ THE FULL HANDOFF:
docs/12-immediate-action-items.md (Day 2-3: Tech Setup section)

Report back when complete with:
- Stack chosen
- Setup status
- Database connection status
- Any issues discovered
```

---

## Phase 2 - User Auth & Accounts

**Copy this prompt into a new chat (after Phase 1 Database is complete):**

```
You're building the LexiCraft MVP. This is Phase 2 - User Auth & Accounts.

CONTEXT:
- Use Supabase for auth (fast, built-in)
- Parent must be account owner (Taiwan legal: age of majority = 20)
- Child accounts linked to parent
- Need role-based access

TASKS:
1. Set up Supabase auth:
   - Email/password signup
   - Parent account creation
   - Child account linking (parent creates child account)

2. Create parent flow:
   - [ ] Sign up page (email + password)
   - [ ] Add child form (name, age)
   - [ ] Deposit amount selection (NT$500-1,000)
   - [ ] Stripe checkout ($29/month or $49 one-time)
   - [ ] Dashboard (child progress, points balance)

3. Create child flow:
   - [ ] Login (simple PIN or parent link)
   - [ ] Child dashboard access
   - [ ] Role-based permissions

4. Create account linking:
   - Parent → Child relationship
   - One parent can have multiple children
   - Child can only access their own data

5. Add Taiwan compliance:
   - Parent consent forms
   - Age verification
   - Terms of Service acceptance

6. Write tests

SUCCESS CRITERIA:
- [ ] Supabase auth working
- [ ] Parent signup flow complete
- [ ] Child account linking working
- [ ] Stripe checkout integrated
- [ ] Role-based access enforced
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE2_AUTH.md
docs/12-immediate-action-items.md (Day 3-5: Parent Flow section)

Report back when complete with:
- Auth flow status
- Account linking status
- Stripe integration status
- Test results
- Any issues discovered
```

---

## Phase 2 - Learning Interface

**Copy this prompt into a new chat (after Phase 1 Word List is complete):**

```
You're building the LexiCraft MVP. This is Phase 2 - Learning Interface.

CONTEXT:
- Child-facing learning UI
- Daily word list (10-20 words)
- Flashcard-style learning
- Progress tracking

TASKS:
1. Create child learning flow:
   - [ ] Word of the day view
   - [ ] Flashcard component
   - [ ] Points display
   - [ ] "Claim Reward" button (triggers parent notification)

2. Create learning interface:
   - Daily word list display
   - Flashcard component (word → definition → example)
   - Progress indicator
   - Word completion status

3. Integrate with word list API:
   - Fetch daily words
   - Display definitions/examples
   - Track learning progress

4. Add learning features:
   - Mark word as "learned"
   - Review words
   - Daily word limit (20 words/day)

5. Create child dashboard:
   - Words learned today
   - Total words learned
   - Points earned
   - Progress visualization

6. Write tests

SUCCESS CRITERIA:
- [ ] Learning interface working
- [ ] Daily word list displayed
- [ ] Flashcard learning working
- [ ] Progress tracking working
- [ ] Daily limit enforced
- [ ] Points display working
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE2_LEARNING.md
docs/12-immediate-action-items.md (Day 3-5: Child Flow section)

Report back when complete with:
- UI components created
- API integration status
- Test results
- Any issues discovered
```

---

## Phase 2 - MCQ Generator

**Copy this prompt into a new chat (after Phase 1 Word List is complete):**

```
You're building the LexiCraft MVP. This is Phase 2 - MCQ Generator.

CONTEXT:
- 6-option MCQ questions
- 99.54% confidence (3 correct over 7 days)
- Need distractors (close, partial, related, wrong, "I don't know")

TASKS:
1. Create MCQ generator (see code example below):
   - Generate 6 options per question
   - 1 correct, 1 close, 1 partial, 1 related, 1 distractor, 1 "I don't know"
   - Use WordNet for related words (distractors)
   - Shuffle options randomly

2. Create question types:
   - Definition questions
   - Usage questions
   - Context questions

3. Create question pool:
   - Multiple questions per word
   - Randomize options
   - Prevent duplicate questions

4. Create scoring system:
   - Pass/fail (no partial credit for MVP)
   - Track correct/incorrect answers
   - Store results in database

5. Integrate with child flow:
   - [ ] MCQ quiz (6 options) in child interface
   - [ ] Display results
   - [ ] Track quiz completion

6. Write tests

SUCCESS CRITERIA:
- [ ] MCQ generator working
- [ ] 6 options per question
- [ ] Question types implemented
- [ ] Scoring system working
- [ ] Quiz integrated in child interface
- [ ] Tests passing

CODE EXAMPLE (Simple MCQ Generator):
```javascript
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

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE2_MCQ.md
docs/12-immediate-action-items.md (Day 3-5: 6-Option MCQ Generator section)

Report back when complete with:
- Generator status
- Question pool size
- Test results
- Any issues discovered
```

---

## Phase 3 - Verification Scheduler

**Copy this prompt into a new chat (after Phase 2 MCQ is complete):**

```
You're building the LexiCraft MVP. This is Phase 3 - Verification Scheduler.

CONTEXT:
- Spaced repetition: Day 1, 3, 7
- Day 1: Learn + immediate test (3 questions, need 2/3)
- Day 3: Retention test (1 question, must pass)
- Day 7: Final test (1 question, must pass) → Points unlock

TASKS:
1. Create verification scheduler:
   - Schedule tests on Day 1, 3, 7
   - Track test status (pending, completed, passed, failed)
   - Handle rescheduling on failure

2. Create test delivery system:
   - Show test when scheduled
   - Generate MCQ questions
   - Score and record results
   - Update verification status

3. Create unlock logic:
   - Day 7 pass → Points unlock
   - Day 7 fail → Reschedule or mark as failed
   - Track verification history

4. Add anti-gaming:
   - Minimum 24 hours between tests
   - Daily word limit (20 words)
   - Time limits (2 hours/day)

5. Write tests

SUCCESS CRITERIA:
- [ ] Scheduler working (Day 1, 3, 7)
- [ ] Test delivery working
- [ ] Unlock logic working
- [ ] Anti-gaming measures enforced
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE3_VERIFICATION.md

Report back when complete with:
- Scheduler status
- Test delivery status
- Unlock logic status
- Test results
- Any issues discovered
```

---

## Phase 3 - Points System

**Copy this prompt into a new chat (after Phase 2 Learning Interface is complete):**

```
You're building the LexiCraft MVP. This is Phase 3 - Points System.

CONTEXT:
- Tier 1: 10 points/word (basic recognition)
- Tier 2: 25 points/word (multiple meanings)
- MVP: Tier 1-2 only
- Points convert to NT$ (1 point = NT$0.10 or similar)

TASKS:
1. Create points calculation:
   - Calculate points per word (Tier 1 or Tier 2)
   - Track points earned per word
   - Sum total points

2. Create points account:
   - Track available points
   - Track locked points (pending verification)
   - Track withdrawn points
   - Track deficit (if verification fails)

3. Create points conversion:
   - Points → NT$ conversion
   - Display in parent dashboard
   - Display in child dashboard

4. Create points history:
   - Track all point transactions
   - Show earning history
   - Show withdrawal history

5. Write tests

SUCCESS CRITERIA:
- [ ] Points calculation working
- [ ] Points account tracking working
- [ ] Conversion working
- [ ] History tracking working
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE3_POINTS.md

Report back when complete with:
- Points system status
- Conversion rate
- Test results
- Any issues discovered
```

---

## Phase 3 - Parent Dashboard

**Copy this prompt into a new chat (after Phase 3 Points is complete):**

```
You're building the LexiCraft MVP. This is Phase 3 - Parent Dashboard.

CONTEXT:
- Parent-facing dashboard
- View child progress
- Manage withdrawals
- Track points/earnings

TASKS:
1. Create parent dashboard:
   - Child list (if multiple children)
   - Child progress overview
   - Points balance
   - Withdrawal requests

2. Create progress visualization:
   - Words learned (total, this week, today)
   - Completion rate
   - Points earned
   - Verification status

3. Create withdrawal management:
   - View withdrawal requests
   - Approve/reject withdrawals
   - Withdrawal history

4. Add notifications:
   - Child completes test
   - Points unlocked
   - Withdrawal requested

5. Write tests

SUCCESS CRITERIA:
- [ ] Dashboard working
- [ ] Progress visualization working
- [ ] Withdrawal management working
- [ ] Notifications working
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE3_DASHBOARD.md

Report back when complete with:
- Dashboard status
- Features implemented
- Test results
- Any issues discovered
```

---

## Phase 4 - Withdrawal System

**Copy this prompt into a new chat (after Phase 3 Points is complete):**

```
You're building the LexiCraft MVP. This is Phase 4 - Withdrawal System.

CONTEXT:
- Direct cash withdrawal (not game currency for MVP)
- Parent requests withdrawal
- Bank transfer (Stripe Connect or local payment)
- Taiwan compliance required

TASKS:
1. Create withdrawal request flow:
   - Parent requests withdrawal
   - Validate available points
   - Convert points to NT$
   - Create withdrawal request

2. Integrate payment processor:
   - Stripe Connect (if available in Taiwan)
   - Or local payment processor
   - Bank account linking
   - Transfer processing

3. Create withdrawal tracking:
   - Withdrawal status (pending, processing, completed, failed)
   - Withdrawal history
   - Transaction records

4. Add Taiwan compliance:
   - Tax reporting (rewards ≥NT$1,000)
   - ID collection
   - Transaction records

5. Write tests

SUCCESS CRITERIA:
- [ ] Withdrawal request flow working
- [ ] Payment processor integrated
- [ ] Withdrawal tracking working
- [ ] Compliance features working
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE4_WITHDRAWAL.md

Report back when complete with:
- Withdrawal system status
- Payment processor status
- Test results
- Any issues discovered
```

---

## Phase 4 - Notifications

**Copy this prompt into a new chat (after Phase 3 Verification is complete):**

```
You're building the LexiCraft MVP. This is Phase 4 - Notifications.

CONTEXT:
- Email notifications (Resend/SendGrid)
- Parent notifications (test results, withdrawals)
- Child notifications (test reminders, achievements)

TASKS:
1. Set up email service:
   - Resend or SendGrid account
   - Email templates
   - SMTP configuration

2. Create notification triggers:
   - Test scheduled (reminder)
   - Test completed (result)
   - Points unlocked
   - Withdrawal requested
   - Withdrawal completed

3. Create email templates:
   - Test reminder
   - Test result
   - Points unlocked
   - Withdrawal notification

4. Add notification preferences:
   - Parent notification settings
   - Email frequency
   - Notification types

5. Write tests

SUCCESS CRITERIA:
- [ ] Email service working
- [ ] Notification triggers working
- [ ] Email templates created
- [ ] Preferences working
- [ ] Tests passing

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE4_NOTIFICATIONS.md

Report back when complete with:
- Notification system status
- Email delivery status
- Test results
- Any issues discovered
```

---

## Phase 4 - Beta Launch Prep

**Copy this prompt into a new chat (after all previous phases are complete):**

```
You're building the LexiCraft MVP. This is Phase 4 - Beta Launch Prep.

CONTEXT:
- All features complete
- Need testing, bug fixes, documentation
- Prepare for 50-100 beta families
- Week 4 target

TASKS:
1. End-to-end testing:
   - Full user flow (signup → learn → verify → withdraw)
   - Edge cases
   - Error handling
   - Performance testing

2. Bug fixes:
   - Fix critical bugs
   - Fix UI/UX issues
   - Fix performance issues

3. Documentation:
   - User guide (parent)
   - User guide (child)
   - Admin guide
   - API documentation

4. Beta launch checklist:
   - All features working
   - All tests passing
   - Documentation complete
   - Monitoring set up
   - Support channels ready

5. Create beta invitation system:
   - Invite 20-50 beta families
   - Track invitations
   - Onboard first users

6. Weekly milestones check:
   - [ ] Week 2 End: Parent signup + Stripe working, Child can learn 10 words, Basic quiz working
   - [ ] Week 3 End: Day 1, 3, 7 test scheduling working, Points tracking complete, Parent notifications working
   - [ ] Week 4 End: MVP feature complete, 20-50 beta families invited, First rewards delivered (manually)

SUCCESS CRITERIA:
- [ ] All tests passing
- [ ] Critical bugs fixed
- [ ] Documentation complete
- [ ] Beta launch checklist complete
- [ ] Invitation system ready
- [ ] 20-50 beta families invited

READ THE FULL HANDOFF:
docs/development/handoffs/HANDOFF_PHASE4_LAUNCH.md
docs/12-immediate-action-items.md (Week 2-4: Build & Test section)

Report back when complete with:
- Testing status
- Bug fix status
- Documentation status
- Launch readiness
- Beta families invited
- Any issues discovered
```

---

## Phase 4 - Community Outreach

**Copy this prompt into a new chat (Day 5-7, can run in parallel):**

```
You're building the LexiCraft MVP. This is Phase 4 - Community Outreach.

CONTEXT:
- Need to build community and get beta testers
- Target: Parents, educators
- Estimated time: Day 5-7

TASKS:
1. Join communities:
   - [ ] Join 5+ parent Facebook groups
   - [ ] Join r/parenting, r/daddit, r/homeschool on Reddit
   - [ ] Engage authentically (not salesy)

2. Write introduction post:
   - Introduce the concept
   - Not salesy, focus on value
   - Offer free beta access for feedback
   - Link to landing page

3. Outreach:
   - [ ] DM 10+ parents who seem interested
   - [ ] Respond to questions
   - [ ] Build relationships

4. Sample outreach message:
```
Hey [Name]! I'm building a learning app where kids earn 
money by learning vocabulary. Would love your feedback 
as a parent - looking for 20 beta testers.

Free access in exchange for honest feedback. Interested?
```

SUCCESS CRITERIA:
- [ ] Joined 5+ communities
- [ ] Introduction post published
- [ ] 10+ DMs sent
- [ ] Beta signups from outreach

READ THE FULL HANDOFF:
docs/12-immediate-action-items.md (Day 5-7: Community Outreach section)

Report back when complete with:
- Communities joined
- Posts published
- DMs sent
- Beta signups received
- Any issues discovered
```

---

## Phase 4 - Investor Prep

**Copy this prompt into a new chat (Week 4-6):**

```
You're building the LexiCraft MVP. This is Phase 4 - Investor Prep.

CONTEXT:
- Prepare investor materials
- Build investor list
- Start outreach
- Week 4-6 timeline

TASKS:
1. Create materials:
   - [ ] One-pager (use template in docs/11-investor-one-pager.md)
   - [ ] Pitch deck (10 slides)
   - [ ] 2-min Loom demo video
   - [ ] Metrics screenshot/dashboard

2. Build investor list:
   - [ ] AngelList profiles (EdTech, Gaming)
   - [ ] LinkedIn: Search "EdTech investor"
   - [ ] Twitter: Follow VCs who invest in EdTech
   - [ ] Ask friends for intros

3. Prepare outreach:
   - Use outreach template (see below)
   - Personalize each message
   - Track responses

4. Outreach template:
```
Subject: Kids earn money by learning - quick demo?

Hi [Name],

I saw you invested in [EdTech company] - we're building
something similar with financial incentives.

LexiCraft: Kids earn real money by learning
vocabulary. Parents pay upfront, kids earn it back.

Traction: [X] beta families, [Y]% completion rate

2-min Loom: [link]

Worth a 15-min call? 

Best,
[Your name]
```

5. Track metrics:
   - Waitlist signups
   - Beta signups
   - Completion rate (Day 7)
   - Daily active users
   - Withdrawal requests processed
   - NPS score
   - Retention (30-day)
   - Referrals

SUCCESS CRITERIA:
- [ ] All materials created
- [ ] Investor list built (20+ contacts)
- [ ] Outreach started
- [ ] Investor meetings booked

READ THE FULL HANDOFF:
docs/12-immediate-action-items.md (Investor Prep section, Success Metrics section)

Report back when complete with:
- Materials created
- Investor list size
- Outreach sent
- Meetings booked
- Any issues discovered
```

---

## Reporting Format

When you complete work, use this format:

```markdown
# Completion Report: [Phase] - [Component]

**Feature:** [Component Name]
**Priority:** [High/Medium/Low]
**Date:** [Date]
**Status:** ✅ Complete / 🚧 In Progress / ⚠️ Blocked

## What was done:
[Brief description]

## Decisions made:
[Key decisions]

## Files changed:
[List of files]

## Testing:
[Test results, coverage]

## Known issues:
[Any issues]

## Next steps:
[What's next]
```

---

## Additional Resources

### Tools Checklist

For all phases, refer to the tools checklist:
- Landing page: Framer/Carrd (Free-$20/mo)
- Email collection: ConvertKit (Free tier)
- Frontend: Next.js (Free)
- Backend/DB: Supabase (Free tier)
- Payments: Stripe (2.9% + $0.30)
- Email sending: Resend (Free tier)
- Analytics: PostHog (Free tier)
- Hosting: Vercel (Free tier)
- Video demos: Loom (Free)
- Investor deck: Pitch/Slides (Free)

**Total MVP cost: ~$0-50/month**

See `docs/12-immediate-action-items.md` (Tools Checklist section) for full list.

### Key Decisions Reference

Before starting, review key decisions:
- Tech stack: Code (Next.js) or No-code (Bubble)?
- Pricing model: Subscription ($29/mo) or Deposit ($49-99)?
- Withdrawal method: Bank transfer or other payment method?
- Beta size: 20, 50, or 100 families?
- Launch timeline: 4 weeks or 6 weeks?

See `docs/12-immediate-action-items.md` (Key Decisions section) and `docs/15-key-decisions-summary.md` for details.

### Success Metrics to Track

Track these metrics throughout the build:
- **Week 1**: Waitlist signups, Landing page conversion rate, Social media followers
- **Week 2-4**: Beta signups, Completion rate (Day 7), Daily active users, Bug reports/feedback, Withdrawal requests processed
- **Week 5-6**: NPS score, Retention (30-day), Referrals, Investor meetings booked

See `docs/12-immediate-action-items.md` (Success Metrics section) for full tracking guide.

### Daily Routine (Week 2-4)

- **Morning**: 2-3 hours building
- **Afternoon**: User outreach, respond to inquiries
- **Evening**: Review feedback, plan next day

See `docs/12-immediate-action-items.md` (Week 2-4: Build & Test section) for full routine.

---

**Copy the appropriate prompt above into a new chat to start that phase!**

**Remember**: Done is better than perfect. Focus on validating the core thesis: Can we get parents to pay? Will kids actually complete the learning? Does the financial reward motivate them?

