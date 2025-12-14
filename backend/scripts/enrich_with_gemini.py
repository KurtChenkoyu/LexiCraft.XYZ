#!/usr/bin/env python3
"""
Gemini-Powered ESL Vocabulary Enrichment

Generates pedagogically useful connections for ESL learners using Gemini 1.5 Flash.
Replaces poor-quality WordNet data with curated, learner-appropriate connections.

Cost: ~$1.50 for 10,470 words
Time: ~10-15 minutes
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 20  # Process 20 words per API call
MAX_WORKERS = 5  # Parallel API calls
CHECKPOINT_INTERVAL = 100  # Save every 100 batches
INPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_gemini.json"
CHECKPOINT_FILE = Path(__file__).parent.parent / "data" / "gemini_checkpoint.json"

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in environment variables")
    print("Please set it in backend/.env file")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# Enrichment prompt template
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
4. **word_family**: Related forms across parts of speech (noun/verb/adjective/adverb)
5. **forms**: Grammatical variations
   - For adjectives: comparative, superlative (use "more/most" for long words, NOT "formaler")
   - For verbs: past, past_participle (include irregulars: do→did→done)
   - For nouns: plural (include irregulars: child→children, person→people, foot→feet)
6. **similar_words**: 2-4 words with similar but distinct meanings

CRITICAL RULES:
- Match or stay below the word's CEFR level (don't use C2 words for A1 learners)
- Collocations must be natural/authentic (check if they sound right)
- No academic jargon for basic words
- For irregular forms, use correct grammar (child→children, NOT childs)
- Skip fields that don't apply (e.g., no plural for abstract nouns)
- sense_ids should match existing vocabulary entries when possible
- For collocation examples: tell ONE coherent story (all sentences must connect logically, about same people/situation)
- Chinese explanations must teach ENGLISH THINKING using Chinese as a bridge (not literal translation)
  * Explain how English constructs meaning conceptually
  * Connect to broader English patterns
  * Help learners think in English, not translate

Return ONLY valid JSON array (no markdown, no explanation):
[
  {{
    "sense_id": "formal.a.01",
    "synonyms": {{
      "sense_ids": ["official.a.01", "proper.a.02"],
      "display_words": ["official", "proper", "traditional"]
    }},
    "antonyms": {{
      "sense_ids": ["informal.a.01", "casual.a.01"],
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
      "noun": ["formality", "formalism"],
      "verb": ["formalize"],
      "adverb": ["formally"]
    }},
    "forms": {{
      "comparative": ["more formal"],
      "superlative": ["most formal"]
    }},
    "similar_words": {{
      "sense_ids": ["official.a.01"],
      "display_words": ["official", "ceremonial"]
    }}
  }}
]
"""


