# Pipeline V2 Revised Prompts - Full Review

**Date**: 2025-12-07  
**Status**: Ready for Review  
**Purpose**: Fix Chinese translation issues, add pedagogical approach, balance Taiwan context

---

## Executive Summary

### Changes Overview

| Module | Current Issue | Proposed Fix |
|--------|---------------|--------------|
| CC-CEDICT Lookup | Wrong translations (scoring picks irrelevant entries) | Better scoring + use as hints only |
| Translation Validator | Approves bad translations | Stricter validation + generate instead of validate |
| Example Generator | Too Taiwan-centric | Balanced context (universal + optional Taiwan) |
| Definition Simplifier | Missing explanation | Add `definition_zh_explanation` field |
| Example Generator | Missing explanation | Add `example_zh_explanation` field |
| All modules | No connection pathway logic | Add for idioms/non-literal meanings |

### Existing Data Decision

**Recommendation: Discard and regenerate**

Reasons:
1. ~8% Chinese translations are wrong (240+ senses)
2. Missing explanation fields entirely
3. Examples are overly Taiwan-centric
4. Regeneration cost is low (~$3 for 3,500 words)
5. Better to have consistent quality than mixed quality

---

## Module 1: CC-CEDICT Lookup (REVISED)

### Current Problem
```python
# Current: Picks entries where word appears ANYWHERE in definition
"therefore" → "糠" because "(of a radish etc) spongy (and therefore unappetising)"
"popular" → "愛玉冰" because "popular Taiwan snack"
```

### Proposed Fix

```python
# File: backend/src/data_sources/cc_cedict.py

# Add stop words to ignore
STOP_WORDS = {'a', 'an', 'the', 'of', 'to', 'in', 'on', 'at', 'for', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'etc', 'eg', 'ie', 'vs'}

def get_best_translation_for_definition(
    self, 
    word: str, 
    definition: str,
    pos: str = None
) -> Optional[str]:
    """
    Get the best Chinese translation matching a specific English definition.
    
    IMPROVED: 
    - Ignores stop words
    - Prioritizes entries where word is the PRIMARY meaning
    - Downranks entries where word is just in description text
    """
    entries = self.lookup(word)
    
    if not entries:
        return None
    
    # Filter definition words (excluding stop words)
    def_words = set(re.findall(r'\b[a-zA-Z]+\b', definition.lower()))
    def_words -= STOP_WORDS
    
    best_match = None
    best_score = 0
    
    for entry in entries:
        entry_def = entry['definition'].lower()
        entry_words = set(re.findall(r'\b[a-zA-Z]+\b', entry_def))
        entry_words -= STOP_WORDS
        
        # Calculate overlap score (excluding stop words)
        overlap = len(def_words & entry_words)
        score = overlap / max(len(def_words), 1)
        
        # BONUS: Word is the PRIMARY meaning (definition starts with word or is very short)
        if entry_def.strip().startswith(word.lower()) or entry_def.strip() == word.lower():
            score += 1.0  # Strong bonus for primary meaning
        elif len(entry_def) < 30 and word.lower() in entry_def:
            score += 0.5  # Bonus for short definition containing word
        
        # PENALTY: Word appears in parentheses or after "e.g." (descriptive, not primary)
        if f'({word.lower()}' in entry_def or f'e.g. {word.lower()}' in entry_def:
            score -= 0.3
        
        # PENALTY: Very long definition (likely word is just mentioned, not defined)
        if len(entry_def) > 100:
            score -= 0.2
        
        # POS bonus
        if pos:
            pos_indicators = {
                'n': ['noun', '(n)', '/n/'],
                'v': ['verb', '(v)', 'to '],
                'adj': ['adjective', '(adj)', '(a)'],
                'adv': ['adverb', '(adv)'],
            }
            for indicator in pos_indicators.get(pos, []):
                if indicator in entry_def:
                    score += 0.2
                    break
        
        if score > best_score:
            best_score = score
            best_match = entry['traditional']
    
    return best_match
```

### Expected Result
- "therefore" → "所以" (score: 1.5) instead of "糠" (score: 0.33)
- "popular" → "流行" or "受歡迎" instead of "愛玉冰"
- "month" → "月" instead of "上浣"

