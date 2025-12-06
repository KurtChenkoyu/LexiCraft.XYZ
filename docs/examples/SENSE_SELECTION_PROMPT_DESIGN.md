# AI-First Sense Selection: Prompt Design

## The Problem with Current Approach

**Current Flow**:
```
WordNet.synsets("drop")[:3]  →  Whatever WordNet thinks is "top 3"
```

**Result**: Academic definitions, missing verbs, arbitrary selection

---

## Proposed: AI-Driven Sense Selection

### Step 1: Get ALL candidates from WordNet

```python
# Get all synsets for a word
all_synsets = wn.synsets("drop")  # Returns 20+ synsets

# Group by POS
grouped = {
    'n': [...],  # 8 noun senses
    'v': [...],  # 12 verb senses
}
```

### Step 2: Let AI Select Useful Senses

```python
SENSE_SELECTION_PROMPT = """
You are helping create a vocabulary learning app for Taiwan B1/B2 English students (國中/高中程度).

**Word**: {word}
**Frequency Rank**: {rank} (lower = more common)

**All possible meanings from dictionary**:
{all_senses_formatted}

**Your Task**:
Select the {num_senses} MOST USEFUL meanings for a Taiwan student learning English.

**Selection Criteria**:
1. PRACTICAL: Used in daily conversation, news, or school contexts
2. DISTINCT: Each meaning is clearly different from others
3. BALANCED: Include at least one verb usage if the word is commonly used as a verb
4. LEARNER-LEVEL: Avoid technical, scientific, or archaic meanings
5. TAIWAN-RELEVANT: Consider what contexts Taiwan students encounter

**Output Format (JSON)**:
{{
  "selected_senses": [
    {{
      "sense_id": "drop.v.01",
      "pos": "v",
      "reason": "Most common usage - letting something fall",
      "priority": 1
    }},
    {{
      "sense_id": "drop.n.03",
      "pos": "n", 
      "reason": "Common in news - 'a drop in prices'",
      "priority": 2
    }}
  ],
  "rejected_notable": [
    {{
      "sense_id": "drop.n.08",
      "reason": "Physics term - not useful for B1/B2"
    }}
  ]
}}
"""
```

### Example: "drop"

**Input to AI**:
```
Word: drop
Frequency Rank: 1726

All possible meanings:
1. drop.n.01 (n): a shape that is spherical and small
2. drop.n.02 (n): a small indefinite quantity of liquid  
3. drop.n.03 (n): a sudden sharp decrease in quantity
4. drop.n.04 (n): a steep descent
5. drop.n.05 (n): a free fall of distance
6. drop.v.01 (v): let fall to the ground
7. drop.v.02 (v): to fall vertically
8. drop.v.03 (v): go down in value
9. drop.v.04 (v): leave or abandon
10. drop.v.05 (v): stop doing something
... (15 more)
```

**AI Output**:
```json
{
  "selected_senses": [
    {
      "sense_id": "drop.v.01",
      "pos": "v",
      "reason": "Essential action verb - 'I dropped my phone'",
      "priority": 1
    },
    {
      "sense_id": "drop.n.03",
      "pos": "n",
      "reason": "Common in news/economy - 'price drop', 'temperature drop'",
      "priority": 2
    }
  ],
  "rejected_notable": [
    {
      "sense_id": "drop.n.01",
      "reason": "Too specific - 'spherical shape' rarely used"
    },
    {
      "sense_id": "drop.v.05",
      "reason": "Covered by 'stop' - not worth separate entry"
    }
  ]
}
```

---

## Step 3: Generate Learner-Appropriate Content

```python
CONTENT_GENERATION_PROMPT = """
You are creating vocabulary content for a Taiwan B1/B2 English learning app.

**Word**: {word}
**Selected Meaning**: {sense_definition}
**Part of Speech**: {pos}

**Generate the following content**:

1. **Learner Definition (English)**
   - Use simple B1/B2 vocabulary
   - Maximum 15 words
   - Start with the word class (noun/verb/adj)

2. **Chinese Translation (繁體中文)**
   - Natural Taiwan Mandarin, not textbook Chinese
   - Include common usage context if helpful

3. **Example Sentence (English)**
   - Relatable to Taiwan students (school, daily life, social media)
   - 8-15 words
   - Make the meaning OBVIOUS from context

4. **Example Translation (繁體中文)**
   - Natural, conversational
   - Match the tone of the English

**Output Format (JSON)**:
{{
  "definition_en": "...",
  "definition_zh": "...",
  "example_en": "...",
  "example_zh": "..."
}}
"""
```

