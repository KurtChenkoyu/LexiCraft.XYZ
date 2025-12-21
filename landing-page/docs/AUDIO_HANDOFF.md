# Audio Generation Handoff Document

## Overview

This document describes the audio infrastructure for LexiCraft and what audio files need to be generated.

## Audio Service Location

`landing-page/lib/audio-service.ts`

## File Structure

```
landing-page/public/audio/
├── emoji/           # Word pronunciations for emoji pack
│   ├── apple.wav
│   ├── banana.wav
│   ├── dog.wav
│   └── ... (200 words)
├── fx/              # Sound effects (5 variants each)
│   ├── correct_001.mp3
│   ├── correct_002.mp3
│   ├── correct_003.mp3
│   ├── correct_004.mp3
│   ├── correct_005.mp3
│   ├── wrong_001.mp3
│   ├── wrong_002.mp3
│   ├── wrong_003.mp3
│   ├── wrong_004.mp3
│   ├── wrong_005.mp3
│   ├── click_001.mp3
│   ├── click_002.mp3
│   ├── click_003.mp3
│   ├── click_004.mp3
│   ├── click_005.mp3
│   ├── levelup_001.mp3
│   ├── levelup_002.mp3
│   ├── levelup_003.mp3
│   ├── levelup_004.mp3
│   ├── levelup_005.mp3
│   ├── celebrate_001.mp3
│   ├── celebrate_002.mp3
│   ├── celebrate_003.mp3
│   ├── celebrate_004.mp3
│   ├── celebrate_005.mp3
│   ├── unlock_001.mp3
│   ├── unlock_002.mp3
│   ├── unlock_003.mp3
│   ├── unlock_004.mp3
│   └── unlock_005.mp3
└── legacy/          # Future: word pronunciations for legacy pack
    └── {sense_id}.wav
```

## Required Audio Files

### 1. Sound Effects (`/audio/fx/`)

Each sound effect has **5 variants** (numbered 001-005) for variety. The audio service randomly selects one variant each time a sound is played, preventing audio fatigue.

| Effect Type | Variants | Description | Duration | Mood | Notes |
|-------------|----------|-------------|----------|------|-------|
| `correct_001.mp3` through `correct_005.mp3` | 5 | Success ding | 0.3-0.5s | Positive, bright | Random selection |
| `wrong_001.mp3` through `wrong_005.mp3` | 5 | Error buzz | 0.3s | Gentle negative | Random selection |
| `celebrate_001.mp3` through `celebrate_005.mp3` | 5 | Big celebration | 1-2s | Triumphant | **Make distinct** - different instruments/styles |
| `click_001.mp3` through `click_005.mp3` | 5 | Button click | 0.1s | Subtle | **Keep similar** - subtle pitch shifts only |
| `unlock_001.mp3` through `unlock_005.mp3` | 5 | Achievement unlocked | 1s | Exciting | Random selection |
| `levelup_001.mp3` through `levelup_005.mp3` | 5 | Level up fanfare | 1.5s | Epic | **Make distinct** - different instruments/styles |

**Total Files:** 30 files (6 effects × 5 variants)

**Recommendations:**
- Keep sounds short and punchy
- Use 44.1kHz, 16-bit
- Keep file sizes small (<100KB each)
- Consider child-friendly, game-like sounds
- **Click sounds:** Keep variants similar (subtle pitch shifts) to avoid feeling "loose"
- **Celebrate/Levelup sounds:** Make variants distinct (different instruments) for excitement

**Source:** Kenney Interface Sounds (free, CC0 license)
- Download: https://github.com/Calinou/kenney-interface-sounds
- Conversion script: `landing-page/scripts/convert-sfx.sh`

### 2. Emoji Pack Word Pronunciations (`/audio/emoji/`)

Generate 11 audio variants for each of the 200 words in the emoji pack (one per OpenAI TTS voice), then select 5 voices per word.

**Source:** `landing-page/data/packs/emoji-core.json`

**Generation Process:**
1. Generate all 11 voices for all words (2,200 files total)
2. Select 5 voices per word (different selection for each word)
3. Store selected 5 in `audio_variants` field in pack JSON

**Voice Settings:**
- Model: `tts-1-hd` (OpenAI TTS HD)
- Voices: All 11 available (alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse)
- Speed: `1.0x`
- Format: `.mp3` (for smaller file size)
- All variants say the word once (for consistent comparison)

**Naming Convention:**
- Format: `{word}_{voice}.mp3`
- Lowercase, spaces replaced with underscores
- Example: `apple_nova.mp3`, `ice_cream_coral.mp3`

**Generation Script:**
```bash
cd backend
export OPENAI_API_KEY='your-key-here'
python3 scripts/generate_emoji_audio_variants.py
```

