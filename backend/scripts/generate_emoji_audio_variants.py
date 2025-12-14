"""
Generate Audio Variants for Emoji Vocabulary Pack

Generates 11 audio variants for each word in the emoji pack using OpenAI TTS HD.
Each word gets one variant per voice (all saying the word once for consistent comparison).

After generation, select 5 voices per word and update the pack JSON with audio_variants.

Usage:
    python3 scripts/generate_emoji_audio_variants.py
    python3 scripts/generate_emoji_audio_variants.py --limit 10  # Test with 10 words
    python3 scripts/generate_emoji_audio_variants.py --resume    # Resume from checkpoint
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
# Try backend directory first (where .env is typically located)
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
# Try backend/.env first, then root/.env
env_paths = [backend_dir / '.env', root_dir / '.env']
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# All available OpenAI TTS voices (9 valid voices as of Dec 2024)
ALL_VOICES = [
    'alloy',    # Neutral and balanced
    'ash',      # Warm and conversational
    'coral',    # Friendly and approachable
    'echo',     # Clear and articulate
    'fable',    # Expressive and dynamic
    'nova',     # Friendly and warm
    'onyx',     # Deep and authoritative
    'sage',     # Calm and measured
    'shimmer',  # Bright and optimistic
]

# Paths
PACK_FILE = Path(__file__).parent.parent.parent / "landing-page" / "data" / "packs" / "emoji-core.json"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "landing-page" / "public" / "audio" / "emoji"
CHECKPOINT_FILE = Path(__file__).parent.parent / "emoji_audio_generation_checkpoint.json"


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


def normalize_word(word: str) -> str:
    """Normalize word for filename (lowercase, replace spaces with underscores)."""
    return word.lower().replace(' ', '_')


def generate_single_audio(word: str, voice: str, client: OpenAI) -> tuple[str, bool, Optional[str]]:
    """Generate a single audio file for a word and voice. Returns (filename, success, error)."""
    normalized_word = normalize_word(word)
    filename = f"{normalized_word}_{voice}.mp3"
    filepath = OUTPUT_DIR / filename
    
    # Skip if already exists
    if filepath.exists():
        return (filename, True, None)
    
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=word,
            speed=1.0
        )
        response.stream_to_file(str(filepath))
        return (filename, True, None)
    except Exception as e:
        error_msg = str(e)
        return (filename, False, error_msg)


def generate_variants(word: str, client: OpenAI, max_workers: int = 5) -> List[str]:
    """Generate all variants for a word in parallel."""
    variants = []
    normalized_word = normalize_word(word)
    
    # Generate all voices in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_single_audio, word, voice, client): voice
            for voice in ALL_VOICES
        }
        
        for future in as_completed(futures):
            voice = futures[future]
            try:
                filename, success, error = future.result()
                if success:
                    variants.append(filename)
                    print(f"  ✅ Generated: {filename}")
                else:
                    print(f"  ❌ Failed {word} ({voice}): {error}")
            except Exception as e:
                print(f"  ❌ Error generating {word} ({voice}): {e}")
    
    return variants


def main():
    parser = argparse.ArgumentParser(description='Generate audio variants for emoji vocabulary')
    parser.add_argument('--limit', type=int, help='Limit number of words to process (for testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--skip-existing', action='store_true', help='Skip words that already have all variants')
    parser.add_argument('--parallel-words', type=int, default=3, help='Number of words to process in parallel (default: 3)')
    parser.add_argument('--parallel-voices', type=int, default=5, help='Number of voices to generate in parallel per word (default: 5)')
    
    args = parser.parse_args()
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Load pack file
    if not PACK_FILE.exists():
        print(f"❌ Pack file not found: {PACK_FILE}")
        return
    
    with open(PACK_FILE, 'r', encoding='utf-8') as f:
        pack_data = json.load(f)
    
    vocabulary = pack_data.get('vocabulary', [])
    total_words = len(vocabulary)
    
    print("=" * 80)
    print("EMOJI AUDIO VARIANT GENERATION")
    print("=" * 80)
    print(f"Pack: {pack_data['pack']['name']}")
    print(f"Total words: {total_words}")
    print(f"Voices: {len(ALL_VOICES)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Expected files: {total_words * len(ALL_VOICES)} ({total_words} words × {len(ALL_VOICES)} voices)")
    print("=" * 80)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint
    checkpoint = load_checkpoint() if args.resume else {}
    processed_words = set(checkpoint.get('processed_words', checkpoint.get('completed', [])))
    
    # Filter words to process
    words_to_process = []
    for item in vocabulary:
        word = item['word']
        if args.resume and word in processed_words:
            continue
        
        # Check if all variants already exist
        normalized_word = normalize_word(word)
        all_exist = all(
            (OUTPUT_DIR / f"{normalized_word}_{voice}.mp3").exists()
            for voice in ALL_VOICES
        )
        if all_exist:
            if args.skip_existing or args.resume:
                print(f"⏭️  Skipping {word} (all variants exist)")
                processed_words.add(word)
                continue
        
        words_to_process.append(item)
    
    if args.limit:
        words_to_process = words_to_process[:args.limit]
        print(f"\n⚠️  Limited to {args.limit} words for testing")
    
    print(f"\n📝 Processing {len(words_to_process)} words...")
    print(f"⚡ Parallel: {args.parallel_words} words, {args.parallel_voices} voices per word")
    print()
    
    # Statistics
    stats = {
        'total': len(words_to_process),
        'processed': 0,
        'failed': 0,
        'started_at': datetime.now().isoformat(),
    }
    
    # Process words in parallel batches
    def process_word(item, idx, total):
        word = item['word']
        print(f"[{idx}/{total}] Processing: {word}")
        
        try:
            variants = generate_variants(word, client, max_workers=args.parallel_voices)
            
            if len(variants) == len(ALL_VOICES):
                print(f"  ✅ Success: Generated {len(variants)} variants for {word}")
                return (word, True, len(variants))
            else:
                print(f"  ⚠️  Partial: Only {len(variants)}/{len(ALL_VOICES)} variants generated")
                return (word, False, len(variants))
            
        except Exception as e:
            print(f"  ❌ Error processing {word}: {e}")
            return (word, False, 0)
    
    # Process in parallel batches
    results = []
    with ThreadPoolExecutor(max_workers=args.parallel_words) as executor:
        futures = {
            executor.submit(process_word, item, idx, len(words_to_process)): idx
            for idx, item in enumerate(words_to_process, 1)
        }
        
        completed_count = 0
        for future in as_completed(futures):
            completed_count += 1
            try:
                result = future.result()
                results.append(result)
                word, success, count = result
                
                # Update stats (thread-safe - we're collecting results)
                if success and count == len(ALL_VOICES):
                    processed_words.add(word)
                    stats['processed'] += 1
                else:
                    stats['failed'] += 1
                
                # Save checkpoint every 5 words
                if completed_count % 5 == 0:
                    checkpoint = {
                        'processed_words': list(processed_words),
                        'completed': list(processed_words),  # Alias for compatibility
                        'stats': stats,
                        'last_updated': datetime.now().isoformat()
                    }
                    save_checkpoint(checkpoint)
                    print(f"  💾 Checkpoint saved ({stats['processed']} words completed)")
                    print()
            except Exception as e:
                print(f"  ❌ Future error: {e}")
                print()
                stats['failed'] += 1
    
    # Final checkpoint
    stats['completed_at'] = datetime.now().isoformat()
    checkpoint = {
        'processed_words': list(processed_words),
        'stats': stats,
        'last_updated': datetime.now().isoformat()
    }
    save_checkpoint(checkpoint)
    
    # Summary
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total words processed: {stats['processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total files generated: {stats['processed'] * len(ALL_VOICES)}")
    print()
    print("📋 Next Steps:")
    print("1. Review generated audio files")
    print("2. Select 5 voices per word (different selection for each word)")
    print("3. Update emoji-core.json with audio_variants field")
    print("4. Test audio playback in the app")
    print("=" * 80)


if __name__ == "__main__":
    main()