class GeminiEnricher:
    """Enriches vocabulary with Gemini-generated pedagogical data."""
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',  # Latest Flash model (upgraded from 1.5)
            generation_config=genai.GenerationConfig(
                temperature=0.3,  # Low for consistency
                response_mime_type="application/json"
            )
        )
        self.stats = {
            'total_words': 0,
            'processed': 0,
            'failed': 0,
            'api_calls': 0,
            'tokens_used': 0,
        }
        self.failed_batches = []
    
    def load_vocabulary(self) -> Dict[str, Any]:
        """Load vocabulary from JSON file."""
        print(f"📖 Loading vocabulary from {INPUT_FILE}")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        senses = data.get('senses', {})
        self.stats['total_words'] = len(senses)
        print(f"✅ Loaded {self.stats['total_words']} senses")
        return data
    
    def prepare_batch(self, senses: List[tuple]) -> str:
        """Prepare a batch of senses for the API call."""
        batch_data = []
        for sense_id, sense in senses:
            batch_data.append({
                "sense_id": sense_id,
                "word": sense.get('word'),
                "pos": sense.get('pos'),
                "cefr": sense.get('cefr', 'B1'),
                "definition": sense.get('definition_en', sense.get('definition', ''))
            })
        return json.dumps(batch_data, indent=2)
    
    def enrich_batch(self, batch: List[tuple]) -> List[Dict]:
        """Enrich a batch of senses using Gemini."""
        batch_json = self.prepare_batch(batch)
        prompt = ENRICHMENT_PROMPT.format(batch_json=batch_json)
        
        try:
            self.stats['api_calls'] += 1
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            result = json.loads(response.text)
            
            # Track token usage (approximate)
            self.stats['tokens_used'] += len(prompt) // 4 + len(response.text) // 4
            
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Response text: {response.text[:500]}")
            self.failed_batches.append([s[0] for s in batch])
            return []
        except Exception as e:
            print(f"❌ API error: {e}")
            self.failed_batches.append([s[0] for s in batch])
            return []
    
    def merge_connections(self, sense: Dict, enriched: Dict) -> Dict:
        """Merge enriched data into sense, keeping some old fields."""
        if 'connections' not in sense:
            sense['connections'] = {}
        
        # Keep old 'confused' field (useful for spelling errors)
        old_confused = sense['connections'].get('confused', [])
        
        # Replace with new Gemini data
        sense['connections'] = {
            'confused': old_confused,  # Keep from WordNet
            'synonyms': enriched.get('synonyms'),
            'antonyms': enriched.get('antonyms'),
            'collocations': enriched.get('collocations'),
            'word_family': enriched.get('word_family'),
            'forms': enriched.get('forms'),
            'similar_words': enriched.get('similar_words'),
        }
        
        # Remove None values
        sense['connections'] = {k: v for k, v in sense['connections'].items() if v}
        
        return sense
    
    def save_checkpoint(self, vocab_data: Dict, batch_num: int):
        """Save checkpoint for resuming."""
        checkpoint = {
            'batch_num': batch_num,
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'failed_batches': self.failed_batches
        }
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)
        
        # Also save current vocabulary state
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(vocab_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Checkpoint saved at batch {batch_num}")
    
    def load_checkpoint(self) -> int:
        """Load checkpoint if exists."""
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            self.stats = checkpoint.get('stats', self.stats)
            self.failed_batches = checkpoint.get('failed_batches', [])
            print(f"🔄 Resuming from batch {checkpoint['batch_num']}")
            return checkpoint['batch_num']
        return 0
    
    def run(self):
        """Main enrichment loop."""
        print("\n" + "="*60)
        print("🚀 Starting Gemini ESL Enrichment")
        print("="*60 + "\n")
        
        # Load vocabulary
        vocab_data = self.load_vocabulary()
        senses = list(vocab_data['senses'].items())
        
        # Check for checkpoint
        start_batch = self.load_checkpoint()
        
        # Create batches
        batches = [senses[i:i+BATCH_SIZE] for i in range(0, len(senses), BATCH_SIZE)]
        total_batches = len(batches)
        
        print(f"📦 Total batches: {total_batches} ({BATCH_SIZE} words/batch)")
        print(f"🔧 Max workers: {MAX_WORKERS}")
        print(f"💰 Estimated cost: ~${(total_batches * 0.003):.2f}\n")
        
        # Process batches
        start_time = datetime.now()
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            
            # Submit batches
            for i, batch in enumerate(batches[start_batch:], start=start_batch):
                future = executor.submit(self.enrich_batch, batch)
                futures[future] = (i, batch)
            
            # Process results
            for future in as_completed(futures):
                batch_num, batch = futures[future]
                enriched_results = future.result()
                
                # Merge results into vocabulary
                for enriched in enriched_results:
                    sense_id = enriched.get('sense_id')
                    if sense_id and sense_id in vocab_data['senses']:
                        vocab_data['senses'][sense_id] = self.merge_connections(
                            vocab_data['senses'][sense_id],
                            enriched
                        )
                        self.stats['processed'] += 1
                    else:
                        self.stats['failed'] += 1
                
                # Progress update
                progress = ((batch_num + 1) / total_batches) * 100
                print(f"⏳ Progress: {batch_num + 1}/{total_batches} ({progress:.1f}%) | "
                      f"Processed: {self.stats['processed']} | "
                      f"Failed: {self.stats['failed']}")
                
                # Save checkpoint
                if (batch_num + 1) % CHECKPOINT_INTERVAL == 0:
                    self.save_checkpoint(vocab_data, batch_num + 1)
        
        # Final save
        self.save_checkpoint(vocab_data, total_batches)
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*60)
        print("✅ Enrichment Complete!")
        print("="*60)
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"📊 Processed: {self.stats['processed']}/{self.stats['total_words']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"🌐 API calls: {self.stats['api_calls']}")
        print(f"📝 Tokens: ~{self.stats['tokens_used']:,}")
        print(f"💰 Cost: ~${(self.stats['tokens_used'] / 1_000_000 * 0.375):.2f}")
        print(f"\n📁 Output: {OUTPUT_FILE}")
        
        if self.failed_batches:
            print(f"\n⚠️  {len(self.failed_batches)} batches failed. "
                  f"Check {CHECKPOINT_FILE} for details.")


if __name__ == "__main__":
    enricher = GeminiEnricher()
    enricher.run()