**After Generation:**
1. Review all 11 voices for each word
2. Select 5 voices that sound best for each specific word
3. Update `emoji-core.json` with `audio_variants` array:
```json
{
  "sense_id": "apple.emoji.01",
  "word": "apple",
  "audio_variants": ["apple_nova.mp3", "apple_coral.mp3", "apple_shimmer.mp3", "apple_echo.mp3", "apple_alloy.mp3"]
}
```

**File Structure:**
```
/audio/emoji/
├── apple_alloy.mp3
├── apple_ash.mp3
├── apple_ballad.mp3
├── ... (all 11 voices for each word)
├── apple_nova.mp3
├── apple_shimmer.mp3
└── ... (2,200 total files: 200 words × 11 voices)
```

### 3. Sentence Audio (Future)

For each word, we'll want a fun example sentence with audio.

**Example JSON structure:**
```json
{
  "word": "apple",
  "emoji": "🍎",
  "sentence": "I eat an apple every day!",
  "sentence_zh": "我每天吃一顆蘋果！",
  "sentence_audio": "/audio/emoji/sentences/apple.wav"
}
```

## Audio Playback Integration

The audio service is already integrated into:

1. **EmojiMCQSession** (`components/features/mcq/EmojiMCQSession.tsx`)
   - Plays `correct.mp3` on correct answer
   - Plays `wrong.mp3` on wrong answer
   - Plays word pronunciation after correct answer
   - Speaker button to play pronunciation on demand

2. **Future Integrations:**
   - Word detail page (play word + sentence)
   - Mine page (click word to hear)
   - Achievement unlocked toast
   - Level up celebration

## API Reference

```typescript
import { audioService } from '@/lib/audio-service'

// Play word pronunciation (randomly selects from word's audio_variants)
audioService.playWord('apple', 'emoji')

// Play specific variant (optional)
audioService.playWord('apple', 'emoji', 0)  // Play first variant

// Get available variants for a word
const variants = await audioService.getWordVariants('apple', 'emoji')
// Returns: ['/audio/emoji/apple_nova.mp3', '/audio/emoji/apple_coral.mp3', ...]

// Play sound effects (randomly selects from 5 variants)
audioService.playCorrect()  // Randomly plays correct_001.mp3 through correct_005.mp3
audioService.playWrong()    // Randomly plays wrong_001.mp3 through wrong_005.mp3
audioService.playCelebrate() // Randomly plays celebrate_001.mp3 through celebrate_005.mp3
audioService.playSfx('levelup') // Randomly plays levelup_001.mp3 through levelup_005.mp3

// Volume control
audioService.setMasterVolume(0.8)
audioService.setSfxVolume(1.0)
audioService.setVoiceVolume(1.0)

// Toggle on/off
audioService.setEnabled(false)

// Preload for instant playback
audioService.preloadSfx(['correct', 'wrong'])  // Preloads all 5 variants (001-005) for each effect
audioService.preloadWords(['apple', 'banana', 'orange'])  // Preloads all variants for each word
```

## Audio Variants System

Each word has 11 audio variants generated (one for each OpenAI TTS voice), but only 5 are selected per word:

- **Generation**: All 11 voices generated for all words (2,200 files total)
- **Selection**: 5 voices selected per word (different selection for each word)
- **Storage**: Selected 5 stored in `audio_variants` array in pack JSON
- **Playback**: System randomly selects from word's 5 variants when playing

**Example:**
- "apple" might use: [nova, coral, shimmer, echo, alloy]
- "dog" might use: [ash, fable, verse, ballad, sage]

**Benefits:**
- Each word gets voices that work well for it
- Provides variety (5 options per word)
- Curated quality - only best-sounding voices per word

## Priority List

1. **HIGH**: Sound effects (correct.mp3, wrong.mp3, celebrate.mp3)
2. **HIGH**: Generate all 11 voices for all 200 words
3. **HIGH**: Select 5 voices per word and update pack JSON
4. **MEDIUM**: Test audio playback with variants
5. **FUTURE**: Sentences audio

## Testing

1. Navigate to `/learner/verification`
2. Start a quiz
3. Answer correctly → should hear correct sound + word
4. Answer wrongly → should hear wrong sound
5. Click speaker button → should hear word

**Test with Apple file:**
The file `apple.wav` has been copied from your Downloads to test the infrastructure.

## Notes for Audio Generator

- **File Format**: MP3 for smaller size (vs WAV)
- **Total Size**: ~110-220MB for all 2,200 files (all 11 voices)
- **Active Size**: ~50-100MB for selected variants (5 per word)
- **Cost**: ~$0.20 for all 2,200 files (OpenAI TTS HD: $15 per 1M chars)
- **Lazy Loading**: Preload only selected 5 variants per word (not all 11)
- **Selection Process**: After generation, manually select 5 voices per word that sound best
- **Future**: Can regenerate with different voice selections if needed (all files kept on disk)

