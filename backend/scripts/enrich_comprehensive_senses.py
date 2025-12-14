#!/usr/bin/env python3
"""
Selective Enrichment of High-Priority Senses

Enriches only critical missing senses (~5-8K) instead of all 25K new senses:
- Missing POS forms (e.g., "set" verb)
- Missing 2nd meanings of common words (e.g., "bank" river)
- NGSL words with missing senses

Uses both:
1. ESL-friendly definitions (from rewrite_definitions_esl.py)
2. Pedagogical connections (from enrich_with_gemini.py)

Cost: ~$25-50 for ~5-8K senses (not all 25K)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 20  # Process 20 senses per API call
MAX_WORKERS = 5  # Parallel API calls
RATE_LIMIT_DELAY = 6  # Seconds between API calls (10 requests/minute)
CHECKPOINT_INTERVAL = 50  # Save every 50 batches
INPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_comprehensive.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary_comprehensive.json"
CHECKPOINT_FILE = Path(__file__).parent.parent / "data" / "comprehensive_enrichment_checkpoint.json"
NGSL_FILE = Path(__file__).parent.parent.parent / "data" / "source" / "ngsl" / "NGSL_1.2_alphabetized_description.txt"

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in environment variables")
    print("Please set it in backend/.env file")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# Combined enrichment prompt (definitions + connections)
ENRICHMENT_PROMPT = """You are an ESL curriculum expert helping beginner English learners.

Enrich these vocabulary senses with ESL-friendly definitions and pedagogical connections.

{batch_json}

For EACH sense, provide:

1. **ESL-Friendly Definition**:
   - Use ONLY the simplest English words (A1-A2 level)
   - Match complexity to CEFR level
   - NO circular definitions
   - PRIORITIZE CLARITY OVER LENGTH (30 simple words > 10 complex words)
   - Generate 3-6 sentence coherent story examples (NOT random disconnected sentences)

2. **Pedagogical Connections**:
   - synonyms: 3-5 practical words learners can substitute
   - antonyms: 1-3 clear opposites (if applicable)
   - collocations: 5-8 authentic phrases with meanings and examples
   - word_family: Related forms across parts of speech
   - forms: Grammatical variations (comparative, superlative, past, plural, etc.)
   - similar_words: 2-4 words with similar but distinct meanings

CRITICAL RULES:
- Match or stay below the word's CEFR level
- Collocations must be natural/authentic
- For collocation examples: tell ONE coherent story (all sentences connect logically)
- sense_ids should match existing vocabulary entries when possible

