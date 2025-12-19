"""
Generate Audio for MCQ Prompts and Feedback Messages

Generates audio files for question prompts and feedback messages using OpenAI TTS HD.
Each prompt/feedback gets one audio file with its specified voice.

Usage:
    python3 scripts/generate_prompt_audio.py
    python3 scripts/generate_prompt_audio.py --limit 5  # Test with 5 items
    python3 scripts/generate_prompt_audio.py --resume    # Resume from checkpoint
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
env_paths = [backend_dir / '.env', root_dir / '.env']
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Valid OpenAI TTS voices
VALID_VOICES = [
    'alloy', 'ash', 'coral', 'echo', 'fable', 'nova', 'onyx', 'sage', 'shimmer'
]

# Paths
PROMPTS_FILE = Path(__file__).parent.parent.parent / "landing-page" / "data" / "audio-prompts.json"
FEEDBACK_FILE = Path(__file__).parent.parent.parent / "landing-page" / "data" / "audio-feedback.json"
PROMPTS_OUTPUT_DIR = Path(__file__).parent.parent.parent / "landing-page" / "public" / "audio" / "prompts"
FEEDBACK_OUTPUT_DIR = Path(__file__).parent.parent.parent / "landing-page" / "public" / "audio" / "feedback"
CHECKPOINT_FILE = Path(__file__).parent.parent / "prompt_audio_generation_checkpoint.json"


def load_checkpoint() -> Dict:
    """Load checkpoint data if exists."""
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load checkpoint: {e}")
            return {}
    return {}


def save_checkpoint(data: Dict):
    """Save checkpoint data."""
    try:
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to save checkpoint: {e}")


def normalize_id(item_id: str) -> str:
    """Normalize ID for filename (lowercase, replace spaces/special chars with underscores)."""
    return item_id.lower().replace(' ', '_').replace('?', '').replace('!', '').replace(',', '').replace("'", "")


def generate_single_audio(
    text: str, 
    item_id: str, 
    voice: str, 
    output_dir: Path,
    category: str,
    client: OpenAI
) -> Tuple[str, bool, Optional[str]]:
    """Generate a single audio file. Returns (filename, success, error)."""
    normalized_id = normalize_id(item_id)
    filename = f"{normalized_id}_{voice}.mp3"
    
    # Create category subdirectory
    category_dir = output_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = category_dir / filename
    
    # Skip if already exists
    if filepath.exists():
        return (filename, True, None)
    
    # Validate voice
    if voice not in VALID_VOICES:
        return (filename, False, f"Invalid voice: {voice}")
    
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=text,
            speed=1.0
        )
        response.stream_to_file(str(filepath))
        return (filename, True, None)
    except Exception as e:
        error_msg = str(e)
        return (filename, False, error_msg)


def load_prompts() -> List[Dict]:
    """Load all prompts from JSON file."""
    if not PROMPTS_FILE.exists():
        print(f"❌ Prompts file not found: {PROMPTS_FILE}")
        return []
    
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts = []
    for category, items in data.get('prompts', {}).items():
        for item in items:
            prompts.append({
                'id': item['id'],
                'text': item['text'],
                'voice': item['voice'],
                'category': item['category'],
                'type': category,  # word_to_emoji, emoji_to_word, general
                'output_dir': PROMPTS_OUTPUT_DIR
            })
    
    return prompts


def load_feedback() -> List[Dict]:
    """Load all feedback messages from JSON file."""
    if not FEEDBACK_FILE.exists():
        print(f"❌ Feedback file not found: {FEEDBACK_FILE}")
        return []
    
    with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    feedback = []
    for category, items in data.get('feedback', {}).items():
        for item in items:
            feedback.append({
                'id': item['id'],
                'text': item['text'],
                'voice': item['voice'],
                'category': item['category'],  # correct or incorrect
                'type': category,  # correct or incorrect
                'output_dir': FEEDBACK_OUTPUT_DIR
            })
    
    return feedback


def process_item(item: Dict, client: OpenAI) -> Tuple[str, bool, Optional[str]]:
    """Process a single prompt or feedback item."""
    item_id = item['id']
    text = item['text']
    voice = item['voice']
    category = item['category']
    output_dir = item['output_dir']
    
    filename, success, error = generate_single_audio(
        text, item_id, voice, output_dir, category, client
    )
    
    if success:
        return (item_id, True, None)
    else:
        return (item_id, False, error)


def main():
    parser = argparse.ArgumentParser(description='Generate audio for prompts and feedback')
    parser.add_argument('--limit', type=int, help='Limit number of items to process (for testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--skip-existing', action='store_true', help='Skip items that already have audio')
    parser.add_argument('--parallel', type=int, default=10, help='Number of items to process in parallel (default: 10)')
    parser.add_argument('--prompts-only', action='store_true', help='Only generate prompts')
    parser.add_argument('--feedback-only', action='store_true', help='Only generate feedback')
    
    args = parser.parse_args()
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Load items
    all_items = []
    
    if not args.feedback_only:
        prompts = load_prompts()
        all_items.extend(prompts)
        print(f"📝 Loaded {len(prompts)} prompts")
    
    if not args.prompts_only:
        feedback = load_feedback()
        all_items.extend(feedback)
        print(f"💬 Loaded {len(feedback)} feedback messages")
    
    total_items = len(all_items)
    
    if total_items == 0:
        print("❌ No items to process")
        return
    
    print("=" * 80)
    print("PROMPT & FEEDBACK AUDIO GENERATION")
    print("=" * 80)
    print(f"Total items: {total_items}")
    print(f"Output directories:")
    print(f"  Prompts: {PROMPTS_OUTPUT_DIR}")
    print(f"  Feedback: {FEEDBACK_OUTPUT_DIR}")
    print(f"Parallel workers: {args.parallel}")
    print("=" * 80)
    
    # Ensure output directories exist
    PROMPTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint
    checkpoint = load_checkpoint() if args.resume else {}
    processed_items = set(checkpoint.get('processed_items', []))
    
    # Filter items to process
    items_to_process = []
    for item in all_items:
        item_id = item['id']
        if args.resume and item_id in processed_items:
            continue
        
        # Check if audio already exists
        normalized_id = normalize_id(item_id)
        category = item['category']
        output_dir = item['output_dir']
        voice = item['voice']
        filename = f"{normalized_id}_{voice}.mp3"
        filepath = output_dir / category / filename
        
        if filepath.exists():
            if args.skip_existing or args.resume:
                print(f"⏭️  Skipping {item_id} (audio exists)")
                processed_items.add(item_id)
                continue
        
        items_to_process.append(item)
    
    if args.limit:
        items_to_process = items_to_process[:args.limit]
        print(f"\n⚠️  Limited to {args.limit} items for testing")
    
    print(f"\n📝 Processing {len(items_to_process)} items...")
    print(f"⚡ Parallel: {args.parallel} items")
    print()
    
    # Statistics
    stats = {
        'total': len(items_to_process),
        'processed': 0,
        'failed': 0,
        'started_at': datetime.now().isoformat(),
    }
    
    # Process items in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(process_item, item, client): item['id']
            for item in items_to_process
        }
        
        completed_count = 0
        for future in as_completed(futures):
            completed_count += 1
            item_id = futures[future]
            try:
                result = future.result()
                results.append(result)
                processed_id, success, error = result
                
                if success:
                    processed_items.add(processed_id)
                    stats['processed'] += 1
                    print(f"  ✅ [{completed_count}/{len(items_to_process)}] {processed_id}")
                else:
                    stats['failed'] += 1
                    print(f"  ❌ [{completed_count}/{len(items_to_process)}] {processed_id}: {error}")
                
                # Save checkpoint every 10 items
                if completed_count % 10 == 0:
                    checkpoint = {
                        'processed_items': list(processed_items),
                        'stats': stats,
                        'last_updated': datetime.now().isoformat()
                    }
                    save_checkpoint(checkpoint)
                    print(f"  💾 Checkpoint saved ({stats['processed']} items completed)")
                    print()
            except Exception as e:
                print(f"  ❌ Future error for {item_id}: {e}")
                stats['failed'] += 1
    
    # Final checkpoint
    stats['completed_at'] = datetime.now().isoformat()
    checkpoint = {
        'processed_items': list(processed_items),
        'stats': stats,
        'last_updated': datetime.now().isoformat()
    }
    save_checkpoint(checkpoint)
    
    # Summary
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total items processed: {stats['processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total files generated: {stats['processed']}")
    print()
    print("📋 Next Steps:")
    print("1. Review generated audio files")
    print("2. Update audio-service.ts with playPrompt() and playFeedback() methods")
    print("3. Integrate audio playback in MCQ components")
    print("4. Test audio playback and timing")
    print("=" * 80)


if __name__ == "__main__":
    main()




