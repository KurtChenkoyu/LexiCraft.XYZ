"""
Show actual prompt output from enhanced prompt builder.
Demonstrates what the LLM receives.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the relationships and context data
relationships = {
    "opposites": [
        {"word": "withdraw", "definition_en": "to take money out of an account", "definition_zh": "提取"},
        {"word": "save", "definition_en": "to keep money for future use", "definition_zh": "儲存"}
    ],
    "similar": [
        {"word": "financial institution", "definition_en": "an institution that provides financial services", "definition_zh": "金融機構"}
    ],
    "confused": [
        {"word": "bank", "definition_en": "the land alongside a river", "definition_zh": "河岸", "reason": "Sound"}
    ]
}

# Simulate the prompt building logic
sense_id = "bank.n.01"
word = "bank"
definition_en = "A financial institution that accepts deposits and makes loans"
definition_zh = "銀行"
part_of_speech = "noun"
existing_example_en = "I need to deposit money at the bank."
existing_example_zh = "我需要在銀行存錢。"
usage_ratio = 0.85
frequency_rank = 150
moe_level = 3
cefr = None
is_moe_word = True
phrases = ["bank account", "bank loan", "bank teller", "savings bank"]

# Detect CEFR level
def detect_cefr_level(cefr, moe_level, frequency_rank):
    if cefr:
        return cefr
    if moe_level:
        moe_to_cefr = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}
        return moe_to_cefr.get(moe_level, "B1/B2")
    if frequency_rank:
        if frequency_rank < 500:
            return "A1/A2"
        elif frequency_rank < 2000:
            return "B1/B2"
        else:
            return "C1/C2"
    return "B1/B2"

target_level = detect_cefr_level(cefr, moe_level, frequency_rank)

# Determine which layers need API calls (hybrid approach)
has_opposites = bool(relationships["opposites"])
has_similar = bool(relationships["similar"])
has_confused = bool(relationships["confused"])

# Build relationship context strings WITH definitions
if has_opposites:
    opposites_list = []
    for opp in relationships["opposites"]:
        opp_str = f'  * "{opp["word"]}" (definition: "{opp.get("definition_en", "")}")'
        opposites_list.append(opp_str)
    opposites_str = "\n".join(opposites_list)
else:
    opposites_str = "None"

if has_similar:
    similar_list = []
    for sim in relationships["similar"]:
        sim_str = f'  * "{sim["word"]}" (definition: "{sim.get("definition_en", "")}")'
        similar_list.append(sim_str)
    similar_str = "\n".join(similar_list)
else:
    similar_str = "None"

if has_confused:
    confused_list = []
    for conf in relationships["confused"]:
        conf_str = f'  * "{conf["word"]}" (definition: "{conf.get("definition_en", "")}", reason: {conf.get("reason", "Unknown")})'
        confused_list.append(conf_str)
    confused_str = "\n".join(confused_list)
else:
    confused_str = "None"

# Build context sections
context_sections = [f"Target Sense: {sense_id}", f'Word: "{word}"']

if part_of_speech:
    context_sections.append(f"Part of Speech: {part_of_speech}")

if cefr:
    context_sections.append(f"CEFR Level: {cefr}")
elif target_level:
    context_sections.append(f"CEFR Level: {target_level} (inferred)")

if moe_level:
    context_sections.append(f"Taiwan MOE Level: {moe_level}")
    if is_moe_word:
        context_sections.append("⚠️ This word appears in Taiwan MOE exam vocabulary")

if frequency_rank:
    context_sections.append(f"Frequency Rank: {frequency_rank} (lower = more common)")

if usage_ratio:
    if usage_ratio > 0.7:
        context_sections.append(f"⚠️ This is the PRIMARY sense (usage ratio: {usage_ratio:.1%})")
    elif usage_ratio < 0.3:
        context_sections.append(f"Note: This is a LESS COMMON sense (usage ratio: {usage_ratio:.1%})")

if existing_example_en:
        context_sections.append(f"\nExisting Example (from Level 1):")
    context_sections.append(f"  EN: {existing_example_en}")
    if existing_example_zh:
        context_sections.append(f"  ZH: {existing_example_zh}")
    context_sections.append("  → Generate NEW examples that are DIFFERENT from this one")

if phrases:
    context_sections.append(f"\nCommon Phrases for this sense:")
    context_sections.append(f"  {', '.join(phrases[:5])}")
    context_sections.append("  → Consider using these phrases in examples if natural")

context_str = "\n".join(context_sections)

# Build prompt sections conditionally (hybrid approach)
prompt_sections = []

# Base instructions
base_instructions = f"""
You are an expert EFL curriculum developer for Taiwan, specializing in vocabulary instruction for {target_level} learners.