---

## Module 2: Translation Validator (REVISED)

### Current Problem
- Validates/approves CC-CEDICT translations even when wrong
- Only checks if translation "exists", not if it "matches"
- No strict quality checks

### Proposed Approach: Generate, Don't Just Validate

```python
# File: backend/src/ai/translator.py

def get_prompt_template(self) -> str:
    return """You are a Chinese translation expert for English vocabulary learning apps in Taiwan.

Target Word: {word}
Part of Speech: {pos}
English Definition: {definition}

{cc_cedict_section}

YOUR TASK:
Generate the BEST Traditional Chinese (繁體中文) translation for this specific meaning.

TRANSLATION REQUIREMENTS:
1. MATCH THE MEANING: The translation must match the SPECIFIC definition given, not just any meaning of the word.
2. TAIWAN MANDARIN: Use Taiwan Traditional Chinese (繁體中文), natural Taiwan usage.
3. APPROPRIATE LENGTH: 
   - For concrete nouns: 1-3 characters is fine (e.g., 銀行, 星星)
   - For abstract concepts: 2-6 characters (e.g., 因此, 機會)
   - For verbs/adjectives: include necessary particles if natural
4. NOT place names, brand names, or overly specific terms.
5. NOT single rare characters that learners wouldn't recognize.

QUALITY CHECKS (you MUST pass all):
- [ ] Does the translation match THIS specific definition?
- [ ] Would a Taiwan high school student understand this translation?
- [ ] Is it the most common translation for this meaning?
- [ ] Is it NOT a place name, proper noun, or brand?

CC-CEDICT OPTIONS (reference only, you may ignore if none fit):
{cc_cedict_options}

EXAMPLES:
- "popular" (liked by many) → "受歡迎的" or "流行的" (NOT "愛玉冰")
- "bank" (financial) → "銀行" (NOT "河岸")
- "bank" (river side) → "河岸" (NOT "銀行")
- "run" (move fast) → "跑" (NOT "經營")
- "therefore" (consequence) → "所以" or "因此" (NOT "糠")

Return a JSON object:
{{
    "translation": "繁體中文翻譯",
    "confidence": "high/medium/low",
    "reason": "Why this translation is correct",
    "rejected_options": ["Why CC-CEDICT option was wrong (if applicable)"]
}}
"""
```

### Key Changes
1. **Generate, don't validate** — AI creates translation, CC-CEDICT is just reference
2. **Explicit quality checks** — Must pass all checks
3. **Negative examples** — Show what NOT to do
4. **Confidence level** — Low confidence triggers manual review

---

## Module 3: Definition Simplifier (REVISED)

### Current Problem
- Only produces `definition_en` and `definition_zh` (single translation)
- Missing `definition_zh_explanation` (nuances, connection pathways)

### Proposed: Add Explanation Field

```python
# File: backend/src/ai/simplifier.py

def get_prompt_template(self) -> str:
    return """You are a vocabulary curriculum expert helping Taiwan B1/B2 students learn English.

Target Word: {word}
Part of Speech: {pos}
Original Definition: {original_definition}

YOUR TASK:
1. Simplify the definition to B1/B2 level English
2. Provide TWO Chinese versions:
   - TRANSLATION: Concise, direct translation (2-6 characters)
   - EXPLANATION: Helps learners understand the meaning deeply

SIMPLIFICATION RULES:
- Maximum 15 words
- Use common vocabulary (B1/B2 level)
- Avoid technical jargon
- Make it immediately understandable

CHINESE TRANSLATION:
- Concise: 2-6 characters typically
- Natural Taiwan Mandarin (繁體中文)
- Match THIS specific meaning

CHINESE EXPLANATION (CRITICAL):
- Helps learners UNDERSTAND the meaning
- Identifies nuances that might be missed
- For words with non-literal/extended meanings:
  * Show the CONNECTION from literal to extended meaning
  * Structure: original meaning → how it extends → final meaning
  * Example: "break" (opportunity) = "原本是打破、中斷的意思，引申為打破困境，獲得新機會"
  * NEVER use "不是...而是" (creates disconnection)
  * ALWAYS show the pathway: literal → metaphor → meaning

EXPLANATION STYLE (vary these):
- Direct: "原本的意思是...，在這裡引申為..." (original meaning...extends to...)
- Comparison: "就像..." (like...), "如同..." (as if...)
- Pathway: "從...的概念，延伸到..." (from...extends to...)
- Context: "在這個情境下，指的是..." (in this context, means...)

BAD EXPLANATION (avoid):
- "「break」在這裡不是指打破東西，而是指機會。" ❌ (disconnection)
- "字面上是...但實際上是..." ❌ (disconnection)

GOOD EXPLANATION:
- "「break」原本是打破、中斷的意思。想像你被困住了，突然出現一個缺口讓你通過，這個缺口就是你的機會。" ✅

Return a JSON object:
{{
    "definition_en": "Simplified English definition (max 15 words)",
    "definition_zh": "簡潔的中文翻譯",
    "definition_zh_explanation": "幫助理解的中文說明（包含連接路徑）"
}}
"""
```

