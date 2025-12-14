"""
Enrich senses directly from vocabulary.json (bypassing Neo4j)

This script generates multi-layer examples for senses that exist in vocabulary.json
but not in Neo4j. It uses the `connections` field in vocabulary.json for
relationship data.

Usage:
    python scripts/enrich_from_vocabulary.py --limit 10         # Enrich 10 senses
    python scripts/enrich_from_vocabulary.py --workers 10       # Use 10 parallel workers
    python scripts/enrich_from_vocabulary.py --mock             # Use mock data
    python scripts/enrich_from_vocabulary.py --resume           # Resume from checkpoint
"""

import os
import sys
import json
import argparse
import time
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Rate limiting - 10 requests/minute limit still applies
# Shared across all workers to prevent exceeding the limit
RATE_LIMIT_LOCK = threading.Lock()
LAST_API_CALL = 0
MIN_DELAY_SECONDS = 6.1  # 10 RPM = 6 seconds per call, small buffer for safety

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai
from dotenv import load_dotenv
from src.pipeline.status import get_status_manager, PipelineState

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Checkpoint file
CHECKPOINT_FILE = Path(__file__).parent.parent / "vocab_enrichment_checkpoint.json"

# Tiered example counts based on usage
TIER_CONFIG = {
    "primary": {"min": 15, "max": 20, "description": "Primary senses (most used)"},
    "common": {"min": 8, "max": 12, "description": "Common senses"},
    "rare": {"min": 5, "max": 8, "description": "Rare senses"}
}


def get_tier(sense: Dict) -> str:
    """Determine the tier for a sense based on usage patterns."""
    usage_ratio = sense.get("usage_ratio") or 0.0
    frequency_rank = sense.get("frequency_rank") or 999
    
    # Extract sense number from sense_id (e.g., "word.n.01" -> 1)
    sense_id = sense.get("id", "")
    try:
        sense_num = int(sense_id.split(".")[-1]) if sense_id else 1
    except ValueError:
        sense_num = 1
    
    # Check if this is the only sense for a word
    is_only_sense = sense.get("is_only_sense", False)
    
    # Determine tier
    if is_only_sense or sense_num == 1:
        # First sense or only sense = primary
        return "primary"
    elif usage_ratio >= 0.3 or frequency_rank <= 5:
        # High usage ratio or very common word
        return "common"
    else:
        return "rare"


def get_tiered_example_count(sense: Dict) -> Tuple[int, int, str]:
    """Get min/max example counts based on sense tier."""
    tier = get_tier(sense)
    config = TIER_CONFIG[tier]
    return config["min"], config["max"], tier


def load_vocabulary() -> Dict[str, Dict]:
    """Load vocabulary.json and return senses dict."""
    vocab_path = Path(__file__).parent.parent / "data" / "vocabulary.json"
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab = json.load(f)
    return vocab.get("senses", {})


def save_vocabulary(senses: Dict[str, Dict]) -> None:
    """Save updated senses back to vocabulary.json."""
    vocab_path = Path(__file__).parent.parent / "data" / "vocabulary.json"
    
    # Load full vocabulary to preserve other fields
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab = json.load(f)
    
    vocab["senses"] = senses
    
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)


