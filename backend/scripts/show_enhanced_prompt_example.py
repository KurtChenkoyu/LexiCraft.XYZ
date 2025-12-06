"""
Example script showing what the enhanced prompt looks like.
Demonstrates the full context and conditional layers.
"""

import sys
sys.path.insert(0, '..')
from src.agent_stage2 import detect_cefr_level

# Example data for "bank" (financial institution)
example_data = {
    "sense_id": "bank.n.01",
    "word": "bank",
    "definition_en": "A financial institution that accepts deposits and makes loans",
    "definition_zh": "銀行",
    "part_of_speech": "noun",
    "existing_example_en": "I need to deposit money at the bank.",
    "existing_example_zh": "我需要在銀行存錢。",
    "usage_ratio": 0.85,
    "frequency_rank": 150,
    "moe_level": 3,
    "cefr": None,  # Will be inferred
    "is_moe_word": True,
    "phrases": ["bank account", "bank loan", "bank teller", "savings bank"],
    "relationships": {
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
}

# Detect CEFR level
target_level = detect_cefr_level(
    example_data["cefr"],
    example_data["moe_level"],
    example_data["frequency_rank"]
)

print("=" * 80)
print("ENHANCED PROMPT EXAMPLE")
print("=" * 80)
print()

# Build context sections
context_sections = [
    f"Target Sense: {example_data['sense_id']}",
    f'Word: "{example_data["word"]}"',
    f"Part of Speech: {example_data['part_of_speech']}",
    f"CEFR Level: {target_level} (inferred from MOE Level {example_data['moe_level']})",
    f"Taiwan MOE Level: {example_data['moe_level']}",
    "⚠️ This word appears in Taiwan MOE exam vocabulary",
    f"Frequency Rank: {example_data['frequency_rank']} (lower = more common)",
    f"⚠️ This is the PRIMARY sense (usage ratio: {example_data['usage_ratio']:.1%})",
    "",
    "Existing Example (from Level 1):",
    f"  EN: {example_data['existing_example_en']}",
    f"  ZH: {example_data['existing_example_zh']}",
    "  → Generate NEW examples that are DIFFERENT from this one",
    "",
    "Common Phrases for this sense:",
    f"  {', '.join(example_data['phrases'])}",
    "  → Consider using these phrases in examples if natural"
]

print("\n".join(context_sections))
print()
print("=" * 80)
print("PROMPT STRUCTURE")
print("=" * 80)
print()
print("1. CONTEXT SECTION (Rich Metadata)")
print("   ✅ Word, Sense ID, POS, CEFR Level, MOE Level")
print("   ✅ Frequency Rank, Usage Ratio")
print("   ✅ Existing Example Reference")
print("   ✅ Common Phrases")
print()
print("2. LANGUAGE REQUIREMENTS (Dynamic)")
print(f"   ✅ Target Level: {target_level}")
print("   ✅ Explicit simple English instructions")
print("   ✅ Sentence length constraints")
print("   ✅ Grammar awareness (POS)")
print()
print("3. LAYERS (Conditional - Hybrid Approach)")
print("   ✅ Layer 1: Always included")
print("   ✅ Layer 2: Included (has opposites)")
print("   ✅ Layer 3: Included (has similar)")
print("   ✅ Layer 4: Included (has confused)")
print()
print("4. RELATIONSHIP CONTEXT (With Definitions)")
print("   ✅ Opposites: withdraw (definition: to take money out), save (definition: to keep money)")
print("   ✅ Similar: financial institution (definition: an institution that provides financial services)")
print("   ✅ Confused: bank (definition: the land alongside a river, reason: Sound)")
print()
print("=" * 80)
print("BENEFITS")
print("=" * 80)
print()
print("✅ Dynamic CEFR level (not hardcoded)")
print("✅ Taiwan context awareness (MOE exam vocabulary)")
print("✅ Grammar correctness (POS awareness)")
print("✅ Example variety (references existing example)")
print("✅ Natural usage (includes common phrases)")
print("✅ Semantic clarity (relationship definitions)")
print("✅ Cost efficient (conditional layers)")
print("✅ Explicit instructions (simple English requirements)")