{context_str}

Definition (EN): {definition_en}
Definition (ZH): {definition_zh}

CRITICAL LANGUAGE REQUIREMENTS:
- Use SIMPLE, CLEAR English suitable for {target_level} level learners
- Keep sentences short (10-20 words maximum for {target_level})
- Use common, everyday words that {target_level} learners would know
- Avoid complex grammar structures beyond {target_level} level
- Make examples immediately understandable without explanation
"""

additional_notes = []

if is_moe_word and moe_level:
    additional_notes.append(f"- Pay special attention: This word is in Taiwan MOE exam vocabulary (Level {moe_level})")

if usage_ratio and usage_ratio > 0.7:
    additional_notes.append(f"- This is the PRIMARY sense ({usage_ratio:.1%} usage) - make examples very clear")
elif usage_ratio and usage_ratio < 0.3:
    additional_notes.append(f"- This is a less common sense ({usage_ratio:.1%} usage) - provide clear context")

if additional_notes:
    base_instructions += "\n".join(additional_notes) + "\n"

if part_of_speech:
    base_instructions += f"\nGRAMMAR NOTE: This is a {part_of_speech.upper()}. Examples must use correct {part_of_speech} grammar.\n"

if existing_example_en:
    base_instructions += f"\nREFERENCE: You already have this example: \"{existing_example_en}\"\n"
    base_instructions += "  → Generate DIFFERENT examples that show other contexts/uses\n"

base_instructions += "\nYour task is to generate example sentences organized into pedagogical layers:\n"

prompt_sections.append(base_instructions)

# Layer 1: Always included (REQUIRED)
layer1_section = f"""
1. CONTEXTUAL SUPPORT (REQUIRED - 2-3 examples):
   - Provide 2-3 natural, modern example sentences that clearly illustrate this sense
   - Use SIMPLE English: short sentences, common words, clear structure
   - Show different contexts/registers if appropriate (formal, casual, written, spoken)
   - Each example should solidify understanding of this specific sense
   - Examples must be immediately understandable to {target_level} learners
   - Avoid complex grammar or vocabulary beyond {target_level} level
"""

if phrases:
    layer1_section += f"   - Consider using phrases like: {', '.join(phrases[:3])}\n"

prompt_sections.append(layer1_section)

# Layer 2: Only if opposites exist
if has_opposites:
    layer2_section = f"""
2. OPPOSITE EXAMPLES:
{opposites_str}
   
   - For each antonym listed above, generate 1-2 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the antonym word in a natural sentence
     * Show clear contrast with the target sense
     * Highlight what aspect of the target sense is being contrasted
     * Make the distinction clear to help learners understand the difference
     * Keep language simple enough for {target_level} learners to understand immediately
   
   - Example structure:
     Target sense: "I deposited money at the bank." (simple, clear)
     Contrast: "He withdrew money from the bank." (shows opposite action: depositing vs withdrawing)
"""
    prompt_sections.append(layer2_section)

# Layer 3: Only if similar exist
if has_similar:
    layer3_section = f"""
