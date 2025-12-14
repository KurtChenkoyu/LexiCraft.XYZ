# MCQ Feedback Loop - MVP Design

## Philosophy

**"Trust but Verify"** - The generator is now a robust system (savepoints, quality caps, strict logic), but users are the ultimate judges of MCQ quality.

## The MVP Loop

```
User sees MCQ → Reacts (👍/👎) → Backend logs → Generator learns → Better MCQs
```

## Database Schema

### Table: `mcq_feedback`

```sql
CREATE TABLE mcq_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mcq_id UUID NOT NULL REFERENCES mcq_pool(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Feedback type
    feedback_type VARCHAR(20) NOT NULL, -- 'thumbs_up', 'thumbs_down', 'report'
    
    -- Reason codes (for thumbs_down / report)
    issue_type VARCHAR(50), -- 'ambiguous', 'wrong_answer', 'bad_distractor', 'confusing_wording', 'other'
    comment TEXT,
    
    -- Context (helps understand WHY user gave this feedback)
    was_correct BOOLEAN NOT NULL, -- Did user answer correctly?
    response_time_ms INTEGER, -- How long they took
    attempt_number INTEGER DEFAULT 1, -- First time seeing this MCQ, or repeat?
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_mcq_feedback_mcq (mcq_id),
    INDEX idx_mcq_feedback_user (user_id),
    INDEX idx_mcq_feedback_type (feedback_type)
);
```

### Computed Field: Quality Score

Add to `mcq_pool` table (or compute dynamically):

```sql
ALTER TABLE mcq_pool ADD COLUMN quality_score DECIMAL(3,2) DEFAULT NULL;
ALTER TABLE mcq_pool ADD COLUMN feedback_count INTEGER DEFAULT 0;
ALTER TABLE mcq_pool ADD COLUMN thumbs_up_count INTEGER DEFAULT 0;
ALTER TABLE mcq_pool ADD COLUMN thumbs_down_count INTEGER DEFAULT 0;

-- Quality score calculation
-- quality_score = (thumbs_up - thumbs_down * 2) / feedback_count
-- Range: -2.0 (all thumbs down) to 1.0 (all thumbs up)
-- Weight thumbs_down 2x because negative feedback is more significant
```

## Frontend UI (Minimal)

### Option 1: Inline Buttons (Recommended for MVP)

```tsx
// Add to MCQSession.tsx after user submits answer
<div className="flex gap-2 mt-4">
  <button onClick={() => handleFeedback('thumbs_up')}>
    👍 Good Question
  </button>
  <button onClick={() => handleFeedback('thumbs_down')}>
    👎 Confusing
  </button>
</div>
```

### Option 2: Slide-up Modal (After Answer)

