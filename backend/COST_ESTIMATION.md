# Cost Estimation for All Enrichment Processes

## Current Status (As of Latest Check)

- **Total Words**: 3,500
- **Enriched Words**: 1,231 (35.2%)
- **Pending Words**: 2,946
- **Total Senses**: 7,590
- **Enriched Senses**: 1,531 (20.2%)
- **Pending Senses**: 6,059

## Processing Configuration

- **Batch Size**: 10 words per API call (batched processing)
- **Model**: Gemini 2.0 Flash
- **Processing Method**: Batched agent (`agent_batched.py`)

## API Call Estimates

### For Remaining Words (2,946 words)

- **API Calls Needed**: 2,946 ÷ 10 = **~295 API calls** (rounded up)
- **Current Batch 2 Progress**: 152/680 words (22.4%) in ranks 1001-2000
- **Remaining Batches**:
  - Batch 2: ~528 words remaining (ranks 1001-2000)
  - Batch 3: ~1,000 words (ranks 2001-3000)
  - Batch 4: ~1,000 words (ranks 3001-3500)
  - Plus any words from Batch 1 that weren't completed

### For Complete Dataset (3,500 words)

- **Total API Calls**: 3,500 ÷ 10 = **350 API calls**
- **Already Completed**: ~123 API calls (1,231 words ÷ 10)

## Token Usage Estimates

Based on documentation and typical usage patterns:

### Per Word (Content Enrichment)
- **Input Tokens**: ~200-300 tokens per word
  - Prompt template: ~150 tokens
  - Word data (skeletons, phrases): ~50-150 tokens per word
- **Output Tokens**: ~200-300 tokens per word
  - Definition (EN + ZH): ~50 tokens
  - Example (EN + ZH): ~50 tokens
  - Quiz (question + 4 options + explanation): ~100 tokens
  - Mapped phrases: ~20 tokens
  - JSON structure: ~30 tokens

**Total per word**: ~400-600 tokens (average: **~500 tokens/word**)

### Per API Call (10 words batched)
- **Input Tokens**: ~2,000-3,000 tokens (10 words × 200-300)
- **Output Tokens**: ~2,000-3,000 tokens (10 words × 200-300)
- **Total per API call**: ~4,000-6,000 tokens (average: **~5,000 tokens/call**)

### Total Token Estimates

#### For Remaining Words (2,946 words)
- **Total Tokens**: 2,946 × 500 = **~1,473,000 tokens** (~1.47M tokens)
- **Input Tokens**: ~1,473,000 × 0.5 = **~736,500 tokens**
- **Output Tokens**: ~1,473,000 × 0.5 = **~736,500 tokens**

#### For Complete Dataset (3,500 words)
- **Total Tokens**: 3,500 × 500 = **~1,750,000 tokens** (~1.75M tokens)
- **Input Tokens**: ~875,000 tokens
- **Output Tokens**: ~875,000 tokens

## Cost Estimates

### Free Tier Limits

According to `GOOGLE_API_SETUP.md`:
- **60 requests per minute** (RPM)
- **1,500 requests per day** (RPD)
- **32,000 tokens per minute** (TPM)
- **1 million tokens per day** (TPD)

**Analysis for Remaining Work**:
- **API Calls**: 295 calls needed
- **Daily Limit**: 1,500 calls/day ✅ (sufficient)
- **Token Limit**: 1M tokens/day
- **Tokens Needed**: 1.47M tokens
- **Days Required**: 1.47M ÷ 1M = **~2 days** (if using free tier)

**Conclusion**: Free tier is **sufficient** for remaining work, but will take ~2 days due to daily token limits.

### Paid Tier Pricing

From `GOOGLE_API_SETUP.md`:
- **Input**: $0.000125 per 1K characters
- **Output**: $0.0005 per 1K characters

**Note**: Pricing is per 1K **characters**, not tokens. 
- 1 token ≈ 4 characters (rough estimate)
- So 1K tokens ≈ 4K characters

