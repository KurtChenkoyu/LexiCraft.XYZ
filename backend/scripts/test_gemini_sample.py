#!/usr/bin/env python3
"""
Test Gemini Enrichment - Small Sample

Tests the enrichment pipeline with just 40 words (2 batches).
"""

import json
import os
import sys
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 20
INPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_test_sample.json"

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in environment variables")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# Enrichment prompt
ENRICHMENT_PROMPT = """You are an expert ESL curriculum designer. Generate pedagogically useful vocabulary connections for these words:

{batch_json}

For EACH word, provide:

1. **synonyms**: 3-5 practical words learners can substitute (at/below CEFR level)
2. **antonyms**: 1-3 clear opposites (if applicable)
3. **collocations**: 5-8 authentic phrases with meanings, Chinese explanations, and contextual examples
   - phrase: the collocation itself
   - cefr: difficulty level (A1, A2, B1, B2, C1, C2)
   - register: formality level (formal, neutral, informal)
   - meaning: clear English definition suitable for learners
   - meaning_zh: Chinese translation of the meaning
   - example: 3-4 sentences that tell ONE coherent story/scenario (NOT random disconnected sentences)
   - example_en_explanation: Teach the ENGLISH mental model (for international learners)
     * Explain how English constructs this meaning conceptually
     * Connect to broader English patterns
     * Use metalinguistic vocabulary to teach English thinking
   - example_zh_explanation: Teach learners to think in English using Chinese as a guide
     * Explain the ENGLISH mental model/logic (NOT literal translation)
     * Show how English constructs this meaning conceptually
     * Connect to broader patterns when relevant
     * Help learners internalize English thinking, not translate word-by-word
4. **word_family**: Related forms (noun/verb/adjective/adverb)
5. **forms**: Grammatical variations
   - Adjectives: comparative, superlative (use "more/most" for long words)
   - Verbs: past, past_participle (include irregulars: do→did→done)
   - Nouns: plural (include irregulars: child→children, person→people)
6. **similar_words**: 2-4 words with similar but distinct meanings

CRITICAL RULES:
- Match or stay below CEFR level
- Natural collocations only (check if they sound right)
- Include irregular forms correctly (child→children, do→did→done)
- Skip fields that don't apply
- For collocation examples: tell ONE coherent story (all sentences must connect logically)

Return ONLY valid JSON array:
[
  {{
    "sense_id": "formal.a.01",
    "synonyms": {{
      "sense_ids": ["official.a.01"],
      "display_words": ["official", "proper"]
    }},
    "antonyms": {{
      "sense_ids": ["informal.a.01"],
      "display_words": ["informal", "casual"]
    }},
    "collocations": [
      {{
        "phrase": "formal education",
        "cefr": "B2",
        "register": "neutral",
        "meaning": "learning at official schools with teachers and certificates",
        "meaning_zh": "在正式學校接受有老師和證書的教育",
        "example": "My grandfather grew up in a small village. He never had formal education at school. Instead, he learned carpentry from his father. Today he can build beautiful furniture without any degree.",
        "example_en_explanation": "English uses 'formal' to mark activities that follow official rules and structures. 'Formal education' refers to learning within an institutional system (schools, teachers, certificates), as opposed to informal learning at home or work. This 'formal + noun' pattern appears throughout English to indicate structured, official activities.",
        "example_zh_explanation": "英文用「formal」來表達「有正式規則和結構」的概念。這個例子對比了學校系統的「formal education」（有老師、課程、證書的正式教育）和家庭傳承（informal learning）。注意英文常用「formal + 名詞」來表達「正式的、有規範的」事物，像是 formal dress（正式服裝）、formal meeting（正式會議）。"
      }},
      {{
        "phrase": "formal dress",
        "cefr": "B1",
        "register": "formal",
        "meaning": "special clothes worn for important events like weddings",
        "meaning_zh": "參加婚禮等重要場合穿的特別服裝",
        "example": "The invitation says formal dress required. That means you need to wear a suit or nice dress. Jeans and t-shirts are not allowed.",
        "example_en_explanation": "English uses 'formal' to indicate adherence to social standards for specific occasions. The collocation 'formal dress' signals clothing that meets the highest level of a dress code. English thinking treats different occasions as having different 'codes' (rules), with 'formal' being the most strict.",
        "example_zh_explanation": "英文用「formal」表達「符合特定場合規範」的概念。這個例子中，邀請函要求「formal dress」，意思是衣服必須符合正式場合的標準（西裝、禮服），而不是休閒服裝（牛仔褲、T恤）。英文思維是：不同場合有不同的「dress code」（穿著規範），formal 表示最高規格。"
      }}
    ],
    "word_family": {{
      "noun": ["formality"],
      "verb": ["formalize"],
      "adverb": ["formally"]
    }},
    "forms": {{
      "comparative": ["more formal"],
      "superlative": ["most formal"]
    }},
    "similar_words": {{
      "sense_ids": ["official.a.01"],
      "display_words": ["official"]
    }}
  }}
]
"""