Only show feedback prompt if:
- User got it wrong (they're frustrated → valuable signal)
- OR it's their 3rd+ time seeing this MCQ (pattern detection)

## Backend API

### Endpoint: `POST /api/v1/mcq/feedback`

```typescript
interface FeedbackRequest {
  mcq_id: string
  feedback_type: 'thumbs_up' | 'thumbs_down' | 'report'
  issue_type?: 'ambiguous' | 'wrong_answer' | 'bad_distractor' | 'confusing_wording' | 'other'
  comment?: string
  was_correct: boolean
  response_time_ms: number
  attempt_number: number
}

interface FeedbackResponse {
  success: boolean
  message: string
  new_quality_score?: number
}
```

### Logic

```python
@router.post("/feedback")
async def submit_mcq_feedback(
    request: FeedbackRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    # 1. Store feedback
    feedback = MCQFeedback(
        mcq_id=request.mcq_id,
        user_id=user_id,
        feedback_type=request.feedback_type,
        issue_type=request.issue_type,
        comment=request.comment,
        was_correct=request.was_correct,
        response_time_ms=request.response_time_ms,
        attempt_number=request.attempt_number
    )
    db.add(feedback)
    
    # 2. Update MCQ quality score
    mcq = db.query(MCQPool).filter(MCQPool.id == request.mcq_id).first()
    mcq.feedback_count += 1
    
    if request.feedback_type == 'thumbs_up':
        mcq.thumbs_up_count += 1
    elif request.feedback_type in ['thumbs_down', 'report']:
        mcq.thumbs_down_count += 1
    
    # Calculate quality score
    if mcq.feedback_count > 0:
        mcq.quality_score = (mcq.thumbs_up_count - mcq.thumbs_down_count * 2) / mcq.feedback_count
    
    # 3. Auto-disable if quality is terrible
    if mcq.feedback_count >= 5 and mcq.quality_score < -1.0:
        mcq.is_active = False
        logger.warning(f"MCQ {mcq.id} auto-disabled due to low quality score: {mcq.quality_score}")
    
    db.commit()
    
    return FeedbackResponse(
        success=True,
        message="Thanks for your feedback!",
        new_quality_score=mcq.quality_score
    )
```

## The Learning Loop (Future Enhancement)

### Phase 1: Human Analysis (Now → 1 month)
- Collect 1,000+ feedback samples
- Manual review of thumbs_down MCQs
- Identify patterns (e.g., "Tier 4 similar distractors are too confusing")

### Phase 2: Agent-Assisted Review (1-3 months)
- LLM reviews flagged MCQs
- Suggests fixes (e.g., "Swap distractor B for a Tier 5 option")
- Human approves/rejects suggestions

### Phase 3: Auto-Regeneration (3-6 months)
- Low-quality MCQs auto-queued for regeneration
- Generator uses feedback data to avoid bad patterns
- Closed loop: Bad MCQs → Feedback → Better rules → Golden MCQs

## Metrics Dashboard (Admin)

### Key Metrics
- **Overall Quality:** Avg quality score across all MCQs
- **Problem MCQs:** List of MCQs with score < -0.5
- **Issue Breakdown:** Pie chart of issue_type distribution
- **Learner Frustration Index:** % of wrong answers that also get thumbs_down

### SQL Queries

```sql
-- Problem MCQs needing review
SELECT 
    m.word,
    m.sense_id,
    m.mcq_type,
    m.quality_score,
    m.feedback_count,
    m.thumbs_down_count
FROM mcq_pool m
WHERE m.feedback_count >= 3 
  AND m.quality_score < -0.5
ORDER BY m.quality_score ASC
LIMIT 50;

-- Most common issues
SELECT 
    issue_type,
    COUNT(*) as count,
    AVG(CASE WHEN was_correct THEN 0 ELSE 1 END) as wrong_answer_rate
FROM mcq_feedback
WHERE feedback_type IN ('thumbs_down', 'report')
GROUP BY issue_type
ORDER BY count DESC;
```

## Gamification Hook (Bonus)

**Reward users for feedback:**
- 👍 Good Question → +1 XP (encourages engagement)
- 👎 Confusing → +5 XP (reward critical feedback)
- 🚩 Report with comment → +20 XP (high-value contribution)

**Why:**
- Aligns incentives: Users WANT to give feedback
- Turns QA into gameplay ("I'm helping improve the game!")
- High-quality feedback = more XP = faster progression

## Implementation Priority

1. **Week 1 (MVP):** Database schema + API endpoint
2. **Week 2:** Frontend buttons + basic feedback flow
3. **Week 3:** Admin dashboard to view flagged MCQs
4. **Week 4:** Analyze first 100 feedback samples, identify patterns

## Success Criteria

- **Target:** 10% of MCQ sessions result in feedback (thumbs up or down)
- **Quality:** < 5% of MCQs have negative quality score after 5+ samples
- **Action:** Within 1 month, disable or regenerate worst 100 MCQs based on feedback

---

**The Loop Closes:** Users teach the machine → Machine generates better questions → Users win more → Positive reinforcement