def load_checkpoint() -> Dict:
    """Load checkpoint file if exists."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"processed": [], "failed": []}


def save_checkpoint(checkpoint: Dict) -> None:
    """Save checkpoint to file."""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def get_senses_to_enrich(senses: Dict[str, Dict], checkpoint: Dict, limit: Optional[int] = None, retry_list: Optional[List[str]] = None) -> List[str]:
    """Get list of sense IDs that need enrichment.
    
    Args:
        senses: All senses from vocabulary.json
        checkpoint: Checkpoint data with processed/failed lists
        limit: Optional limit on number of senses to process
        retry_list: Optional list of specific sense IDs to retry (overrides normal filtering)
    """
    # If retry list provided, use only those senses
    if retry_list:
        to_enrich = []
        for sense_id in retry_list:
            if sense_id in senses:
                sense = senses[sense_id]
                # Skip if already has V3 enrichment (might have been enriched since failure)
                if sense.get("stage2_version") == 3:
                    continue
                to_enrich.append(sense_id)
        return to_enrich
    
    # Normal processing: find all senses that need enrichment
    processed = set(checkpoint.get("processed", []))
    
    to_enrich = []
    for sense_id, sense in senses.items():
        # Skip if already has V3 enrichment
        if sense.get("stage2_version") == 3:
            continue
        # Skip if already processed in this run
        if sense_id in processed:
            continue
        to_enrich.append(sense_id)
    
    if limit:
        to_enrich = to_enrich[:limit]
    
    return to_enrich


def get_mock_examples(sense: Dict) -> Dict:
    """Generate mock examples for testing."""
    min_ex, max_ex, tier = get_tiered_example_count(sense)
    num_examples = (min_ex + max_ex) // 2
    word = sense.get("word", sense.get("lemma", "word"))
    
    return {
        "examples_contextual": [
            {
                "example_en": f"Mock contextual example {i} for {word}.",
                "example_zh_translation": f"{word} 的模擬上下文例句 {i}。",
                "example_zh_explanation": f"說明：這是 {word} 的第 {i} 個例句。"
            }
            for i in range(1, num_examples + 1)
        ],
        "examples_opposite": [
            {
                "example_en": f"Mock opposite example for {word}.",
                "example_zh_translation": f"{word} 的反義例句。",
                "example_zh_explanation": f"說明：這展示了 {word} 的反義。",
                "relationship_word": "opposite_word",
                "relationship_type": "opposite"
            }
        ] if sense.get("connections", {}).get("opposite") else [],
        "examples_similar": [
            {
                "example_en": f"Mock similar example for {word}.",
                "example_zh_translation": f"{word} 的近義例句。",
                "example_zh_explanation": f"說明：這展示了與 {word} 相似的用法。",
                "relationship_word": "similar_word",
                "relationship_type": "similar"
            }
        ] if sense.get("connections", {}).get("related") else [],
        "examples_confused": [
            {
                "example_en": f"Mock confusion-clarifying example for {word}.",
                "example_zh_translation": f"澄清 {word} 混淆的例句。",
                "example_zh_explanation": f"說明：這澄清了與 {word} 常見的混淆。",
                "relationship_word": "confused_word",
                "relationship_type": "confused"
            }
        ] if sense.get("connections", {}).get("confused") else []
    }


def rate_limit():
    """Enforce rate limiting for API calls across all workers."""
    global LAST_API_CALL
    with RATE_LIMIT_LOCK:
        now = time.time()
        elapsed = now - LAST_API_CALL
        if elapsed < MIN_DELAY_SECONDS:
            sleep_time = MIN_DELAY_SECONDS - elapsed
            time.sleep(sleep_time)
        LAST_API_CALL = time.time()


def call_gemini_api(sense: Dict, max_retries: int = 3) -> Optional[Dict]:
    """Call Gemini API to generate examples for a sense with rate limiting and retries."""
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not configured")
    
    word = sense.get("word", sense.get("lemma", "unknown"))
    definition_en = sense.get("definition_en", sense.get("definition", ""))
    definition_zh = sense.get("definition_zh", "")
    example_en = sense.get("example_en", "")
    
    # Get relationship data from connections
    connections = sense.get("connections", {})
    
    def extract_word(item):
        """Extract word from connection item (handles both string and dict formats)."""
        if isinstance(item, str):
            return item.split(".")[0]
        elif isinstance(item, dict):
            return item.get("sense_id", "").split(".")[0]
        return ""
    
    opposites = [extract_word(c) for c in connections.get("opposite", []) if extract_word(c)][:3]
    similar = [extract_word(c) for c in connections.get("related", []) if extract_word(c)][:3]
    confused = [extract_word(c) for c in connections.get("confused", []) if extract_word(c)][:3]
    
    # Get tiered example count
    min_ex, max_ex, tier = get_tiered_example_count(sense)
    
    # Build prompt
    prompt = f"""Generate multi-layer example sentences for vocabulary learning.

**Word:** {word}
**Definition (English):** {definition_en}
**Definition (Chinese):** {definition_zh}
**Existing Example:** {example_en}
**Tier:** {tier} (generate {min_ex}-{max_ex} contextual examples)

**Relationships:**
- Opposite words: {', '.join(opposites) if opposites else 'None'}
- Similar words: {', '.join(similar) if similar else 'None'}
- Commonly confused with: {', '.join(confused) if confused else 'None'}