### Output Schema Change
```python
@dataclass
class SimplifiedDefinition:
    definition_en: str
    definition_zh: str  # Concise translation
    definition_zh_explanation: str  # NEW: Understanding explanation
    is_simplified: bool
```

---

## Module 4: Example Generator (REVISED)

### Current Problem
- TOO Taiwan-centric (every example has 學測, 夜市, LINE)
- Missing `example_zh_explanation` (connection pathways)
- Code-switching awkward ("with my社團 performance")

### Proposed: Balanced Context + Explanation

```python
# File: backend/src/ai/example_gen.py

def get_prompt_template(self) -> str:
    return """Create an example sentence for a Taiwan B1/B2 vocabulary app.

Word: {word}
Meaning: {definition}
Part of Speech: {pos}

REQUIREMENTS:
1. LENGTH: 8-15 words (ideal: 10-12)
2. CLARITY: The meaning of "{word}" must be OBVIOUS from context
3. TONE: Natural, conversational (not formal or textbook-like)
4. GRAMMAR: Common patterns appropriate for B1/B2 level

CONTEXT BALANCE (important!):
- 60% UNIVERSAL: School, work, friends, daily activities, technology
- 40% TAIWAN-SPECIFIC: Only when it fits naturally

UNIVERSAL CONTEXTS (prefer these):
- School: studying, exams, homework, projects, classes
- Daily life: shopping, eating, transport, weather
- Social: friends, messaging, going out, weekends
- Work: jobs, meetings, tasks, colleagues

TAIWAN CONTEXTS (use naturally, don't force):
- Can mention: convenience stores, public transport, local food
- Don't force: 學測, 夜市, 珍珠奶茶 into every example
- Avoid code-switching: Don't mix English with Chinese words

GOOD EXAMPLES:
✅ "Be careful not to drop your phone!" (universal)
✅ "I stayed up late studying for the exam." (universal)
✅ "Let's meet at the coffee shop after class." (universal)
✅ "The MRT was really crowded this morning." (natural Taiwan reference)

BAD EXAMPLES:
❌ "I forgot about the 學測 when I saw the star." (forced Taiwan reference)
❌ "He dropped his phone on the 捷運!" (awkward code-switching)
❌ "After buying 珍珠奶茶, I felt happy." (forced reference)

CHINESE VERSIONS (provide TWO):
1. TRANSLATION (字面翻譯): Direct translation showing English structure
2. EXPLANATION (意思說明): 
   - Helps understand nuances
   - For idioms/non-literal meanings: Show connection pathway
   - Structure: literal meaning → metaphor → actual meaning
   - NEVER use "不是...而是" (creates disconnection)

EXPLANATION EXAMPLE (for "give me a break" = stop bothering me):
GOOD: "「break」原本是休息、中斷的意思。這裡是請對方中斷他的行為，讓你喘口氣。所以引申為「別煩我了」的意思。" ✅
BAD: "「break」在這裡不是指休息，而是指別煩我。" ❌

Return a JSON object:
{{
    "example_en": "The English example sentence with {word}.",
    "example_zh_translation": "字面翻譯（直接翻譯，顯示英文結構）",
    "example_zh_explanation": "意思說明（解釋nuances、連接路徑）",
    "context": "universal/taiwan/school/work/social"
}}

CRITICAL:
- The word "{word}" MUST appear in the example
- Both Chinese versions are REQUIRED
- Make the meaning crystal clear from context
"""
```

