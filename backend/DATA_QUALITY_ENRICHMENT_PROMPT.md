# Improved Enrichment Prompt for Data Quality

This is an enhanced version of the enrichment prompt that addresses data quality issues like:
- Wrong/shared sense definitions (e.g., "brave" showing "cope" definition)
- Missing primary senses
- Lack of context for secondary meanings (e.g., "bread" = money slang)

## Current Prompt (Basic)

```python
prompt = f"""
You are an expert EFL curriculum developer for Taiwan.
Target Word: "{word}"

Below are the raw meanings (skeletons) for this word. 
Your task is to create the Content AND the Validation Engine for LexiCraft.

1. Filter: Keep only relevant senses for B1/B2 learners.
2. Enrich: 
   - Rewrite definition simply (B1/B2).
   - Translate definition to Traditional Chinese (Taiwan usage).
   - Write a modern example sentence + Traditional Chinese translation.

3. Validation Engine (CRITICAL):
   - Quiz: Create a HARDER-THAN-AVERAGE Multiple Choice Question (MCQ) for THIS specific sense. 
     - The distractors should be tricky (e.g., other meanings of the same word).
   - Mapped Phrases: Look at the list of phrases provided in the skeleton (if any). 
     - Which ones belong to THIS specific meaning? Map them.
     - If no phrases provided, suggest 1-2 common collocations for this sense.

Raw Skeletons:
{json.dumps(skeletons, indent=2)}

Return a strict JSON object matching the schema:
{{
    "senses": [
        {{
            "sense_id": "...",
            "definition_en": "...",
            "definition_zh": "...",
            "example_en": "...",
            "example_zh": "...",
            "quiz": {{
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": 0,
                "explanation": "..."
            }},
            "mapped_phrases": ["phrase 1", "phrase 2"]
        }}
    ]
}}
"""
```

## Improved Prompt (Addresses Data Quality Issues)

```python
prompt = f"""
You are an expert EFL curriculum developer for Taiwan, specializing in vocabulary instruction for B1/B2 learners.

Target Word: "{word}"

CRITICAL INSTRUCTIONS FOR DATA QUALITY:
1. PRIMARY SENSE PRIORITY: 
   - If a sense_id starts with "{word.lower()}" (e.g., "{word.lower()}.n.01"), this is the PRIMARY sense for this word.
   - PRIMARY senses should be enriched FIRST and with the MOST COMMON meaning.
   - If a sense_id does NOT start with "{word.lower()}" (e.g., "weather.v.01"), it is a SHARED sense from another word.
   - SHARED senses should only be included if they are genuinely relevant to "{word}" in common usage.
   - DO NOT use shared senses as the primary definition (e.g., don't define "brave" as "to cope with" from weather.v.01).

2. DEFINITION ACCURACY:
   - Each definition MUST accurately reflect the sense_id provided.
   - If the sense_id is "{word.lower()}.n.01", the definition should be the PRIMARY noun meaning of "{word}".
   - If the sense_id is "{word.lower()}.v.01", the definition should be the PRIMARY verb meaning of "{word}".
   - Cross-reference the WordNet definition in the skeleton to ensure accuracy.

3. CONTEXT & USAGE:
   - For PRIMARY senses: Provide clear, common usage examples.
   - For SECONDARY/SLANG senses (e.g., "bread" = money): 
     * Clearly indicate it's informal/slang in the definition.
     * Provide context in the example (e.g., "He makes a lot of bread" = money).
   - Include register markers when appropriate (formal/informal/slang).

4. POLYSEMY HANDLING:
   - If "{word}" has multiple valid meanings (e.g., "bread" = food AND money slang):
     * Enrich BOTH if they are common enough for B1/B2 learners.
     * Clearly distinguish them with context in examples.
     * Mark the primary meaning (most common) clearly.

Below are the raw WordNet meanings (skeletons) for "{word}":
{json.dumps(skeletons, indent=2)}

YOUR TASK:
1. IDENTIFY PRIMARY SENSES: 
   - Find all senses where sense_id starts with "{word.lower()}"
   - These are the PRIMARY meanings you MUST enrich.
   - Prioritize these over shared senses.

2. FILTER & ENRICH:
   - Keep only relevant senses for B1/B2 learners (max 3-5 most common).
   - For each sense:
     * Rewrite definition simply (B1/B2 level English).
     * Translate to Traditional Chinese (Taiwan usage, clear and natural).
     * Write a modern, natural example sentence in English.
     * Translate the example to Traditional Chinese.
     * If it's a secondary/slang meaning, add context (e.g., "非正式用語" for informal).

3. VALIDATION ENGINE:
   - Quiz: Create a challenging MCQ for THIS specific sense.
     * Distractors should include other meanings of "{word}" (if polysemous).
     * Make it clear which sense is being tested.
   - Mapped Phrases: Map skeleton phrases to the correct sense, or suggest common collocations.

4. QUALITY CHECK:
   - Verify the definition matches the sense_id (not a shared sense from another word).
   - Ensure examples are natural and modern (not outdated).
   - Confirm Chinese translations are clear and use Taiwan Traditional Chinese.

Return a strict JSON object matching this schema:
{{
    "senses": [
        {{
            "sense_id": "...",
            "definition_en": "...",
            "definition_zh": "...",
            "example_en": "...",
            "example_zh": "...",
            "quiz": {{
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": 0,
                "explanation": "..."
            }},
            "mapped_phrases": ["phrase 1", "phrase 2"]
        }}
    ]
}}

IMPORTANT: Only return senses that are genuinely relevant to "{word}" and appropriate for B1/B2 learners. 
Prioritize PRIMARY senses (sense_id starts with "{word.lower()}") over shared senses.
"""
```

## Key Improvements

1. **Primary Sense Priority**: Explicitly instructs to prioritize senses where `sense_id` starts with the word name.
2. **Definition Accuracy**: Warns against using shared senses as primary definitions.
3. **Context & Usage**: Requires clear indication of register (formal/informal/slang) and context for secondary meanings.
4. **Polysemy Handling**: Explicitly handles words with multiple valid meanings (like "bread").
5. **Quality Checks**: Adds verification steps to ensure definitions match sense_ids.

## Usage

Replace the prompt in `backend/src/agent.py` at line 73 with the improved version above.

