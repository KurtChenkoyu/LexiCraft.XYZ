# Survey → Verification Integration Flow Investigation

**Date:** 2025-01-XX  
**Status:** Investigation Complete  
**Purpose:** Understand survey completion data and design integration approach for creating `learning_progress` entries

---

## Executive Summary

The survey system **DOES identify specific words** tested during the survey, not just vocabulary size estimates. However, the integration requires mapping from survey word data to `learning_point_id` format used by the verification system.

### Key Findings

1. ✅ **Survey tracks specific words**: Each question in `survey_history` contains the exact word tested
2. ✅ **Word-level data available**: History includes `word`, `rank`, `correct`, `band`, and `sense_id`
3. ⚠️ **Mapping required**: Survey uses `sense_id` (Neo4j Sense.id), verification uses `learning_point_id` (format: `word_pos_tier`)
4. ✅ **Frequency band data**: Band performance tracked for vocabulary estimation
5. ✅ **Correctness tracking**: Each word has a `correct` flag indicating if user knew it

---

## Survey Data Structure

### 1. Survey History (`survey_history` table)

**Schema:**
```sql
CREATE TABLE survey_history (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES survey_sessions(id),
    history JSONB NOT NULL,  -- Array of QuestionHistory objects
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**History Entry Structure** (from `QuestionHistory` model):
```json
{
    "rank": 3500,
    "correct": true,
    "time_taken": 4.5,
    "word": "Establish",
    "question_id": "q_3500_12345",
    "band": 4000,
    "question_number": 1,
    "selected_option_ids": ["target_establish_0"],
    "correct_option_ids": ["target_establish_0"],
    "all_options": [...]
}
```

**Key Fields:**
- `word`: The exact word tested (e.g., "Establish")
- `rank`: Frequency rank (1-8000)
- `correct`: Boolean indicating if user answered correctly
- `band`: Frequency band (1000, 2000, 3000, ..., 8000)
- `sense_id`: Optional - Neo4j Sense.id (e.g., "establish.v.01")

### 2. Survey Results (`survey_results` table)

**Schema:**
```sql
CREATE TABLE survey_results (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES survey_sessions(id),
    volume INTEGER,      -- Estimated vocabulary size
    reach INTEGER,       -- Highest reliable rank
    density FLOAT,       -- Consistency score (0.0-1.0)
    cefr_level TEXT
);
```

**Metrics:**
- `volume`: Extrapolated vocabulary size from band performance
- `reach`: Highest frequency band where accuracy > 50%
- `density`: Monotonicity/consistency of knowledge

### 3. Survey Questions (`survey_questions` table)

**Schema:**
```sql
CREATE TABLE survey_questions (
    session_id UUID,
    question_id TEXT,
    question_number INTEGER,
    word TEXT,
    rank INTEGER,
    phase INTEGER,
    options JSONB,
    time_limit INTEGER
);
```

Contains the full question data including the word and all options.

---

## Survey Completion Flow

### Location: `backend/src/api/survey.py` (lines 532-700)

**Process:**
1. Survey engine processes final answer
2. Calculates Tri-Metric Report (volume, reach, density)
3. Saves to `survey_results` table
4. Saves metadata to `survey_metadata` table (V3 PSM)
5. History already saved incrementally in `survey_history` table

**Key Code:**
```python
# Lines 532-551: Save survey results
if result.status == 'complete' and result.metrics:
    db.execute(
        text("""
            INSERT INTO survey_results (session_id, volume, reach, density, cefr_level)
            VALUES (:session_id, :volume, :reach, :density, :cefr_level)
            ...
        """),
        {
            "session_id": db_session_id,
            "volume": result.metrics.volume,
            "reach": result.metrics.reach,
            "density": result.metrics.density,
            "cefr_level": None,
        }
    )