### Output Schema Change
```python
@dataclass
class GeneratedExample:
    example_en: str
    example_zh_translation: str  # Direct translation
    example_zh_explanation: str  # NEW: Understanding explanation
    context: str
    word_highlighted: bool
```

---

## Module 5: Example Validator (REVISED)

### Current Problem
- Only checks if word is in example
- Doesn't validate Chinese quality
- Doesn't check for disconnection patterns

### Proposed: Comprehensive Validation

```python
# File: backend/src/ai/validator.py

def get_prompt_template(self) -> str:
    return """You are a quality validator for a Taiwan vocabulary learning app.

Word: {word}
Definition: {definition}
Part of Speech: {pos}

Example to validate:
- English: {example_en}
- Chinese Translation: {example_zh_translation}
- Chinese Explanation: {example_zh_explanation}

VALIDATION CHECKLIST:

1. WORD USAGE:
   [ ] Word "{word}" appears in the example
   [ ] Word is used with the correct meaning (matches definition)
   [ ] Word is used naturally (not forced)

2. ENGLISH QUALITY:
   [ ] Length is appropriate (8-15 words)
   [ ] Grammar is correct
   [ ] Natural, conversational tone
   [ ] Meaning is clear from context

3. CHINESE TRANSLATION:
   [ ] Accurately translates the English
   [ ] Uses Taiwan Traditional Chinese (繁體中文)
   [ ] Natural expression (not word-for-word awkward)

4. CHINESE EXPLANATION:
   [ ] Helps understand the meaning
   [ ] For non-literal meanings: Shows connection pathway
   [ ] Does NOT contain "不是...而是" (disconnection)
   [ ] Does NOT contain "字面上...但實際上" (disconnection)
   [ ] Uses varied language (not always "想像一下")

5. CONTEXT:
   [ ] Relatable for Taiwan B1/B2 students
   [ ] Not overly Taiwan-specific (forced references)
   [ ] Not code-switching (混用中英文)

Return a JSON object:
{{
    "valid": true/false,
    "score": 0-100,
    "issues": ["List of issues found"],
    "suggestions": ["How to fix issues"],
    "disconnection_found": true/false
}}
"""
```

---

## Module 6: Sense Selector (MINOR UPDATES)

### Current State
- Works well for selecting appropriate senses
- Minor improvement: Add explanation for why sense was selected

### Proposed Addition

```python
# Add to output schema:
@dataclass
class SelectedSense:
    sense_id: str
    wordnet_definition: str
    rank: int  # 1 = most useful
    reason: str  # Why this sense was selected
    is_primary: bool  # Is this the primary/most common sense?
    usage_notes: str  # NEW: Notes about usage (formal/informal/slang)
```

---

## Data Model Changes

### Current Schema
```python
{
    "id": "bank.n.01",
    "word": "bank",
    "pos": "n",
    "cefr": "A2",
    "tier": 2,
    "definition_en": "...",
    "definition_zh": "銀行",  # Single field
    "example_en": "...",
    "example_zh": "...",  # Single field
    "validated": true,
    ...
}
```

### Proposed Schema
```python
{
    "id": "bank.n.01",
    "word": "bank",
    "pos": "n",
    "cefr": "A2",
    "tier": 2,
    "definition_en": "A place where you keep your money safe.",
    "definition_zh": "銀行",  # Concise translation
    "definition_zh_explanation": "存放金錢的金融機構，可以存款、提款、轉帳等。",  # NEW
    "example_en": "I need to go to the bank before it closes.",
    "example_zh_translation": "我需要在銀行關門前去一趟。",  # Renamed
    "example_zh_explanation": "「bank」在這裡是指銀行，一個處理金錢事務的地方。",  # NEW
    "validated": true,
    "validation_score": 95,  # NEW: 0-100 score
    ...
}
```

---

## Existing Data: Recommendation

### Option 1: Discard and Regenerate (RECOMMENDED)
- Cost: ~$3 USD for 3,500 words
- Time: ~10 hours
- Quality: Consistent, all new fields populated
- Risk: Low