3. SIMILAR EXAMPLES:
{similar_str}
   
   - For each synonym listed above, generate 1-2 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the synonym word in a natural sentence
     * Show subtle differences from the target sense
     * Help learners understand when to use this word vs. the synonym
     * Highlight the nuance between similar meanings
     * Keep language simple enough for {target_level} learners to understand immediately
   
   - Example structure:
     Target sense: "I opened an account at the bank." (simple, clear)
     Similar: "I opened an account at the financial institution." (shows synonym, but "bank" is more common/casual)
"""
    prompt_sections.append(layer3_section)

# Layer 4: Only if confused exist
if has_confused:
    layer4_section = f"""
4. CONFUSED EXAMPLES:
{confused_str}
   
   - For each confused word listed above, generate 1-2 examples that:
     * Use SIMPLE English: short, clear sentences with common words
     * Use the confused word in a natural sentence
     * Clearly show the distinction from the target sense
     * Address the specific confusion reason (Sound/Spelling/L1/Usage)
     * Help Taiwan EFL learners avoid common errors
     * Keep language simple enough for {target_level} learners to understand immediately
   
   - Example structure:
     Target sense: "I need to deposit money at the bank." (simple, clear)
     Confused: "The river bank was flooded." (clarifies: financial bank vs river bank)
"""
    prompt_sections.append(layer4_section)

# Common requirements
common_requirements = f"""
CRITICAL REQUIREMENTS:
- All examples must use SIMPLE, CLEAR English suitable for {target_level} level learners
- Keep sentences short (10-20 words maximum)
- Use common, everyday vocabulary
- Avoid complex grammar structures, idioms, or advanced vocabulary
- All examples must be natural, modern English (not outdated)
- All Chinese translations must be Traditional Chinese (Taiwan usage)
- Examples must clearly illustrate the target sense
- For Layers 2-4, the relationship words MUST appear in the examples
- Make examples immediately understandable without explanation

Return a strict JSON object matching this schema:
{{
    "sense_id": "{sense_id}",
    "examples_contextual": [
        {{
            "example_en": "...",
            "example_zh": "...",
            "context_label": "formal" | "casual" | "written" | "spoken" | null
        }},
        ...
    ],
"""

# Add schema sections conditionally
if has_opposites:
    common_requirements += """
    "examples_opposite": [
        {{
            "example_en": "...",
            "example_zh": "...",
            "relationship_word": "...",
            "relationship_type": "opposite"
        }},
        ...
    ],
"""

if has_similar:
    common_requirements += """
    "examples_similar": [
        {{
            "example_en": "...",
            "example_zh": "...",
            "relationship_word": "...",
            "relationship_type": "similar"
        }},
        ...
    ],
"""

if has_confused:
    common_requirements += """
    "examples_confused": [
        {{
            "example_en": "...",
            "example_zh": "...",
            "relationship_word": "...",
            "relationship_type": "confused"
        }},
        ...
    ],
"""

common_requirements += f"""
}}

IMPORTANT: 
- Generate 2-3 contextual examples (Layer 1) - REQUIRED
- Generate examples for Layers 2-4 ONLY if relationship words are provided (not "None")
- If a layer has no relationships, return empty array []
- All relationship words must appear in their respective examples
- Use SIMPLE English: short sentences, common words, clear structure
- All examples must be immediately understandable to {target_level} learners
"""

prompt_sections.append(common_requirements)

# Combine all sections
prompt = "\n".join(prompt_sections)

print("=" * 80)
print("FULL ENHANCED PROMPT (What the LLM Receives)")
print("=" * 80)
print()
print(prompt)
print()
print("=" * 80)
print(f"Prompt Length: {len(prompt)} characters")
print(f"Layers Included: Layer 1 (always) + {'Layer 2 ' if has_opposites else ''}{'Layer 3 ' if has_similar else ''}{'Layer 4 ' if has_confused else ''}")
print("=" * 80)

