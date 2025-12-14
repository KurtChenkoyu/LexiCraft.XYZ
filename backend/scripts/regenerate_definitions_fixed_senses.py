#!/usr/bin/env python3
"""
ESL Definition Regeneration Script for Fixed Senses

Regenerates ESL-friendly definitions for 1,992 senses where the word field was corrected.
Uses Gemini API with context from old_definition to understand which specific sense to define.

Cost: ~$0.30-0.50 for 1,992 senses
Time: ~30-60 minutes
"""

import json
import os
import sys
import time
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 20  # Process 20 senses per API call
MAX_WORKERS = 5  # Parallel API calls
CHECKPOINT_INTERVAL = 100  # Save every 100 batches
INPUT_SENSES_FILE = Path(__file__).parent.parent / "data" / "senses_needing_definition_regen.json"
VOCABULARY_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "vocabulary.json"
FRONTEND_FILE = Path(__file__).parent.parent.parent / "landing-page" / "public" / "vocabulary-v6-enriched.json"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"
CHECKPOINT_FILE = Path(__file__).parent.parent / "data" / "definition_regen_checkpoint.json"

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in environment variables")
    print("Please set it in backend/.env file")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# Definition regeneration prompt template
DEFINITION_REGEN_PROMPT = """You are an ESL curriculum expert helping beginner English learners.

Regenerate definitions for vocabulary words where the word field was corrected to the canonical lemma.

{batch_json}

For EACH sense, regenerate the definition following these CRITICAL RULES:

1. **The "word" is a LEMMA (base form)** - your definition must work for ALL inflections:
   - Example: "press" (verb) → definition works for "press", "presses", "pressed", "pressing"
   - Example: "experience" (verb) → definition works for "experience", "experiences", "experienced", "experiencing"
   - Write the definition using the base form, but make it clear it applies to all forms

2. **The "intended_meaning" describes which specific sense to define**:
   - The word field was wrong before (it was a synonym/variant)
   - The "intended_meaning" tells you exactly which sense/meaning we want
   - Use this to understand the correct sense, even if the word was different

3. Use ONLY the simplest English words (A1-A2 level, like: be, have, do, go, come, see, know, think, say, tell, show, give, take, put, get, make, use, find, work, call, try, ask, need, want, like, help, thing, person, people, place, time, way, real, true, clear, simple, easy, hard, good, bad, new, old, big, small, long, short, high, low, right, wrong, different, same, important, possible, not, all, some, many, few, more, most, very, too, also, only, just, about, with, for, from, to, in, on, at, by, of)

4. Match complexity to CEFR level:
   - A1-A2 words: Use ONLY A1 words in definition
   - B1-B2 words: Use A1-A2 words in definition
   - C1-C2 words: Use A1-B1 words in definition

5. NO circular definitions - don't use the word itself to define itself

6. **PRIORITIZE CLARITY OVER LENGTH**:
   - It's better to use 30 simple words than 10 complex words
   - Add context if it helps understanding
   - Use examples within the definition if needed
   - Don't sacrifice clarity for brevity

7. Make definitions concrete and clear - use everyday situations and common examples

8. For beginner ESL learners (not children) - use simple, complete English explanations

9. Generate 3-6 sentence coherent story examples (NOT random disconnected sentences). All sentences must connect logically, about the same people/situation.

EXAMPLES:
❌ BAD: "to exert pressure" (uses "exert" - too complex, unclear)
✅ GOOD: "to push hard on something with your hands" (uses simple words, clear)

❌ BAD: "rap with the knuckles" (uses "rap" and "knuckles" - confusing)
✅ GOOD: "to hit a door or surface with your hand to get someone's attention" (clear, complete)

Return ONLY valid JSON array (no markdown, no explanation):
[
  {{
    "sense_id": "press.v.01",
    "definition_en": "learner-friendly English definition using only simple words - clarity is more important than length. Remember: this is a LEMMA, so the definition should work for all forms (press, presses, pressed, pressing).",
    "definition_zh": "繁體中文翻譯",
    "example_en": "3-6 sentences that tell ONE coherent story/scenario using this word. All sentences must connect logically, about the same people/situation.",
    "example_zh_translation": "中文翻譯（直譯，顯示英文結構）",
    "example_zh_explanation": "中文解釋（說明這個詞在這個例子中的用法和含義）"
  }}
]
"""