Return ONLY valid JSON array (no markdown, no explanation):
[
  {{
    "sense_id": "set.v.01",
    "definition_en": "learner-friendly English definition using only simple words",
    "definition_zh": "繁體中文翻譯",
    "example_en": "3-6 sentences that tell ONE coherent story/scenario",
    "example_zh_translation": "中文翻譯（直譯）",
    "example_zh_explanation": "中文解釋（說明用法和含義）",
    "synonyms": {{
      "sense_ids": ["place.v.01", "put.v.01"],
      "display_words": ["place", "put", "position"]
    }},
    "antonyms": {{
      "sense_ids": ["remove.v.01"],
      "display_words": ["remove", "take away"]
    }},
    "collocations": [
      {{
        "phrase": "set the table",
        "cefr": "A2",
        "register": "neutral",
        "meaning": "to put plates, forks, and knives on the table before eating",
        "meaning_zh": "在吃飯前把盤子、叉子和刀子放在桌上",
        "example": "Every evening, my mother asks me to set the table. I put out four plates, four forks, and four knives. Then I call everyone to come eat dinner.",
        "example_en_explanation": "English uses 'set' to mean arranging objects in their proper place for a specific purpose. 'Set the table' is a fixed collocation meaning to prepare the dining table with dishes and utensils.",
        "example_zh_explanation": "英文用「set」表達「把物品放在正確位置以備使用」的概念。「set the table」是固定搭配，意思是準備餐桌（擺放餐具）。"
      }}
    ],
    "word_family": {{
      "noun": ["setting"],
      "verb": ["set"],
      "adjective": ["set"]
    }},
    "forms": {{
      "past": ["set"],
      "past_participle": ["set"]
    }},
    "similar_words": {{
      "sense_ids": ["place.v.01"],
      "display_words": ["place", "position"]
    }}
  }}
]
"""


def load_ngsl_words() -> Set[str]:
    """Load NGSL word list from text file."""
    if not NGSL_FILE.exists():
        print(f"⚠️  NGSL file not found: {NGSL_FILE}")
        return set()
    
    words = set()
    with open(NGSL_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Skip header lines (first 19 lines are description)
            if line_num <= 19:
                continue
            
            word = line.strip().lower()
            # Skip empty lines and lines that look like headers
            if word and not word.startswith('#') and not '\t' in word:
                # Take first word if there are multiple (tab-separated)
                word = word.split('\t')[0].split(',')[0]
                if word:
                    words.add(word)
    
    print(f"✅ Loaded {len(words)} NGSL words")
    return words


def extract_lemma(sense_id: str) -> str:
    """Extract lemma from sense_id."""
    return sense_id.split('.')[0] if '.' in sense_id else sense_id


def is_missing_pos_form(sense_id: str, all_senses: Dict[str, Dict], lemma: str) -> bool:
    """Check if this sense is a missing POS form (word has other POS, this one was missing)."""
    # Get all senses for this lemma
    lemma_senses = [s for sid, s in all_senses.items() if extract_lemma(sid) == lemma]
    
    if len(lemma_senses) <= 1:
        return False  # Only one sense, not a missing POS form
    
    # Check if this sense's POS is different from enriched senses
    enriched_pos = {s.get('pos') for s in lemma_senses if s.get('enriched')}
    this_pos = all_senses[sense_id].get('pos')
    
    # If this POS wasn't in enriched senses, it's a missing POS form
    return this_pos not in enriched_pos and len(enriched_pos) > 0


def is_common_word_missing_meaning(sense_id: str, sense: Dict, frequency_rank: Optional[int]) -> bool:
    """Check if this is a missing 2nd-3rd meaning of a common word."""
    if not frequency_rank or frequency_rank >= 5000:
        return False
    
    # Check if this is sense 2 or 3 (not the first sense)
    sense_num = int(sense_id.split('.')[-1]) if '.' in sense_id else 1
    return sense_num in (2, 3)


def is_ngsl_word_missing_sense(sense_id: str, sense: Dict, ngsl_words: Set[str]) -> bool:
    """Check if this is an NGSL word with a missing sense."""
    lemma = extract_lemma(sense_id)
    return lemma.lower() in ngsl_words


def prioritize_senses(
    unenriched_senses: List[tuple],
    all_senses: Dict[str, Dict],
    ngsl_words: Set[str]
) -> List[tuple]:
    """Prioritize senses for enrichment."""
    priority_1 = []  # Missing POS forms
    priority_2 = []  # Missing 2nd meanings of common words
    priority_3 = []  # NGSL words with missing senses
    priority_4 = []  # Others (by total_xp)
    
    for sense_id, sense in unenriched_senses:
        lemma = extract_lemma(sense_id)
        frequency_rank = sense.get('frequency_rank')
        total_xp = sense.get('value', {}).get('total_xp', 0)
        
        if is_missing_pos_form(sense_id, all_senses, lemma):
            priority_1.append((sense_id, sense, 1))
        elif is_common_word_missing_meaning(sense_id, sense, frequency_rank):
            priority_2.append((sense_id, sense, 2))
        elif is_ngsl_word_missing_sense(sense_id, sense, ngsl_words):
            priority_3.append((sense_id, sense, 3))
        else:
            priority_4.append((sense_id, sense, 4))
    
    # Sort each priority by total_xp (highest first)
    priority_1.sort(key=lambda x: -x[1].get('value', {}).get('total_xp', 0))
    priority_2.sort(key=lambda x: -x[1].get('value', {}).get('total_xp', 0))
    priority_3.sort(key=lambda x: -x[1].get('value', {}).get('total_xp', 0))
    priority_4.sort(key=lambda x: -x[1].get('value', {}).get('total_xp', 0))
    
    # Combine in priority order
    prioritized = priority_1 + priority_2 + priority_3 + priority_4
    
    print(f"\n📊 Prioritization:")
    print(f"   Priority 1 (Missing POS forms): {len(priority_1):,}")
    print(f"   Priority 2 (Missing 2nd meanings): {len(priority_2):,}")
    print(f"   Priority 3 (NGSL words): {len(priority_3):,}")
    print(f"   Priority 4 (Others by total_xp): {len(priority_4):,}")
    print(f"   Total high-priority: {len(priority_1) + len(priority_2) + len(priority_3):,}")
    
    return [(sid, s) for sid, s, _ in prioritized]


class ComprehensiveEnricher:
    """Enriches high-priority senses with Gemini."""
    
    def __init__(self, test_limit: Optional[int] = None):
        """
        Initialize enricher.
        
        Args:
            test_limit: If set, only process this many senses (for testing)
        """
        self.test_limit = test_limit
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        self.stats = {
            'total_senses': 0,
            'processed': 0,
            'failed': 0,
            'api_calls': 0,
        }
        self.failed_batches = []
    
    def load_vocabulary(self) -> Dict[str, Any]:
        """Load comprehensive vocabulary."""
        print(f"📖 Loading vocabulary from {INPUT_FILE}")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        senses = data.get('senses', {})
        self.stats['total_senses'] = len(senses)
        print(f"✅ Loaded {self.stats['total_senses']} senses")
        return data
    
    def prepare_batch(self, senses: List[tuple]) -> str:
        """Prepare a batch of senses for the API call."""
        batch_data = []
        for sense_id, sense in senses:
            batch_data.append({
                "sense_id": sense_id,
                "word": sense.get('word'),
                "lemma": sense.get('lemma', extract_lemma(sense_id)),
                "pos": sense.get('pos'),
                "cefr": sense.get('cefr', 'B1'),
                "definition": sense.get('definition_en', ''),
                "moe_level": sense.get('moe_level'),
            })
        return json.dumps(batch_data, indent=2)
    
    def enrich_batch(self, batch: List[tuple]) -> List[Dict]:
        """Enrich a batch of senses using Gemini."""
        batch_json = self.prepare_batch(batch)
        prompt = ENRICHMENT_PROMPT.format(batch_json=batch_json)
        
        try:
            self.stats['api_calls'] += 1
            response = self.model.generate_content(prompt)
            
            # Get response text
            response_text = response.text.strip()
            
            # Handle markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines[-1].strip() == '```':
                    lines = lines[:-1]
                response_text = '\n'.join(lines)
            
            # Try to fix incomplete JSON (if response was truncated)
            if not response_text.endswith(']'):
                # Try to find the last complete object
                last_bracket = response_text.rfind('}')
                if last_bracket > 0:
                    response_text = response_text[:last_bracket + 1] + ']'
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Ensure result is a list
            if not isinstance(result, list):
                result = [result]
            
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Response length: {len(response.text)} chars")
            print(f"Response preview (first 500): {response.text[:500]}")
            print(f"Response preview (last 500): {response.text[-500:]}")
            self.failed_batches.append([s[0] for s in batch])
            return []
        except Exception as e:
            print(f"❌ API error: {e}")
            self.failed_batches.append([s[0] for s in batch])
            return []
    
    def merge_enrichment(self, sense: Dict, enriched: Dict) -> Dict:
        """Merge enriched data into sense."""
        # Update definitions
        if enriched.get('definition_en'):
            sense['definition_en'] = enriched['definition_en']
        if enriched.get('definition_zh'):
            sense['definition_zh'] = enriched['definition_zh']
        if enriched.get('example_en'):
            sense['example_en'] = enriched['example_en']
        if enriched.get('example_zh_translation'):
            sense['example_zh_translation'] = enriched['example_zh_translation']
        if enriched.get('example_zh_explanation'):
            sense['example_zh_explanation'] = enriched['example_zh_explanation']
        
        # Update connections
        if 'connections' not in sense:
            sense['connections'] = {}
        
        # Keep old 'confused' field if exists
        old_confused = sense['connections'].get('confused', [])
        
        # Update with new connections
        if enriched.get('synonyms'):
            sense['connections']['synonyms'] = enriched['synonyms']
        if enriched.get('antonyms'):
            sense['connections']['antonyms'] = enriched['antonyms']
        if enriched.get('collocations'):
            sense['connections']['collocations'] = enriched['collocations']
        if enriched.get('word_family'):
            sense['connections']['word_family'] = enriched['word_family']
        if enriched.get('forms'):
            sense['connections']['forms'] = enriched['forms']
        if enriched.get('similar_words'):
            sense['connections']['similar_words'] = enriched['similar_words']
        
        # Keep confused if it exists
        if old_confused:
            sense['connections']['confused'] = old_confused
        
        # Mark as enriched
        sense['enriched'] = True
        
        # Recalculate value (connections may have changed)
        # Import the calculation function inline
        TIER_BASE_XP = {1: 100, 2: 250, 3: 500, 4: 1000, 5: 300, 6: 400, 7: 750}
        CONNECTION_BONUSES = {
            'related': 10, 'opposite': 10, 'phrases': 20, 'idioms': 30, 'morphological': 10,
            'synonyms': 10, 'antonyms': 10, 'similar_words': 10,
        }
        
        tier = sense.get('tier', 1)
        base_xp = TIER_BASE_XP.get(tier, 100)
        connections = sense.get('connections', {})
        
        connection_bonus = 0
        for conn_type, bonus in CONNECTION_BONUSES.items():
            if conn_type in connections:
                if isinstance(connections[conn_type], dict):
                    count = len(connections[conn_type].get('sense_ids', []))
                elif isinstance(connections[conn_type], list):
                    count = len(connections[conn_type])
                else:
                    count = 0
            else:
                count = 0
            connection_bonus += count * bonus
        
        sense['value'] = {
            'base_xp': base_xp,
            'connection_bonus': connection_bonus,
            'total_xp': base_xp + connection_bonus
        }
        
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
        print("🚀 Selective Enrichment of High-Priority Senses")
        print("="*60 + "\n")
        
        # Load data
        vocab_data = self.load_vocabulary()
        ngsl_words = load_ngsl_words()
        
        # Filter unenriched senses
        all_senses = vocab_data['senses']
        unenriched = [
            (sid, s) for sid, s in all_senses.items()
            if not s.get('enriched', False)
        ]
        
        print(f"📊 Found {len(unenriched)} unenriched senses")
        
        # Prioritize
        prioritized = prioritize_senses(unenriched, all_senses, ngsl_words)
        
        # Limit to high-priority (~5-8K) or test mode
        test_limit = getattr(self, 'test_limit', None)
        if test_limit:
            high_priority = prioritized[:test_limit]
            print(f"\n🧪 TEST MODE: Enriching top {len(high_priority)} senses")
            # Use smaller batch size for testing
            global BATCH_SIZE
            original_batch_size = BATCH_SIZE
            BATCH_SIZE = min(5, test_limit)  # Smaller batches for testing
        else:
            high_priority = prioritized[:8000]  # Top 8K
            print(f"\n🎯 Enriching top {len(high_priority)} high-priority senses")
        
        # Create batches
        batches = [
            high_priority[i:i+BATCH_SIZE]
            for i in range(0, len(high_priority), BATCH_SIZE)
        ]
        total_batches = len(batches)
        
        print(f"📦 Total batches: {total_batches} ({BATCH_SIZE} senses/batch)")
        print(f"🔧 Max workers: {MAX_WORKERS} (parallel processing)")
        print(f"💰 Estimated cost: ~${(total_batches * 0.002):.2f}\n")
        
        # Load checkpoint
        start_batch = self.load_checkpoint()
        
        # Process batches in parallel
        start_time = datetime.now()
        processed_batches = set()
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            
            # Submit batches
            for i, batch in enumerate(batches[start_batch:], start=start_batch):
                future = executor.submit(self.enrich_batch, batch)
                futures[future] = (i, batch)
            
            # Process results as they complete
            for future in as_completed(futures):
                batch_num, batch = futures[future]
                try:
                    enriched_results = future.result()
                    
                    # Merge results
                    for enriched in enriched_results:
                        sense_id = enriched.get('sense_id')
                        if sense_id and sense_id in all_senses:
                            all_senses[sense_id] = self.merge_enrichment(
                                all_senses[sense_id],
                                enriched
                            )
                            self.stats['processed'] += 1
                        else:
                            self.stats['failed'] += 1
                    
                    processed_batches.add(batch_num)
                    
                    # Progress update
                    completed = len(processed_batches)
                    progress = (completed / total_batches) * 100
                    print(f"⏳ Progress: {completed}/{total_batches} ({progress:.1f}%) | "
                          f"Processed: {self.stats['processed']} | "
                          f"Failed: {self.stats['failed']}")
                    
                    # Save checkpoint periodically (use max batch number processed)
                    if completed % CHECKPOINT_INTERVAL == 0:
                        max_batch = max(processed_batches)
                        self.save_checkpoint(vocab_data, max_batch)
                        
                except Exception as e:
                    print(f"❌ Error processing batch {batch_num}: {e}")
                    self.stats['failed'] += len(batch)
                    processed_batches.add(batch_num)
        
        # Final save
        self.save_checkpoint(vocab_data, total_batches)
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*60)
        print("✅ Enrichment Complete!")
        print("="*60)
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"📊 Processed: {self.stats['processed']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"📞 API calls: {self.stats['api_calls']}")
        print(f"💰 Estimated cost: ${self.stats['api_calls'] * 0.002:.2f}")


def run_daemon(test_limit: Optional[int] = None):
    """
    Run the enrichment in daemon mode with auto-restart.
    
    Will automatically resume and retry on failures.
    """
    print("=" * 60)
    print("🔄 DAEMON MODE - Auto-restart enabled")
    print("=" * 60)
    
    max_retries = 10
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        print(f"\n📍 Attempt {attempt + 1}/{max_retries}")
        
        try:
            enricher = ComprehensiveEnricher(test_limit=test_limit)
            enricher.run()
            
            print("\n✅ Enrichment completed successfully!")
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached, giving up.")
                return False
    
    print("❌ Enrichment failed after max retries")
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Selective Enrichment of High-Priority Senses')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run in daemon mode with auto-restart')
    parser.add_argument('--test', type=int, metavar='N',
                       help='Test mode: only process N senses (e.g., --test 20)')
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(test_limit=args.test)
    else:
        enricher = ComprehensiveEnricher(test_limit=args.test)
        enricher.run()

