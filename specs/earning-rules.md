# Earning Rules Specification

## Tier Definitions

### Tier 1: Basic Word Recognition
- **Rate**: $1.00 per word
- **Requirements**:
  - Word in most common context
  - Top 1,000 most common words
  - Single, primary meaning
- **Verification**: 
  - Recognition test (multiple choice)
  - 7-day verification cycle
  - Must pass Day 3, 7 tests
- **Example**: "apple" = fruit

### Tier 2: Multiple Meanings
- **Rate**: $2.50 per word
- **Requirements**:
  - Word with 2+ distinct meanings
  - Top 5,000 words
  - Must demonstrate all meanings
- **Verification**:
  - Multiple context tests
  - 14-day verification cycle
  - Must pass all context tests
- **Example**: "bank" = financial institution AND river edge

### Tier 3: Phrase/Collocation Mastery
- **Rate**: $5.00 per phrase
- **Requirements**:
  - Words in common phrases/collocations
  - Top 10,000 collocations
  - Must use word correctly in phrases
- **Verification**:
  - Phrase completion tests
  - Collocation error detection
  - 21-day verification cycle
- **Example**: "make a decision" (not "do a decision")

### Tier 4: Idiom/Expression Mastery
- **Rate**: $10.00 per idiom
- **Requirements**:
  - Idiomatic expressions
  - Top 1,000 idioms
  - Must understand figurative meaning
- **Verification**:
  - Figurative vs. literal meaning tests
  - Context-appropriate usage
  - 30-day verification cycle
- **Example**: "beat around the bush" = avoid being direct

### Tier 5: Morphological Mastery
- **Rate**: $3.00 per relationship
- **Requirements**:
  - Word family relationships
  - Prefix/suffix understanding
  - Top 5,000 morphological relationships
- **Verification**:
  - Prefix/suffix recognition
  - Word formation pattern tests
  - 14-day verification cycle
- **Example**: "direct" → "indirect" (knowing "in-" prefix)

### Tier 6: Register Mastery
- **Rate**: $4.00 per variant
- **Requirements**:
  - Formal vs. informal variants
  - Top 2,500 register pairs
  - Must use appropriate register
- **Verification**:
  - Register appropriateness tests
  - Context-based usage tests
  - 21-day verification cycle
- **Example**: "utilize" (formal) vs. "use" (informal)

### Tier 7: Advanced Context Mastery
- **Rate**: $7.50 per context
- **Requirements**:
  - Words in specialized contexts
  - Context-specific meaning
  - Multiple specialized contexts
- **Verification**:
  - Multi-context tests
  - Specialized usage tests
  - 30-day verification cycle
- **Example**: "bush" in "beat around the bush" vs. "bush" as plant

## Bonus Types

### Relationship Discovery Bonus
- **Amount**: $1.50
- **Trigger**: Discover relationship between known components
- **Example**: Know "direct" → discover "indirect" relationship → +$1.50

### Pattern Recognition Bonus
- **Amount**: $2.00
- **Trigger**: Recognize morphological or collocation pattern
- **Example**: Recognize "in-" prefix pattern → +$2.00

### Phrase Completion Bonus
- **Amount**: $3.00
- **Trigger**: Master phrase after learning component words
- **Example**: Learn "make" + "decision" → master "make a decision" → +$3.00

### Idiom Unlock Bonus
- **Amount**: $7.00
- **Trigger**: Unlock idiom after learning component words
- **Example**: Learn components → unlock "beat around the bush" → +$7.00

### Context Mastery Bonus
- **Amount**: $2.00
- **Trigger**: Master word in multiple contexts
- **Example**: Learn "bank" (financial) + "bank" (river) → +$2.00

### Pattern Mastery Bonus
- **Amount**: $5.00
- **Trigger**: Master pattern across 5+ words
- **Example**: Master "in-" prefix pattern with 5+ words → +$5.00

## Earning Calculation Rules

### Base Calculation
```
earning = tier_rate × component_count
```

### With Bonuses
```
earning = (tier_rate × component_count) + sum(bonuses)
```

### Example Calculation
```
Component: "beat around the bush" (idiom)
- Component words: beat ($1.00) + around ($1.00) + bush ($2.50) = $4.50
- Relationship discovery: indirect (+$1.50)
- Pattern recognition: in- prefix (+$2.00)
- Idiom unlock: beat around the bush (+$7.00)
- Idiom mastery: figurative meaning (+$3.00)
Total: $18.00
```

## Unlock Rules

### Progressive Unlock Schedule
- **Immediate (70%)**: After platform verification passes
- **30 days (20%)**: After community spot-check (optional)
- **60 days (10%)**: After retention verification passes

### Unlock Conditions
1. Component must pass all verification tests
2. Minimum verification cycle completed (7-30 days based on tier)
3. Retention check passed (if applicable)
4. No active disputes

### Recall Conditions
- Retention drops below 80% after 60 days
- Verification fraud detected
- User appeal successful (parent dispute)

## Earning Limits

### Per Component
- Maximum earning per component: $50.00
- Includes all tiers, bonuses, and achievements

### Per User
- No maximum limit
- Based on investment tier and learning progress

### Per Investment
- Basic ($5K): Tiers 1-2 only
- Standard ($10K): Tiers 1-4
- Premium ($15K): All tiers
- Elite ($25K): All tiers + specialized content

## Earning History Tracking

### Required Fields
- Component ID
- Tier
- Base amount
- Bonus amount
- Total amount
- Unlock timestamp
- Transfer timestamp
- Status (unlocked, transferred, recalled)

### Reporting
- Total earned
- Unlocked amount
- Transferred amount
- Available amount
- Earning breakdown by tier
- Bonus breakdown by type

## Dispute Resolution

### Parent Disputes
- Can dispute verification results
- Human review process
- Additional testing available
- Fair resolution within 7 days

### Platform Disputes
- Retention failure
- Verification fraud
- System errors
- Automatic recall if justified

## Next Steps

See `verification-rules.md` for verification requirements.