```

**History Storage:**
- History is saved incrementally after each answer (lines 474-485)
- Each entry includes full word details
- Stored as JSONB array in `survey_history.history`

---

## Frequency Band Performance

### Band Structure

**Bands:** [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]

Each band represents ~1000 words. Performance tracked per band:
```python
band_performance = {
    1000: {"tested": 4, "correct": 3},  # 75% accuracy
    2000: {"tested": 3, "correct": 2},  # 67% accuracy
    3000: {"tested": 2, "correct": 1},  # 50% accuracy
    4000: {"tested": 2, "correct": 0}   # 0% accuracy
}
```

**Volume Calculation:**
```
Volume = Σ (band_accuracy × 1000)
Example: 0.75×1000 + 0.67×1000 + 0.5×1000 + 0×1000 = 1920 words
```

### Band vs. Word-Level Data

**Band-level (aggregated):**
- Used for vocabulary size estimation
- Stored in `SurveyState.band_performance`
- Not directly stored in database (calculated on-the-fly)

**Word-level (specific):**
- Each tested word stored in `survey_history.history`
- Includes exact word, rank, correctness
- **This is what we need for integration**

---

## Key Questions Answered

### Q1: Does survey identify specific known words, or just vocabulary size?

**Answer: YES, survey identifies specific words.**

- Each question tests a specific word
- Word stored in `survey_history.history[].word`
- Correctness stored in `survey_history.history[].correct`
- Rank stored in `survey_history.history[].rank`

**Example:**
```json
{
    "word": "Establish",
    "rank": 3500,
    "correct": true,
    "band": 4000
}
```

### Q2: What data is available after survey completion?

**Answer: Complete word-level history available.**

**Available Data:**
1. **Word-level history**: `survey_history.history` (JSONB array)
   - Each entry: `{word, rank, correct, band, time_taken, ...}`
   
2. **Aggregate metrics**: `survey_results` table
   - `volume`: Estimated vocabulary size
   - `reach`: Highest reliable rank
   - `density`: Consistency score

3. **Band performance**: Calculated from history
   - Can reconstruct from `survey_history.history`
   - Each entry has `band` field

4. **Question details**: `survey_questions` table
   - Full question data including options
   - Can cross-reference with history

### Q3: How should we convert survey results to `learning_progress` entries?

**Answer: Create entries for words answered correctly.**

**Approach:**
1. Query `survey_history` for completed survey session
2. Filter entries where `correct = true`
3. For each correct word:
   - Map `word` + `rank` → `learning_point_id`
   - Determine `tier` (likely tier 1 for survey words)
   - Create `learning_progress` entry with:
     - `user_id`: From `survey_sessions.user_id`
     - `learning_point_id`: Mapped from word
     - `tier`: 1 (or determined from rank)
     - `status`: 'verified' (since survey confirmed knowledge)
     - `learned_at`: Survey completion time

**Mapping Challenge:**
- Survey uses `word` (e.g., "Establish")
- Verification uses `learning_point_id` (e.g., "establish_v1")
- Need mapping function: `word → learning_point_id`

### Q4: Should we create entries for all words in known frequency bands, or only specific tested words?

**Answer: Only specific tested words (conservative approach).**

**Rationale:**
1. **Survey tests samples, not all words**
   - Only ~10-35 words tested per survey
   - Band performance is statistical estimate
   - Cannot assume all words in band are known

2. **Verification system requires specific words**
   - `learning_progress` tracks specific learning points
   - Cannot create entries for untested words
   - Would create false positives

3. **Conservative approach recommended**
   - Only create entries for words where `correct = true`
   - Let verification system handle additional words
   - Survey provides initial seed, not complete vocabulary

**Alternative (if needed):**
- Could create entries for all words in bands with >80% accuracy
- But this is risky and may create false positives
- **Recommendation: Stick to tested words only**

---

## Integration Design

### Option 1: Automatic Integration (Recommended)

**Trigger:** After survey completion (`status = 'complete'`)

**Location:** `backend/src/api/survey.py` (after line 700)

**Process:**
```python
# After survey completion
if result.status == 'complete':
    # 1. Get survey history
    history = get_survey_history(db, session_id)
    
    # 2. Filter correct answers
    correct_words = [h for h in history if h.get('correct')]
    
    # 3. Create learning_progress entries
    for entry in correct_words:
        learning_point_id = map_word_to_learning_point(
            word=entry['word'],
            rank=entry['rank']
        )
        
        create_learning_progress(
            db=db,
            user_id=user_id,
            learning_point_id=learning_point_id,
            tier=determine_tier(entry['rank']),
            status='verified',
            learned_at=survey_completion_time
        )
```

**Pros:**
- Automatic, no user action needed
- Immediate integration
- Seamless user experience

**Cons:**
- Requires word → learning_point_id mapping
- May create duplicates if user retakes survey
- Need to handle edge cases

### Option 2: Conversion Endpoint

**Endpoint:** `POST /api/v1/survey/{session_id}/convert-to-progress`

**Process:**
- User explicitly triggers conversion
- Same logic as Option 1, but user-controlled

**Pros:**
- User has control
- Can review before converting
- Easier to debug

**Cons:**
- Extra step for user
- May be forgotten
- Less seamless

**Recommendation: Option 1 (Automatic) with Option 2 as fallback**

---

## Implementation Requirements

### 1. Word → Learning Point ID Mapping

**Challenge:** Survey uses word name, verification uses learning_point_id format.

**Format:**
- Survey: `word = "Establish"`
- Verification: `learning_point_id = "establish_v1"` (format: `{word}_{pos}{tier}`)

**Solution Options:**

**Option A: Query Neo4j**
```python
def map_word_to_learning_point_id(conn: Neo4jConnection, word: str, rank: int) -> str:
    """
    Find learning_point_id for a word.
    
    Strategy:
    1. Query Neo4j for LearningPoint with matching word
    2. Prefer Tier 1 (primary sense)
    3. Use frequency_rank to disambiguate if multiple
    """
    query = """
        MATCH (lp:LearningPoint {word: $word})
        WHERE lp.frequency_rank <= $rank + 100
           AND lp.frequency_rank >= $rank - 100
        RETURN lp.id as id, lp.tier as tier
        ORDER BY lp.tier ASC, lp.frequency_rank ASC
        LIMIT 1
    """
    # Execute query and return learning_point_id