def test_enrichment():
    """Test enrichment with a small sample."""
    print("\n" + "="*60)
    print("🧪 Testing Gemini Enrichment (40 words)")
    print("="*60 + "\n")
    
    # Load vocabulary
    print(f"📖 Loading vocabulary from {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    
    senses = list(vocab_data['senses'].items())
    print(f"✅ Loaded {len(senses)} total senses\n")
    
    # Take first 40 words (2 batches)
    test_senses = senses[:40]
    print(f"🔬 Testing with first 40 words (2 batches)\n")
    
    # Process each batch
    model = genai.GenerativeModel(
        'gemini-2.5-flash',  # Latest Flash model
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )
    )
    
    total_enriched = 0
    for batch_num in range(2):
        batch = test_senses[batch_num*BATCH_SIZE:(batch_num+1)*BATCH_SIZE]
        
        # Prepare batch
        batch_data = []
        for sense_id, sense in batch:
            batch_data.append({
                "sense_id": sense_id,
                "word": sense.get('word'),
                "pos": sense.get('pos'),
                "cefr": sense.get('cefr', 'B1'),
                "definition": sense.get('definition_en', sense.get('definition', ''))
            })
        
        batch_json = json.dumps(batch_data, indent=2)
        prompt = ENRICHMENT_PROMPT.format(batch_json=batch_json)
        
        print(f"⏳ Processing batch {batch_num + 1}/2...")
        
        try:
            response = model.generate_content(prompt)
            enriched_results = json.loads(response.text)
            
            # Merge results
            for enriched in enriched_results:
                sense_id = enriched.get('sense_id')
                if sense_id and sense_id in vocab_data['senses']:
                    sense = vocab_data['senses'][sense_id]
                    
                    # Keep old confused field
                    old_confused = sense.get('connections', {}).get('confused', [])
                    
                    # Update with new data
                    sense['connections'] = {
                        'confused': old_confused,
                        'synonyms': enriched.get('synonyms'),
                        'antonyms': enriched.get('antonyms'),
                        'collocations': enriched.get('collocations'),
                        'word_family': enriched.get('word_family'),
                        'forms': enriched.get('forms'),
                        'similar_words': enriched.get('similar_words'),
                    }
                    # Remove None values
                    sense['connections'] = {k: v for k, v in sense['connections'].items() if v}
                    
                    total_enriched += 1
                    
                    # Print first result as example
                    if total_enriched == 1:
                        print(f"\n📝 Example Result for '{sense.get('word')}':")
                        print(json.dumps(sense['connections'], indent=2, ensure_ascii=False))
            
            print(f"✅ Batch {batch_num + 1} complete ({len(enriched_results)} words)")
            
        except Exception as e:
            print(f"❌ Error in batch {batch_num + 1}: {e}")
            if hasattr(response, 'text'):
                print(f"Response: {response.text[:200]}")
    
    # Save test output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(vocab_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "="*60)
    print(f"✅ Test Complete!")
    print("="*60)
    print(f"📊 Enriched: {total_enriched}/40 words")
    print(f"📁 Output: {OUTPUT_FILE}")
    print(f"\n💡 Review the output file to verify quality before running full enrichment.")


if __name__ == "__main__":
    test_enrichment()