#### Cost Calculation (Paid Tier)

**For Remaining Words (2,946 words)**:
- Input: 736,500 tokens × 4 chars/token = 2,946,000 chars = 2,946 × 1K chars
  - Cost: 2,946 × $0.000125 = **~$0.37**
- Output: 736,500 tokens × 4 chars/token = 2,946,000 chars = 2,946 × 1K chars
  - Cost: 2,946 × $0.0005 = **~$1.47**
- **Total for Remaining**: **~$1.84**

**For Complete Dataset (3,500 words)**:
- Input: 875,000 tokens × 4 = 3,500,000 chars = 3,500 × 1K chars
  - Cost: 3,500 × $0.000125 = **~$0.44**
- Output: 875,000 tokens × 4 = 3,500,000 chars = 3,500 × 1K chars
  - Cost: 3,500 × $0.0005 = **~$1.75**
- **Total for Complete Dataset**: **~$2.19**

### Alternative Calculation (Using Token-Based Pricing)

If we use a more accurate token-to-cost conversion:
- Gemini 2.0 Flash pricing (approximate): ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens

**For Remaining Words**:
- Input: 0.7365M tokens × $0.075 = **~$0.06**
- Output: 0.7365M tokens × $0.30 = **~$0.22**
- **Total**: **~$0.28**

**For Complete Dataset**:
- Input: 0.875M tokens × $0.075 = **~$0.07**
- Output: 0.875M tokens × $0.30 = **~$0.26**
- **Total**: **~$0.33**

## Summary Table

| Scenario | Words | API Calls | Tokens | Free Tier | Paid Tier (Char) | Paid Tier (Token) |
|----------|-------|-----------|--------|-----------|------------------|-------------------|
| **Remaining** | 2,946 | ~295 | ~1.47M | ✅ 2 days | ~$1.84 | ~$0.28 |
| **Complete** | 3,500 | ~350 | ~1.75M | ✅ 2 days | ~$2.19 | ~$0.33 |
| **Already Done** | 1,231 | ~123 | ~0.62M | ✅ Free | ~$0.77 | ~$0.12 |

## Recommendations

### Option 1: Free Tier (Recommended)
- **Cost**: $0
- **Time**: ~2 days (due to 1M tokens/day limit)
- **Best for**: Budget-conscious, no rush

### Option 2: Paid Tier
- **Cost**: ~$0.28 - $1.84 (depending on pricing model)
- **Time**: ~5-6 hours (with rate limits: 60 requests/min)
- **Best for**: Faster completion, minimal cost

### Option 3: Hybrid Approach
- Use free tier during development/testing
- Switch to paid tier for final batches if needed
- **Estimated additional cost**: <$1

## Additional Processes (Not Included Above)

### Embeddings Generation
- **Tokens per word**: ~10 tokens
- **Total for 3,500 words**: ~35,000 tokens
- **Cost**: Negligible (~$0.01)

### Adversary Mining (Relationships)
- Already completed (Phase 3)
- No API costs for this phase

## Total Project Cost Estimate

**Complete Enrichment (3,500 words)**:
- Content Enrichment: **~$0.28 - $2.19** (depending on pricing model)
- Embeddings: **~$0.01**
- **Total**: **~$0.30 - $2.20**

**Budget Recommendation**: **$5 USD** (as per documentation) is more than sufficient.

## Notes

1. **Token estimates** are approximate and may vary based on:
   - Word complexity
   - Number of senses per word
   - Response length variations

2. **Free tier limits** may require:
   - Running processes overnight
   - Spreading work across multiple days
   - Handling 429 rate limit errors

3. **Paid tier** provides:
   - Higher rate limits
   - Faster completion
   - More predictable processing time

4. **Current progress** shows Batch 2 is 22.4% complete, so remaining work is primarily:
   - Complete Batch 2 (ranks 1001-2000)
   - Batch 3 (ranks 2001-3000)
   - Batch 4 (ranks 3001-3500)