### Option 2: Keep Examples, Regenerate Translations
- Keep: `example_en` (good quality)
- Regenerate: `definition_zh`, `example_zh_*` (add explanations)
- Complexity: Higher (need selective regeneration)
- Risk: Medium (mixed quality)

### Option 3: Keep All, Add Missing Fields
- Keep: Everything
- Add: `definition_zh_explanation`, `example_zh_explanation`
- Problem: Wrong translations remain (~8%)
- Risk: High (quality issues persist)

**RECOMMENDATION: Option 1 (Discard and Regenerate)**

Reasons:
1. Clean slate with consistent quality
2. All new fields populated correctly
3. Cost is minimal (~$3)
4. Time is acceptable (~10 hours)
5. No mixed quality issues

---

## Test Plan

### Phase 1: Prompt Testing (5 words)
Run on: "break", "bank", "run", "popular", "therefore"
Verify:
- [ ] Chinese translations are correct
- [ ] Explanations show connection pathways
- [ ] Examples are balanced (not too Taiwan-centric)
- [ ] No disconnection patterns ("不是...而是")

### Phase 2: Batch Testing (50 words)
Run on: Random sample of 50 words from word list
Verify:
- [ ] Translation accuracy > 95%
- [ ] Validation pass rate > 90%
- [ ] Context balance (60% universal, 40% Taiwan)
- [ ] Explanation quality

### Phase 3: Full Run (3,500 words)
Only proceed after Phase 1 and 2 pass.

---

## Implementation Order

1. **Fix CC-CEDICT scoring** (`cc_cedict.py`)
2. **Update Translator** (`translator.py`) — generate instead of validate
3. **Update Simplifier** (`simplifier.py`) — add explanation field
4. **Update Example Generator** (`example_gen.py`) — balance context + explanation
5. **Update Validator** (`validator.py`) — comprehensive checks
6. **Update Pipeline** (`enrich_vocabulary_v2.py`) — new schema
7. **Clear checkpoint** — start fresh
8. **Run Phase 1 test** (5 words)
9. **Review and adjust**
10. **Run Phase 2 test** (50 words)
11. **Full pipeline run**

---

## Questions for Review

Before implementing:

1. **Schema change OK?** Adding `definition_zh_explanation`, splitting example_zh
2. **Discard existing data OK?** Recommendation is to start fresh
3. **Context balance OK?** 60% universal, 40% Taiwan-specific
4. **Connection pathway approach OK?** From V1 prompts
5. **Test plan OK?** 5 words → 50 words → full run

---

## Appendix: Side-by-Side Comparison

### Example: "break" (opportunity)

| Field | Current (V2) | Proposed |
|-------|--------------|----------|
| definition_en | "an opportunity" | "A chance to do something good" |
| definition_zh | "機會" | "機會" |
| definition_zh_explanation | ❌ Missing | "「break」原本是打破、中斷的意思。想像你被困住了，突然出現一個缺口(break)讓你通過，這就是你的機會。" |
| example_en | "Getting that break in my career on the 捷運 was life-changing!" | "Getting that job was a real break for me." |
| example_zh | "在捷運上得到那個職涯機會真的改變了我的人生！" | ❌ Missing |
| example_zh_translation | ❌ Missing | "得到那份工作對我來說是個真正的機會。" |
| example_zh_explanation | ❌ Missing | "這裡的「break」不是休息的意思，而是指突破困境獲得的好機會。「real break」強調這是一個重要的轉機。" |

### Example: "therefore" (consequence)

| Field | Current (V2) | Proposed |
|-------|--------------|----------|
| definition_zh | "糠" ❌ | "所以" or "因此" ✅ |
| definition_zh_explanation | ❌ Missing | "表示因果關係，前面說了原因，後面接著說結果。" |

### Example: "popular" (liked by many)

| Field | Current (V2) | Proposed |
|-------|--------------|----------|
| definition_zh | "愛玉冰" ❌ | "受歡迎的" or "流行的" ✅ |
| definition_zh_explanation | ❌ Missing | "很多人喜歡的、廣受歡迎的意思。" |

