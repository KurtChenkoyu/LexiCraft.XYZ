#!/usr/bin/env python3
"""
Check status of emoji audio generation.

Usage:
    python3 scripts/check_audio_status.py
"""

import json
from pathlib import Path

# Paths
CHECKPOINT_FILE = Path(__file__).parent.parent / "emoji_audio_generation_checkpoint.json"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "landing-page" / "public" / "audio" / "emoji"
PACK_FILE = Path(__file__).parent.parent.parent / "landing-page" / "data" / "packs" / "emoji-core.json"

ALL_VOICES = [
    'alloy', 'ash', 'coral', 'echo', 'fable', 'nova', 'onyx', 'sage', 'shimmer'
]

def normalize_word(word: str) -> str:
    return word.lower().replace(' ', '_')

def main():
    # Load pack
    if not PACK_FILE.exists():
        print(f"❌ Pack file not found: {PACK_FILE}")
        return
    
    with open(PACK_FILE, 'r', encoding='utf-8') as f:
        pack_data = json.load(f)
    
    vocabulary = pack_data.get('vocabulary', [])
    total_words = len(vocabulary)
    
    # Load checkpoint
    checkpoint = {}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
        except:
            pass
    
    processed_words = set(checkpoint.get('processed_words', checkpoint.get('completed', [])))
    
    # Count files
    if not OUTPUT_DIR.exists():
        print("❌ Output directory doesn't exist")
        return
    
    files = list(OUTPUT_DIR.glob("*.mp3"))
    total_files = len(files)
    
    # Count complete words
    complete_words = []
    partial_words = []
    
    for item in vocabulary:
        word = item['word']
        normalized = normalize_word(word)
        existing = sum(
            1 for voice in ALL_VOICES
            if (OUTPUT_DIR / f"{normalized}_{voice}.mp3").exists()
        )
        
        if existing == len(ALL_VOICES):
            complete_words.append(word)
        elif existing > 0:
            partial_words.append((word, existing, len(ALL_VOICES)))
    
    # Stats
    complete_count = len(complete_words)
    partial_count = len(partial_words)
    remaining = total_words - complete_count - partial_count
    
    # Print status
    print("=" * 80)
    print("EMOJI AUDIO GENERATION STATUS")
    print("=" * 80)
    print(f"Total words in pack: {total_words}")
    print(f"Expected files: {total_words * len(ALL_VOICES)} ({total_words} words × {len(ALL_VOICES)} voices)")
    print()
    print(f"✅ Complete: {complete_count} words ({complete_count * 100 // total_words}%)")
    print(f"⚠️  Partial: {partial_count} words")
    print(f"⏳ Remaining: {remaining} words")
    print(f"📁 Files generated: {total_files}")
    print()
    
    if checkpoint.get('stats'):
        stats = checkpoint['stats']
        print("📊 Generation Stats:")
        print(f"   Started: {stats.get('started_at', 'Unknown')}")
        print(f"   Processed: {stats.get('processed', 0)}")
        print(f"   Failed: {stats.get('failed', 0)}")
        if 'completed_at' in stats:
            print(f"   Completed: {stats['completed_at']}")
        print()
    
    if partial_words:
        print("⚠️  Partial words (need completion):")
        for word, existing, total in partial_words[:10]:
            print(f"   {word}: {existing}/{total} voices")
        if len(partial_words) > 10:
            print(f"   ... and {len(partial_words) - 10} more")
        print()
    
    if complete_count < total_words:
        progress_pct = (complete_count * 100) // total_words
        print(f"📈 Progress: {progress_pct}% ({complete_count}/{total_words})")
        print()
        print("💡 To continue generation:")
        print("   python3 backend/scripts/generate_emoji_audio_variants.py --resume --skip-existing")
    else:
        print("🎉 All words completed!")
    
    print("=" * 80)

if __name__ == "__main__":
    main()