```

**Option B: Use sense_id from survey**
- Survey history may contain `sense_id` (Neo4j Sense.id)
- Need to map Sense.id → LearningPoint.id
- May require additional Neo4j query

**Option C: Generate learning_point_id**
- Use format: `{normalized_word}_{pos}1`
- Assumes Tier 1, primary POS
- Risky if word has multiple senses

**Recommendation: Option A (Query Neo4j) - Most reliable**

### 2. Tier Determination

**Options:**
1. **Always Tier 1**: Survey words are typically Tier 1 (basic recognition)
2. **Based on rank**: Lower rank = Tier 1, higher rank = Tier 2
3. **Query Neo4j**: Get tier from LearningPoint node

**Recommendation: Query Neo4j** - Most accurate

### 3. Duplicate Handling

**Issue:** User may retake survey, creating duplicate entries.

**Solution:**
```python
# Use ON CONFLICT to handle duplicates
INSERT INTO learning_progress (user_id, learning_point_id, tier, status, learned_at)
VALUES (:user_id, :learning_point_id, :tier, 'verified', :learned_at)
ON CONFLICT (user_id, learning_point_id, tier) 
DO UPDATE SET
    status = 'verified',
    learned_at = GREATEST(learning_progress.learned_at, EXCLUDED.learned_at)
```

**Logic:**
- If entry exists, update to 'verified' status
- Keep earliest `learned_at` timestamp
- Prevents duplicates while preserving history

### 4. Status Field

**Options:**
- `'verified'`: Survey confirmed knowledge (recommended)
- `'learning'`: Treat as initial learning (less accurate)
- `'pending'`: Requires verification (defeats purpose)

**Recommendation: `'verified'`** - Survey is a form of verification

---

## Data Flow Diagram

```
Survey Completion
    ↓
survey_results saved (volume, reach, density)
    ↓
survey_history.history contains word-level data
    ↓
[INTEGRATION POINT]
    ↓
For each correct word in history:
    1. Query Neo4j: word → learning_point_id
    2. Determine tier
    3. Create learning_progress entry
    ↓
learning_progress entries created
    ↓
Verification system can now use these entries
```

---

## Example Integration Code

### Pseudo-code Implementation

```python
async def integrate_survey_to_verification(
    db: Session,
    neo4j_conn: Neo4jConnection,
    session_id: UUID,
    user_id: UUID
):
    """
    Convert survey results to learning_progress entries.
    
    Called automatically after survey completion.
    """
    # 1. Get survey history
    history_result = db.execute(
        text("""
            SELECT history FROM survey_history
            WHERE session_id = :session_id
        """),
        {"session_id": session_id}
    ).fetchone()
    
    if not history_result:
        logger.warning(f"No history found for session {session_id}")
        return
    
    history = history_result[0]  # JSONB array
    
    # 2. Get survey completion time
    session_result = db.execute(
        text("""
            SELECT start_time, updated_at FROM survey_sessions
            WHERE id = :session_id
        """),
        {"session_id": session_id}
    ).fetchone()
    
    completion_time = session_result[1] or session_result[0]
    
    # 3. Filter correct answers
    correct_entries = [
        entry for entry in history
        if entry.get('correct', False) and entry.get('word')
    ]
    
    logger.info(f"Found {len(correct_entries)} correct words to integrate")
    
    # 4. Create learning_progress entries
    created_count = 0
    skipped_count = 0
    
    for entry in correct_entries:
        word = entry['word']
        rank = entry.get('rank', 0)
        
        try:
            # Map word to learning_point_id
            learning_point_id = await map_word_to_learning_point_id(
                neo4j_conn=neo4j_conn,
                word=word,
                rank=rank
            )
            
            if not learning_point_id:
                logger.warning(f"Could not map word '{word}' to learning_point_id")
                skipped_count += 1
                continue
            
            # Determine tier (query Neo4j or use default)
            tier = await determine_tier(neo4j_conn, learning_point_id) or 1
            
            # Create learning_progress entry
            db.execute(
                text("""
                    INSERT INTO learning_progress 
                    (user_id, learning_point_id, tier, status, learned_at)
                    VALUES (:user_id, :learning_point_id, :tier, 'verified', :learned_at)
                    ON CONFLICT (user_id, learning_point_id, tier)
                    DO UPDATE SET
                        status = 'verified',
                        learned_at = GREATEST(learning_progress.learned_at, EXCLUDED.learned_at)
                """),
                {
                    "user_id": user_id,
                    "learning_point_id": learning_point_id,
                    "tier": tier,
                    "learned_at": completion_time
                }
            )
            
            created_count += 1
            
        except Exception as e:
            logger.error(f"Error creating learning_progress for word '{word}': {e}")
            skipped_count += 1
    
    db.commit()
    
    logger.info(
        f"Survey integration complete: {created_count} created, {skipped_count} skipped"
    )
    
    return {
        "created": created_count,
        "skipped": skipped_count,
        "total_correct": len(correct_entries)
    }