Generate examples in this JSON format:
{{
  "examples_contextual": [
    {{
      "example_en": "English sentence using the word naturally",
      "example_zh_translation": "直譯：中文翻譯",
      "example_zh_explanation": "說明：為什麼在這個例句中使用這個詞"
    }}
    // Generate {min_ex}-{max_ex} contextual examples showing different usage patterns
  ],
  "examples_opposite": [
    {{
      "example_en": "Sentence showing contrast with opposite word",
      "example_zh_translation": "直譯：中文翻譯",
      "example_zh_explanation": "說明：解釋反義關係",
      "relationship_word": "opposite_word",
      "relationship_type": "opposite"
    }}
    // Generate 2-3 examples if opposite words exist, otherwise empty array
  ],
  "examples_similar": [
    {{
      "example_en": "Sentence showing similarity with related word",
      "example_zh_translation": "直譯：中文翻譯",
      "example_zh_explanation": "說明：解釋相似關係",
      "relationship_word": "similar_word",
      "relationship_type": "similar"
    }}
    // Generate 2-3 examples if similar words exist, otherwise empty array
  ],
  "examples_confused": [
    {{
      "example_en": "Sentence clarifying confusion with commonly confused word",
      "example_zh_translation": "直譯：中文翻譯",
      "example_zh_explanation": "說明：解釋為什麼容易混淆以及如何區分",
      "relationship_word": "confused_word",
      "relationship_type": "confused"
    }}
    // Generate 2-3 examples if confused words exist, otherwise empty array
  ]
}}

