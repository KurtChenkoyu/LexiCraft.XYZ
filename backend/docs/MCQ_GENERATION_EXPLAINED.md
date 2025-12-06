# MCQ Generation V2 - Context-Aware, Polysemy-Safe

## Overview

The MCQ Assembler V2 generates fair, helpful MCQs that:
1. **Always provide context** (example sentence)
2. **Avoid polysemy traps** (distractors from different words only)
3. **Are sense-specific** (test THIS meaning, not "any meaning")

---

## The Core Problems We Fixed

### Problem 1: No Context ❌ → Context Required ✅

**Before (V1):**
```
Q: "break" 在這個情境中是什麼意思？
A) 機會
B) 休息
C) 錯過
D) 煞車
```
Issue: What "情境"? There's no sentence!

**After (V2):**
```
Q: 在這個句子中，"break" 是什麼意思？
📖 Context: "Getting that job was a real break for him."

A) 機會 ✅
B) 錯過 [opposite: miss]
C) 煞車 [confused: brake]
D) 開始 [similar: start]
```
Fix: Context sentence is REQUIRED and displayed.

---

### Problem 2: Polysemy Trap ❌ → Different Words Only ✅

**Before (V1):**
```
Word: "break" (opportunity sense)
Distractors might include:
- 休息 (from "break" rest sense) ← WRONG! "break" CAN mean this!
```

**After (V2):**
```
Word: "break" (opportunity sense)
Distractors ONLY from DIFFERENT words:
- 錯過 (from "miss") ← OK, different word
- 煞車 (from "brake") ← OK, different word
- 開始 (from "start") ← OK, different word

EXCLUDED:
- 休息 (from "break" different sense) ← Excluded, same word!
```

---

### Problem 3: USAGE MCQ Too Generic ❌ → Sense-Specific ✅

**Before (V1):**
```
Q: 哪一個句子正確使用了 "break"？
```
Issue: ALL sentences might correctly use "break" (in different senses)!

**After (V2):**
```
Q: 哪一個句子中的 "break" 表示「機會」？
```
Fix: Question specifies WHICH meaning we're asking about.

---

## MCQ Types

### Type 1: MEANING (with Context)

Tests if learner knows what the word means **in the given context**.

```
┌─────────────────────────────────────────────────────────────────┐
│ Q: 在這個句子中，"break" 是什麼意思？                           │
│                                                                 │
│ 📖 "Getting that job was a real break for him."                 │
│                                                                 │
│ A) 機會；好運           [target: break]            ✅           │
│ B) 錯過；失去           [opposite: miss]                        │
│ C) 煞車；制動           [confused: brake]                       │
│ D) 開始；啟動           [similar: start]                        │
│                                                                 │
│ 💡 正確答案是「機會；好運」。在句子「Getting that job was a     │
│    real break for him.」中，"break" 表示「機會；好運」。        │
└─────────────────────────────────────────────────────────────────┘
```

**Key features:**
- Context sentence is REQUIRED
- Distractors from DIFFERENT words only
- Each option shows source word

### Type 2: USAGE (Sense-Specific)

Tests if learner can identify which sentence shows **this specific meaning**.

```
┌─────────────────────────────────────────────────────────────────┐
│ Q: 哪一個句子中的 "break" 表示「機會」？                        │
│                                                                 │
│ A) Getting that job was a real break for him. ✅                │
│ B) I need a break from work. [confused: rest]                   │
│ C) He missed his chance. [opposite: miss]                       │
│ D) The brake pedal is stuck. [confused: brake]                  │
│                                                                 │
│ 💡 正確答案是：「Getting that job was a real break for him.」   │
│    這個句子中的 "break" 表示「機會」。                          │
└─────────────────────────────────────────────────────────────────┘
```

**Key features:**
- Question specifies the target meaning
- All sentences may be grammatically correct (but only one shows this sense)

### Type 3: DISCRIMINATION (Different Words)

Tests if learner can distinguish between **genuinely different words**.