async def map_word_to_learning_point_id(
    neo4j_conn: Neo4jConnection,
    word: str,
    rank: int
) -> Optional[str]:
    """
    Map a word to its learning_point_id.
    
    Strategy:
    1. Query Neo4j for LearningPoint with matching word
    2. Prefer Tier 1 (primary sense)
    3. Use frequency_rank proximity to disambiguate
    """
    query = """
        MATCH (lp:LearningPoint)
        WHERE toLower(lp.word) = toLower($word)
           AND lp.frequency_rank >= $min_rank
           AND lp.frequency_rank <= $max_rank
        RETURN lp.id as id, lp.tier as tier, lp.frequency_rank as rank
        ORDER BY lp.tier ASC, abs(lp.frequency_rank - $target_rank) ASC
        LIMIT 1
    """
    
    with neo4j_conn.get_session() as session:
        result = session.run(
            query,
            word=word,
            min_rank=max(1, rank - 200),
            max_rank=min(8000, rank + 200),
            target_rank=rank
        )
        
        record = result.single()
        if record:
            return record["id"]
    
    return None


async def determine_tier(
    neo4j_conn: Neo4jConnection,
    learning_point_id: str
) -> Optional[int]:
    """Get tier from LearningPoint node."""
    query = """
        MATCH (lp:LearningPoint {id: $id})
        RETURN lp.tier as tier
    """
    
    with neo4j_conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        record = result.single()
        if record:
            return record["tier"]
    
    return None
```

---

## Testing Strategy

### Unit Tests

1. **Word mapping**
   - Test `map_word_to_learning_point_id()` with various words
   - Test edge cases (multiple senses, missing words)

2. **Integration logic**
   - Test with mock survey history
   - Test duplicate handling
   - Test error cases

### Integration Tests

1. **End-to-end flow**
   - Complete survey → check learning_progress entries
   - Verify correct words are created
   - Verify incorrect words are not created

2. **Duplicate handling**
   - Retake survey → verify no duplicates
   - Verify status updates correctly

### Edge Cases

1. **Missing words**: Word not in Neo4j
2. **Multiple senses**: Word has multiple learning points
3. **Empty history**: Survey completed but no history
4. **Partial completion**: Survey abandoned mid-way

---

## Next Steps

1. ✅ **Investigation complete** (this document)
2. ⏳ **Implement word mapping function** (`map_word_to_learning_point_id`)
3. ⏳ **Implement integration function** (`integrate_survey_to_verification`)
4. ⏳ **Add to survey completion flow** (automatic integration)
5. ⏳ **Add conversion endpoint** (optional manual trigger)
6. ⏳ **Write tests** (unit + integration)
7. ⏳ **Document API changes** (if endpoint added)

---

## References

- `backend/src/api/survey.py` - Survey completion flow
- `backend/src/survey/lexisurvey_engine.py` - Survey engine logic
- `backend/src/survey/models.py` - Survey data models
- `backend/migrations/002_survey_schema.sql` - Survey schema
- `backend/migrations/007_unified_user_model.sql` - learning_progress schema
- `backend/src/database/models.py` - LearningProgress model

---

## Appendix: Database Queries

### Get Survey History with Words

```sql
SELECT 
    sh.history,
    ss.user_id,
    ss.start_time,
    ss.updated_at
FROM survey_history sh
JOIN survey_sessions ss ON ss.id = sh.session_id
WHERE ss.id = :session_id
  AND ss.status = 'completed';
```

### Check Existing Learning Progress

```sql
SELECT 
    lp.learning_point_id,
    lp.tier,
    lp.status,
    lp.learned_at
FROM learning_progress lp
WHERE lp.user_id = :user_id
  AND lp.learning_point_id = :learning_point_id
  AND lp.tier = :tier;
```

### Count Integrated Words

```sql
SELECT COUNT(*) 
FROM learning_progress lp
JOIN survey_sessions ss ON ss.user_id = lp.user_id
WHERE lp.status = 'verified'
  AND lp.learned_at >= ss.start_time
  AND lp.learned_at <= ss.updated_at
  AND ss.id = :session_id;
```