Requirements:
1. Contextual examples should be diverse, showing different contexts and grammatical patterns
2. All examples should be natural and commonly used
3. Chinese translations should be accurate and helpful for Chinese learners
4. Explanations should clarify WHY this word is used in each context
5. Return ONLY valid JSON, no markdown or extra text
"""
    
    for attempt in range(max_retries):
        try:
            # Apply rate limiting (shared across all workers)
            rate_limit()
            
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            text = response.text.strip()
            
            # Try to extract JSON from markdown code block if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
            if json_match:
                text = json_match.group(1).strip()
            
            # Parse JSON
            result = json.loads(text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"    JSON parse error: {e}")
            return None
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < max_retries - 1:
                # Rate limit error - wait and retry
                wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                print(f"    Rate limit hit, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            print(f"    API error: {e}")
            return None
    
    return None


def enrich_sense(sense_id: str, sense: Dict, use_mock: bool = False) -> Optional[Dict]:
    """Enrich a single sense with examples."""
    if use_mock:
        return get_mock_examples(sense)
    else:
        return call_gemini_api(sense)


def main():
    parser = argparse.ArgumentParser(
        description="Enrich senses directly from vocabulary.json"
    )
    parser.add_argument("--limit", type=int, help="Limit number of senses to process")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of API")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--save-interval", type=int, default=50, help="Save progress every N senses")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--stop", action="store_true", help="Request enrichment to stop")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode with auto-restart")
    parser.add_argument("--retry-list", type=str, help="JSON file containing list of sense IDs to retry")
    args = parser.parse_args()
    
    status_manager = get_status_manager()
    
    # Handle status command
    if args.status:
        status = status_manager.get_status()
        print(json.dumps(status.to_dict(), indent=2))
        return 0
    
    # Handle stop command
    if args.stop:
        status_manager.request_stop()
        print("⏹️ Stop requested. Enrichment will stop after current sense.")
        return 0
    
    # Check if already running
    if status_manager.is_running():
        print("⚠️ Enrichment is already running!")
        print("Use --status to check progress or --stop to request stop")
        return 1
    
    print("=" * 60)
    print("Vocabulary-based Enrichment Script")
    print("=" * 60)
    
    # Mark as running
    status_manager.start_run(total_words=0, run_id=f"vocab_enrich_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Load vocabulary
    print("\n📥 Loading vocabulary.json...")
    senses = load_vocabulary()
    print(f"   Loaded {len(senses):,} senses")
    
    # Load retry list if provided
    retry_list = None
    if args.retry_list:
        retry_file = Path(args.retry_list)
        if not retry_file.exists():
            print(f"❌ Retry list file not found: {retry_file}")
            return 1
        with open(retry_file, 'r') as f:
            retry_list = json.load(f)
        print(f"   Loaded retry list: {len(retry_list):,} senses to retry")
    
    # Load checkpoint if resuming (but skip if using retry list)
    checkpoint = load_checkpoint() if args.resume and not args.retry_list else {"processed": [], "failed": []}
    if args.resume and not args.retry_list:
        print(f"   Resuming from checkpoint: {len(checkpoint['processed']):,} already processed")
    
    # Get senses to enrich
    to_enrich = get_senses_to_enrich(senses, checkpoint, args.limit, retry_list)
    print(f"\n📋 Senses to enrich: {len(to_enrich):,}")
    
    if not to_enrich:
        print("✅ All senses already enriched!")
        status_manager.mark_completed()
        return 0
    
    # Update status with total
    status_manager.update_progress(
        processed_words=len(checkpoint['processed']),
        current_word=None,
        total_senses=len(to_enrich),
        validated_senses=0,
        failed_senses=len(checkpoint['failed']),
        ai_calls=0,
        estimated_cost_usd=0.0
    )
    
    # Show tier distribution
    tier_counts = {"primary": 0, "common": 0, "rare": 0}
    for sid in to_enrich:
        tier = get_tier(senses[sid])
        tier_counts[tier] += 1
    print(f"   Tier distribution: Primary={tier_counts['primary']:,}, Common={tier_counts['common']:,}, Rare={tier_counts['rare']:,}")
    
    # Process senses
    print(f"\n🚀 Starting enrichment with {args.workers} workers...")
    print(f"   Mode: {'MOCK' if args.mock else 'GEMINI API'}")
    
    start_time = time.time()
    processed_count = 0
    failed_count = 0
    
    def process_sense(sense_id: str) -> Tuple[str, bool, Optional[Dict]]:
        """Process a single sense and return results."""
        sense = senses[sense_id]
        result = enrich_sense(sense_id, sense, use_mock=args.mock)
        return sense_id, result is not None, result
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_sense, sid): sid for sid in to_enrich}
        
        for future in as_completed(futures):
            sense_id = futures[future]
            try:
                # Check if stop requested
                if status_manager.should_stop():
                    print("\n⏹️ Stop requested, finishing current batch...")
                    break
                
                sid, success, result = future.result()
                
                if success and result:
                    # Update sense with enrichment data
                    senses[sid]["examples_contextual"] = result.get("examples_contextual", [])
                    senses[sid]["examples_opposite"] = result.get("examples_opposite", [])
                    senses[sid]["examples_similar"] = result.get("examples_similar", [])
                    senses[sid]["examples_confused"] = result.get("examples_confused", [])
                    senses[sid]["stage2_version"] = 3
                    senses[sid]["stage2_enriched_at"] = datetime.now(timezone.utc).isoformat()
                    
                    checkpoint["processed"].append(sid)
                    processed_count += 1
                    
                    tier = get_tier(senses[sid])
                    ctx_count = len(result.get("examples_contextual", []))
                    print(f"  ✅ {sid} [{tier}]: {ctx_count} contextual examples")
                    
                    # Update status
                    status_manager.update_progress(
                        processed_words=processed_count,
                        current_word=sid,
                        total_senses=len(to_enrich),
                        validated_senses=processed_count,
                        failed_senses=failed_count,
                        ai_calls=processed_count + failed_count,
                        estimated_cost_usd=(processed_count + failed_count) * 0.0001
                    )
                else:
                    checkpoint["failed"].append(sid)
                    failed_count += 1
                    print(f"  ❌ {sid}: Failed to enrich")
                
                # Save progress periodically
                total_processed = processed_count + failed_count
                if total_processed % args.save_interval == 0:
                    print(f"\n💾 Saving progress ({total_processed:,}/{len(to_enrich):,})...")
                    save_vocabulary(senses)
                    save_checkpoint(checkpoint)
                    
                    elapsed = time.time() - start_time
                    rate = total_processed / elapsed if elapsed > 0 else 0
                    remaining = len(to_enrich) - total_processed
                    eta = remaining / rate if rate > 0 else 0
                    print(f"   Rate: {rate:.1f} senses/sec, ETA: {eta/60:.1f} min\n")
                    
            except Exception as e:
                print(f"  ❌ {sense_id}: Error - {e}")
                checkpoint["failed"].append(sense_id)
                failed_count += 1
    
    # Final save
    print("\n💾 Saving final results...")
    save_vocabulary(senses)
    save_checkpoint(checkpoint)
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print("📊 Summary")
    print(f"{'=' * 60}")
    print(f"   Processed: {processed_count:,}")
    print(f"   Failed: {failed_count:,}")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"   Rate: {processed_count/elapsed:.1f} senses/sec")
    
    # Count V3 senses
    v3_count = sum(1 for s in senses.values() if s.get("stage2_version") == 3)
    print(f"\n   Total V3 senses in vocabulary.json: {v3_count:,} / {len(senses):,}")
    
    # Update status
    if status_manager.should_stop():
        status_manager.mark_stopped()
        print("\n⏹️ Enrichment stopped by user request")
    else:
        status_manager.mark_completed()
        print("\n✅ Enrichment complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

