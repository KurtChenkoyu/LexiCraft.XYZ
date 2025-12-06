# Prompt Refinement: Strengthening Connection Pathways

**Date:** January 2025  
**Status:** ✅ Complete

---

## What Was Refined

### Problem Identified
After testing with real API calls, explanations were functional but:
- Brief and didn't show strong connection pathways
- Didn't clearly explain HOW literal meaning connects to idiomatic meaning
- Missing the pathway structure we saw in test script

### Solution: Enhanced Prompt Instructions

Added explicit instructions and examples to strengthen connection pathways:

---

## Key Enhancements Added

### 1. Explicit Pathway Structure
**Before:**
```
- Show the semantic pathway: how the literal meaning naturally leads to the idiomatic meaning
```

**After:**
```
- Create a natural CONNECTION and PATHWAY - show how the meaning flows from literal to idiomatic
- Show the semantic pathway clearly: literal meaning → metaphor/evolution → idiomatic meaning
```

**Impact:** Makes the pathway structure explicit and clear.

---

### 2. Specific Language Patterns
**Added:**
```
- Use diverse approaches:
  * Direct descriptions: "原本的意思是...，在這裡引申為..." (original meaning...extends to...)
  * Natural metaphors: "就像..." (like), "如同..." (as if) - embedded naturally in explanation
  * Examples: "例如..." (for example)
  * Comparisons: "可以想成..." (can think of it as)
  * Only use "想像一下" when it genuinely helps create a clear pathway
```

**Impact:** Gives concrete language patterns to use, not just abstract instructions.

---

### 3. Concrete Examples
**Added Good Example:**
```
"原本你被困住，前面有一道牆擋著你 (literal break)。這道牆突然出現一個缺口 
(metaphorical break)，讓你可以通過，繼續前進。所以「a break」就像是打破了阻礙你前進的
困境，給你帶來一個新的開始和更好的機會 (idiomatic meaning)。"

This shows: literal → metaphor → idiomatic (creates pathway, not disconnection)
```

**Added Bad Example:**
```
"「break」在這裡不是指打破東西，而是指一個好機會。" ❌

This creates disconnection ("不是...而是") instead of showing connection pathway
```

**Impact:** Shows exactly what we want (pathway) vs what we don't want (disconnection).

---

### 4. Stronger Emphasis on Connection
**Added:**
- Multiple reminders: "Create a natural CONNECTION and PATHWAY"
- Explicit structure: "literal meaning → metaphor/evolution → idiomatic meaning"
- Clear prohibition: "NEVER start with '不是...' or '字面上...但實際上'"
- Focus statement: "idioms are EXTENSIONS, help learners see the connection pathway"

**Impact:** Reinforces the connection approach throughout the prompt.

---

## Files Updated

1. ✅ `backend/src/agent.py` - Stage 1 prompts
2. ✅ `backend/src/agent_batched.py` - Stage 1 batched prompts
3. ✅ `backend/src/agent_stage2.py` - Stage 2 prompts (all sections)

---

## Expected Improvements

After these refinements, explanations should:
- ✅ Show clearer connection pathways (literal → metaphor → idiomatic)
- ✅ Use more varied language patterns
- ✅ Avoid disconnection statements
- ✅ Help learners understand HOW meanings connect, not just WHAT they mean

---

## Next Step: Test Again

**Recommended:**
```bash
# Reset and test again
python3 << 'EOF'
from src.database.neo4j_connection import Neo4jConnection
conn = Neo4jConnection()
with conn.get_session() as session:
    session.run("""
        MATCH (s:Sense {id: 'break.n.02'})
        SET s.enriched = null,
            s.definition_zh_translation = null,
            s.definition_zh_explanation = null,
            s.example_zh_translation = null,
            s.example_zh_explanation = null
    """)
EOF

python3 -m src.agent --word break --limit 1
```

Then check if explanations show stronger connection pathways.

---

**Status:** ✅ Refinements Complete  
**Ready for:** Testing with real API calls