class DefinitionRegenerator:
    """Regenerates ESL-friendly definitions for fixed senses using Gemini."""
    
    def __init__(self, test_mode: bool = False, limit: Optional[int] = None, dry_run: bool = False):
        self.test_mode = test_mode
        self.limit = limit
        self.dry_run = dry_run
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=genai.GenerationConfig(
                temperature=0.3,  # Low for consistency
                response_mime_type="application/json"
            )
        )
        self.stats = {
            'total_senses': 0,
            'processed': 0,
            'failed': 0,
            'api_calls': 0,
            'tokens_used': 0,
            'skipped_no_sense': 0,
            'skipped_no_definition': 0,
        }
        self.failed_batches = []
        self.vocab_data = None
    
    def extract_lemma(self, sense_id: str) -> str:
        """Extract lemma from sense_id (e.g., 'press.v.01' -> 'press')."""
        return sense_id.split('.')[0] if '.' in sense_id else sense_id
    
    def load_input_senses(self) -> List[Dict]:
        """Load the list of senses needing definition regeneration."""
        print(f"📖 Loading input senses from {INPUT_SENSES_FILE}")
        if not INPUT_SENSES_FILE.exists():
            print(f"❌ Error: {INPUT_SENSES_FILE} not found")
            sys.exit(1)
        
        with open(INPUT_SENSES_FILE, 'r', encoding='utf-8') as f:
            senses = json.load(f)
        
        self.stats['total_senses'] = len(senses)
        print(f"✅ Loaded {self.stats['total_senses']} senses needing regeneration")
        return senses
    
    def load_vocabulary(self) -> Dict[str, Any]:
        """Load vocabulary from JSON file to get current sense data."""
        print(f"📖 Loading vocabulary from {VOCABULARY_FILE}")
        if not VOCABULARY_FILE.exists():
            print(f"❌ Error: {VOCABULARY_FILE} not found")
            sys.exit(1)
        
        with open(VOCABULARY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab_data = data
        print(f"✅ Loaded vocabulary with {len(data.get('senses', {}))} senses")
        return data
    
    def prepare_batch(self, input_senses: List[Dict]) -> List[Dict]:
        """Prepare a batch of senses for the API call."""
        batch_data = []
        for sense_info in input_senses:
            sense_id = sense_info.get('sense_id')
            if not sense_id:
                self.stats['skipped_no_sense'] += 1
                continue
            
            # Get current sense from vocabulary.json if it exists
            current_sense = self.vocab_data.get('senses', {}).get(sense_id, {})
            
            # Get example usage from current sense if available
            example_usage = current_sense.get('example_en', '')
            
            batch_data.append({
                "sense_id": sense_id,
                "word": sense_info.get('new_word', ''),  # The lemma (base form)
                "pos": sense_info.get('pos', ''),
                "cefr": sense_info.get('cefr', 'B1'),
                "intended_meaning": sense_info.get('old_definition', ''),  # Describes which sense
                "example_usage": example_usage  # Optional, from vocabulary.json
            })
        return batch_data
    
    def regenerate_batch(self, batch: List[Dict]) -> List[Dict]:
        """Regenerate definitions for a batch of senses using Gemini."""
        batch_data = self.prepare_batch(batch)
        if not batch_data:
            return []
        
        try:
            # Format batch as JSON for prompt
            batch_json = json.dumps(batch_data, indent=2, ensure_ascii=False)
            prompt = DEFINITION_REGEN_PROMPT.format(batch_json=batch_json)
            
            self.stats['api_calls'] += 1
            response = self.model.generate_content(prompt)
            
            # Parse JSON response (should be an array)
            results = json.loads(response.text)
            
            # Ensure results is a list
            if not isinstance(results, list):
                results = [results]
            
            # Track token usage (approximate)
            self.stats['tokens_used'] += len(prompt) // 4 + len(response.text) // 4
            
            return results
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Response text: {response.text[:500] if 'response' in locals() else 'No response'}")
            self.failed_batches.append([s.get('sense_id') for s in batch])
            return []
        except Exception as e:
            print(f"❌ API error: {e}")
            self.failed_batches.append([s.get('sense_id') for s in batch])
            return []
    
    def merge_definitions(self, sense: Dict, regenerated: Dict) -> Dict:
        """Merge regenerated definitions into sense, preserving all other fields."""
        # Update definition fields
        if 'definition_en' in regenerated:
            sense['definition_en'] = regenerated['definition_en']
        if 'definition_zh' in regenerated:
            sense['definition_zh'] = regenerated['definition_zh']
        
        # Update example fields
        if 'example_en' in regenerated:
            sense['example_en'] = regenerated['example_en']
        if 'example_zh_translation' in regenerated:
            sense['example_zh_translation'] = regenerated['example_zh_translation']
        if 'example_zh_explanation' in regenerated:
            sense['example_zh_explanation'] = regenerated['example_zh_explanation']
        
        # Preserve/Add lemma field
        sense_id = regenerated.get('sense_id', sense.get('id', ''))
        if sense_id and 'lemma' not in sense:
            sense['lemma'] = self.extract_lemma(sense_id)
        
        # Ensure word field is set to the lemma (it should already be correct, but double-check)
        if sense_id:
            lemma = self.extract_lemma(sense_id)
            sense['word'] = lemma
        
        # Preserve all other fields (connections, network, etc.)
        return sense
    
    def validate_definition(self, sense_id: str, regenerated: Dict, original_sense: Dict) -> Tuple[bool, List[str]]:
        """Validate regenerated definition."""
        issues = []
        
        definition = regenerated.get('definition_en', '')
        word = regenerated.get('word', '')
        cefr = original_sense.get('cefr', 'B1')
        
        # Check for circular definition
        if word:
            word_lower = word.lower()
            definition_lower = definition.lower()
            # Check if word appears as standalone word (not part of another word)
            if word_lower in definition_lower:
                # Allow if it's part of a phrase or necessary context
                word_with_spaces = f" {word_lower} "
                if word_with_spaces not in f" {definition_lower} ":
                    # Also check if it's at start or end
                    if not (definition_lower.startswith(word_lower + ' ') or 
                           definition_lower.endswith(' ' + word_lower)):
                        issues.append(f"Possible circular definition: uses '{word}'")
        
        # Check example coherence (basic check)
        example = regenerated.get('example_en', '')
        if example:
            sentences = [s.strip() for s in example.split('.') if s.strip()]
            if len(sentences) < 3 or len(sentences) > 6:
                issues.append(f"Example should be 3-6 sentences, got {len(sentences)}")
        
        # Check definition length (informational, not a failure)
        if len(definition) > 200:
            issues.append(f"Definition is very long ({len(definition)} chars) - may be too complex")
        
        return len(issues) == 0, issues
    
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
        
        if not self.dry_run:
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
    
    def create_backup(self):
        """Create backup of vocabulary.json before updating."""
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"vocabulary_backup_{timestamp}.json"
        shutil.copy(VOCABULARY_FILE, backup_path)
        print(f"💾 Backup created: {backup_path}")
        return backup_path
    
    def copy_to_frontend(self):
        """Copy updated vocabulary.json to frontend."""
        if not OUTPUT_FILE.exists():
            print(f"❌ Error: {OUTPUT_FILE} not found")
            return False
        
        print(f"📋 Copying to frontend: {FRONTEND_FILE}")
        FRONTEND_FILE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(OUTPUT_FILE, FRONTEND_FILE)
        print(f"✅ Copied to {FRONTEND_FILE}")
        return True
    
    def run(self):
        """Main regeneration loop."""
        print("\n" + "="*60)
        print("🚀 Starting ESL Definition Regeneration for Fixed Senses")
        print("="*60 + "\n")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified\n")
        
        # Create backup if not dry run
        if not self.dry_run:
            self.create_backup()
        
        # Load input senses
        input_senses = self.load_input_senses()
        
        # Load vocabulary to get current sense data
        vocab_data = self.load_vocabulary()
        
        # Apply limit if specified (for testing)
        if self.limit:
            input_senses = input_senses[:self.limit]
            print(f"📊 Limited to first {self.limit} senses")
        
        # Filter out senses that don't exist in vocabulary.json
        valid_senses = []
        for sense_info in input_senses:
            sense_id = sense_info.get('sense_id')
            if sense_id and sense_id in vocab_data.get('senses', {}):
                valid_senses.append(sense_info)
            else:
                self.stats['skipped_no_sense'] += 1
                print(f"⚠️  Skipping {sense_id}: not found in vocabulary.json")
        
        print(f"📊 Processing {len(valid_senses)} valid senses")
        
        # Check for checkpoint
        start_batch = self.load_checkpoint() if not self.test_mode else 0
        
        # Create batches
        batches = [valid_senses[i:i+BATCH_SIZE] 
                  for i in range(0, len(valid_senses), BATCH_SIZE)]
        total_batches = len(batches)
        
        print(f"📦 Total batches: {total_batches} ({BATCH_SIZE} senses/batch)")
        print(f"🔧 Max workers: {MAX_WORKERS}")
        print(f"💰 Estimated cost: ~${(total_batches * 0.003):.2f}\n")
        
        # Process batches
        start_time = datetime.now()
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            
            # Submit batches
            for i, batch in enumerate(batches[start_batch:], start=start_batch):
                future = executor.submit(self.regenerate_batch, batch)
                futures[future] = (i, batch)
            
            # Process results
            for future in as_completed(futures):
                batch_num, batch = futures[future]
                regenerated_results = future.result()
                
                # Merge results into vocabulary
                for regenerated in regenerated_results:
                    sense_id = regenerated.get('sense_id')
                    if sense_id and sense_id in vocab_data['senses']:
                        original_sense = vocab_data['senses'][sense_id]
                        # Validate
                        is_valid, issues = self.validate_definition(sense_id, regenerated, original_sense)
                        if issues:
                            print(f"⚠️  {sense_id}: {', '.join(issues)}")
                        
                        vocab_data['senses'][sense_id] = self.merge_definitions(
                            original_sense,
                            regenerated
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
        
        # Update exportedAt timestamp
        if not self.dry_run:
            vocab_data['exportedAt'] = datetime.now().isoformat()
        
        # Final save
        self.save_checkpoint(vocab_data, total_batches)
        
        # Copy to frontend
        if not self.dry_run:
            self.copy_to_frontend()
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*60)
        print("✅ Definition Regeneration Complete!")
        print("="*60)
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"📊 Processed: {self.stats['processed']}/{len(valid_senses)}")
        print(f"⏭️  Skipped (not in vocab): {self.stats['skipped_no_sense']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"🌐 API calls: {self.stats['api_calls']}")
        print(f"📝 Tokens: ~{self.stats['tokens_used']:,}")
        print(f"💰 Cost: ~${(self.stats['tokens_used'] / 1_000_000 * 0.375):.2f}")
        
        if not self.dry_run:
            print(f"\n📁 Output: {OUTPUT_FILE}")
            print(f"📁 Frontend: {FRONTEND_FILE}")
        else:
            print(f"\n🔍 DRY RUN - No files modified")
        
        if self.failed_batches:
            print(f"\n⚠️  {len(self.failed_batches)} batches failed. "
                  f"Check {CHECKPOINT_FILE} for details.")


def run_daemon(test_mode: bool = False, limit: Optional[int] = None, dry_run: bool = False):
    """
    Run the regeneration in daemon mode with auto-restart.
    
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
            regenerator = DefinitionRegenerator(
                test_mode=test_mode,
                limit=limit,
                dry_run=dry_run
            )
            
            regenerator.run()
            
            print("\n✅ Regeneration completed successfully!")
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached, giving up.")
                return False
    
    print("❌ Regeneration failed after max retries")
    return False


def main():
    parser = argparse.ArgumentParser(description='ESL Definition Regeneration Script for Fixed Senses')
    parser.add_argument('--test', action='store_true', 
                       help='Test mode (process first 20-40 senses)')
    parser.add_argument('--limit', type=int, 
                       help='Process only first N senses (for incremental testing)')
    parser.add_argument('--resume', action='store_true', 
                       help='Resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Validate without updating vocabulary.json')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run in daemon mode with auto-restart')
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(test_mode=args.test, limit=args.limit, dry_run=args.dry_run)
    else:
        regenerator = DefinitionRegenerator(
            test_mode=args.test,
            limit=args.limit,
            dry_run=args.dry_run
        )
        regenerator.run()


if __name__ == "__main__":
    main()