### Example Output for "drop (v)"

```json
{
  "definition_en": "(verb) To let something fall from your hand or a higher place.",
  "definition_zh": "讓某物從手中或高處掉落",
  "example_en": "Be careful not to drop your phone - the screen might crack!",
  "example_zh": "小心別把手機摔了——螢幕可能會裂掉！"
}
```

### Example Output for "drop (n)"

```json
{
  "definition_en": "(noun) A sudden decrease in the amount or level of something.",
  "definition_zh": "數量或程度的突然下降",
  "example_en": "There was a big drop in temperature this morning.",
  "example_zh": "今天早上氣溫驟降。"
}
```

---

## Comparison: Before vs After

### Before (WordNet-First)

| Aspect | Result |
|--------|--------|
| Sense selection | Random top 3 from WordNet |
| Definitions | "a shape that is spherical and small" |
| Examples | May not match sense |
| POS coverage | Often misses verbs |
| Taiwan context | None |

### After (AI-First Hybrid)

| Aspect | Result |
|--------|--------|
| Sense selection | AI picks most useful |
| Definitions | "To let something fall" |
| Examples | Relatable, matches sense |
| POS coverage | Balanced across POS |
| Taiwan context | Built into prompts |

---

## Implementation Code Sketch

```python
# New pipeline: ai_sense_selector.py

from google.generativeai import GenerativeModel

class AISenseSelector:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model = GenerativeModel(model_name)
    
    def select_senses(self, word: str, frequency_rank: int, max_senses: int = 2) -> list:
        """Use AI to select the most useful senses for a word."""
        
        # 1. Get all WordNet synsets
        all_synsets = wn.synsets(word)
        
        # 2. Format for AI
        senses_formatted = self._format_synsets(all_synsets)
        
        # 3. Call AI
        prompt = SENSE_SELECTION_PROMPT.format(
            word=word,
            rank=frequency_rank,
            all_senses_formatted=senses_formatted,
            num_senses=max_senses
        )
        
        response = self.model.generate_content(prompt)
        
        # 4. Parse and return
        return self._parse_response(response.text)
    
    def generate_content(self, word: str, sense_id: str, sense_def: str, pos: str) -> dict:
        """Generate learner-appropriate content for a selected sense."""
        
        prompt = CONTENT_GENERATION_PROMPT.format(
            word=word,
            sense_definition=sense_def,
            pos=pos
        )
        
        response = self.model.generate_content(prompt)
        return self._parse_content(response.text)
```

---

## Quality Validation

### Automated Checks

```python
def validate_example_matches_sense(example: str, word: str, definition: str) -> bool:
    """Use AI to verify example matches intended meaning."""
    
    prompt = f"""
    Does this example sentence clearly demonstrate this meaning of "{word}"?
    
    Meaning: {definition}
    Example: "{example}"
    
    Answer YES if a student could understand the meaning from this example.
    Answer NO if the example is ambiguous or uses a different meaning.
    """
    
    response = model.generate_content(prompt)
    return "YES" in response.text.upper()
```

### Human Review Queue

```python
# Flag for human review if:
# 1. Word is in top 500 frequency
# 2. Auto-validation failed
# 3. Multiple similar senses exist
# 4. Word has sensitive meanings (race, politics, etc.)
```

---

## Expected Outcomes

| Metric | Current | Expected |
|--------|---------|----------|
| Sense usefulness | ~40% | ~90% |
| Example-sense match | ~60% | ~95% |
| Verb coverage | ~30% | ~80% |
| Taiwan relevance | ~20% | ~90% |
| Data quality issues | Constant | Rare |

---

*This is a design document. Implementation requires switching the pipeline from WordNet-first to AI-first.*