```
┌─────────────────────────────────────────────────────────────────┐
│ Q: 請選擇正確的詞填入空格：                                     │
│                                                                 │
│ 📖 "Getting that job was a real _____ for him."                 │
│                                                                 │
│ A) break               [target]                  ✅             │
│ B) brake               [confused: Sound-alike]                  │
│ C) rest                [confused: Semantic]                     │
│ D) 以上皆非                                                     │
│                                                                 │
│ 💡 正確答案是 "break"。                                         │
│    "break" 和 "brake" 容易混淆（Sound-alike）。                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key features:**
- Fill-in-the-blank format
- Distractors are DIFFERENT WORDS that are commonly confused
- NOT a polysemy test

---

## The Distractor Hierarchy

```
Priority 1: CONFUSED_WITH (Best)
├── Different words commonly confused
├── Example: "affect" vs "effect"
└── Highest pedagogical value

Priority 2: OPPOSITE_TO (Good)
├── Different words with opposite meaning
├── Example: "deposit" vs "withdraw"
└── Tests understanding of meaning boundaries

Priority 3: RELATED_TO (Careful)
├── Synonyms - may be too similar
├── Example: "start" vs "begin"
└── Use sparingly, check for near-duplicates

EXCLUDED: Same word, different sense (Polysemy)
├── "break" (opportunity) vs "break" (rest)
├── This would be unfair - both are valid meanings!
└── Never use as distractors
```

---

## Polysemy Safety Logic

```python
def _fetch_distractors_safe(self, word, target_sense_id, other_senses):
    """
    Fetch distractors from DIFFERENT WORDS only.
    
    CRITICAL: Excludes definitions from:
    1. Other senses of the SAME word (polysemy trap!)
    2. Definitions too similar to the correct answer
    """
    
    # Step 1: Collect definitions from other senses of SAME word
    same_word_definitions = set()
    for sense in other_senses:
        same_word_definitions.add(sense["definition_zh"])
    
    # Step 2: Fetch from CONFUSED_WITH (different words)
    # Skip any that match same_word_definitions
    
    # Step 3: Return only definitions from DIFFERENT words
```

---

## Example: Testing "break"

**Word:** "break"
**Senses:**
1. `break.n.01` - 機會；好運 (opportunity)
2. `break.n.02` - 休息；暫停 (rest)
3. `break.v.01` - 打破；弄壞 (damage)

**For sense `break.n.01` (opportunity):**

```
Target definition: 機會；好運

EXCLUDED (same word, different sense):
- 休息；暫停 (from break.n.02) ← CANNOT use as distractor!
- 打破；弄壞 (from break.v.01) ← CANNOT use as distractor!

VALID distractors (different words):
- 錯過 (from "miss" - OPPOSITE_TO)
- 煞車 (from "brake" - CONFUSED_WITH)
- 開始 (from "start" - RELATED_TO)
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCQ GENERATION V2                           │
└─────────────────────────────────────────────────────────────────┘

1. INPUT: Sense ID (e.g., "break.n.01")
   │
   ▼
2. FETCH SENSE DATA
   ├── Target definition: "機會；好運"
   ├── Context sentence: "Getting that job was a real break..."
   └── Other senses of same word: [break.n.02, break.v.01, ...]
   │
   ▼
3. FETCH SAFE DISTRACTORS
   ├── Query CONFUSED_WITH → ["brake", "rest"]
   ├── Query OPPOSITE_TO → ["miss", "lose"]
   ├── Query RELATED_TO → ["opportunity", "chance"]
   │
   ├── FILTER: Remove definitions that match other senses of "break"
   │   └── Exclude: 休息, 打破 (from break's other senses)
   │
   └── Result: Only definitions from DIFFERENT words
   │
   ▼
4. GENERATE MCQs
   ├── MEANING MCQ (with context!)
   ├── USAGE MCQ (sense-specific!)
   └── DISCRIMINATION MCQ (different words!)
   │
   ▼
5. OUTPUT: Fair, Polysemy-Safe MCQs
```

---

## Testing

```bash
# Test polysemy safety
python3 -m scripts.test_mcq_assembler --word break

# Full MCQ output
python3 -m scripts.test_mcq_assembler --word break --full

# Test specific sense
python3 -m src.mcq_assembler --sense break.n.01
```

---

## Philosophy Recap

> **"Help, not confuse"**

- ✅ Context: Always show the sentence so learner knows WHICH meaning
- ✅ Fair distractors: From different words, not polysemy traps
- ✅ Sense-specific: Test THIS meaning, not "any meaning of the word"
- ✅ Transparent: Show where each distractor came from
- ❌ Never: Use other senses of same word as "wrong" answers
- ❌ Never: Ask about "correct usage" when multiple senses could fit
