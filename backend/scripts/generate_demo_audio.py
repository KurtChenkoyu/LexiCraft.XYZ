"""
Generate Audio for Demo Words Missing from Pack

Generates audio files for demo words that aren't in the emoji-core.json pack:
- T-Rex
- Popcorn
- Unicorn
- Ninja

Generates all 9 voice variants for each word.

Usage:
    python3 scripts/generate_demo_audio.py
"""

import sys
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
env_paths = [backend_dir / '.env', root_dir / '.env']
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

# All available OpenAI TTS voices (9 valid voices)
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

# Demo words that need audio
DEMO_WORDS = [
    'T-Rex',
    'Popcorn',
    'Unicorn',
    'Ninja',
]

# Output directory (same as emoji pack audio)
OUTPUT_DIR = Path(__file__).parent.parent.parent / "landing-page" / "public" / "audio" / "emoji"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def normalize_word(word: str) -> str:
    """Normalize word for filename (lowercase, replace spaces with underscores)."""
    return word.lower().replace(' ', '_').replace('-', '_')


def generate_audio(word: str, voice: str, client: OpenAI) -> tuple[bool, str]:
    """Generate a single audio file. Returns (success, message)."""
    normalized_word = normalize_word(word)
    filename = f"{normalized_word}_{voice}.mp3"
    filepath = OUTPUT_DIR / filename
    
    # Skip if already exists
    if filepath.exists():
        return (True, f"✅ {filename} already exists")
    
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=word,
            speed=1.0
        )
        response.stream_to_file(str(filepath))
        return (True, f"✅ Generated: {filename}")
    except Exception as e:
        return (False, f"❌ Failed {word} ({voice}): {str(e)}")


def main():
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("   Please set it in your .env file")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    print(f"🎵 Generating audio for {len(DEMO_WORDS)} demo words...")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    
    total_files = len(DEMO_WORDS) * len(ALL_VOICES)
    generated = 0
    skipped = 0
    failed = 0
    
    for word in DEMO_WORDS:
        print(f"📝 Processing: {word}")
        for voice in ALL_VOICES:
            success, message = generate_audio(word, voice, client)
            print(f"  {message}")
            
            if success:
                if "already exists" in message:
                    skipped += 1
                else:
                    generated += 1
            else:
                failed += 1
        
        print()
    
    print("=" * 60)
    print(f"✅ Generated: {generated} files")
    print(f"⏭️  Skipped (already exist): {skipped} files")
    print(f"❌ Failed: {failed} files")
    print(f"📊 Total: {total_files} files")
    print()
    print("🎉 Done! Audio files are ready in:")
    print(f"   {OUTPUT_DIR}")
    print()
    print("💡 Next step: Upload these files to Supabase Storage:")
    print("   landing-page/scripts/upload-audio-to-supabase.js")


if __name__ == '__main__':
    main()

