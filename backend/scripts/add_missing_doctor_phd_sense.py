#!/usr/bin/env python3
"""
Add Missing Doctor PhD Sense

Adds doctor.n.04 (PhD holder) sense to vocabulary.json.
This is a common meaning that was missed during initial sense selection.

Usage:
    python add_missing_doctor_phd_sense.py
"""

import json
from pathlib import Path
from datetime import datetime

VOCAB_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"

# Template for doctor.n.04 (PhD holder)
DOCTOR_PHD_SENSE = {
    "id": "doctor.n.04",
    "word": "doctor",
    "lemma": "doctor",
    "pos": "n",
    "frequency_rank": 10667,  # Same as doctor.n.01 (it's the same word)
    "moe_level": 1,
    "cefr": "B1",  # PhD is more advanced than medical doctor (A1)
    "tier": 2,
    "definition_en": "A doctor is also a person who has earned the highest degree from a university. They have a PhD (Doctor of Philosophy) or similar advanced degree. For example, someone who studies science for many years and writes a long research paper can become a doctor in that subject.",
    "definition_zh": "博士是指在大學獲得最高學位的人。他們擁有博士學位（哲學博士）或類似的進階學位。例如，長期研究科學並撰寫長篇研究論文的人可以成為該學科的博士。",
    "definition_zh_explanation": "「博士」在這裡指的是學術學位，而不是醫療專業。獲得博士學位需要完成多年的研究和論文寫作。",
    "translation_source": "ai",
    "example_en": "Dr. Chen is a doctor of physics. She spent eight years studying quantum mechanics. Her research helped scientists understand how particles behave. Now she teaches at the university and guides other students.",
    "example_zh_translation": "陳博士是物理學博士。她花了八年時間研究量子力學。她的研究幫助科學家了解粒子如何運作。現在她在大學教書並指導其他學生。",
    "example_zh_explanation": "這個例子展示了「博士」作為學術學位的用法。Dr. 是 Doctor 的縮寫，用於稱呼擁有博士學位的人。",
    "connections": {
        "synonyms": {
            "display_words": ["PhD", "PhD holder", "doctorate holder"],
            "sense_ids": []  # These might not exist in vocabulary
        },
        "antonyms": {
            "display_words": [],
            "sense_ids": []
        },
        "similar_words": {
            "display_words": ["professor", "researcher", "scholar"],
            "sense_ids": []
        },
        "confused_with": {
            "display_words": ["doctor.n.01"],  # Medical doctor
            "sense_ids": ["doctor.n.01"]
        }
    },
    "network": {
        "hop_1_count": 0,
        "hop_2_count": 0,
        "total_reachable": 0,
        "total_xp": 150  # Slightly higher than medical doctor (B1 vs A1)
    },
    "other_senses": ["doctor.n.01"],  # Link to medical doctor sense
}


def main():
    print("\n" + "="*60)
    print("➕ Adding Missing Doctor PhD Sense (doctor.n.04)")
    print("="*60 + "\n")
    
    # Load vocabulary
    print(f"📖 Loading {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    senses = data.get('senses', {})
    print(f"✅ Loaded {len(senses)} senses")
    
    # Check if already exists
    if "doctor.n.04" in senses:
        print("\n⚠️  doctor.n.04 already exists!")
        existing = senses["doctor.n.04"]
        print(f"   Current definition: {existing.get('definition_en', '')[:80]}...")
        response = input("\n   Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted.")
            return
    else:
        print("\n✅ doctor.n.04 not found - will add it")
    
    # Add the sense
    senses["doctor.n.04"] = DOCTOR_PHD_SENSE
    data['senses'] = senses
    
    # Save
    print(f"\n💾 Saving to {VOCAB_FILE}...")
    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Added doctor.n.04 (PhD holder)")
    print(f"\n📋 New sense details:")
    print(f"   CEFR: {DOCTOR_PHD_SENSE['cefr']}")
    print(f"   Definition: {DOCTOR_PHD_SENSE['definition_en'][:80]}...")
    print(f"\n💡 Note: You may want to:")
    print(f"   1. Run fix_sense_ids.py to populate synonym sense_ids")
    print(f"   2. Copy to frontend: cp {VOCAB_FILE} landing-page/public/vocabulary-v6-enriched.json")
    print(f"   3. Bump cache version in vocabularyDB.ts, vocab-loader.js, vocabularyLoader.ts")


if __name__ == "__main__":
    main()

