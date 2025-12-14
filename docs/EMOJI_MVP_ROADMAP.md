# Emoji MVP Roadmap

**Goal**: Ship a focused emoji matching game for young children (4-8) as a learning validation tool.

## Current Status ✅

- [x] Emoji vocabulary pack (200 words)
- [x] Mine page shows emoji cards
- [x] Verification uses emoji MCQs (word↔emoji)
- [x] Compact pack selector dropdown in top nav
- [x] Bootstrap skips legacy 10k vocab when emoji pack active

---

## 1. Audio & Detail Page (Handoff to Another Chat)

### Scope

| Item | Description | Priority |
|------|-------------|----------|
| Word Pronunciation | Native English audio for each word | P0 |
| Chinese Translation Audio | "蘋果" spoken in Mandarin | P1 |
| Fun Example Sentences | "I love to eat apples! 🍎" | P0 |
| Sentence Audio | Full sentence pronunciation | P1 |
| Sound Effects | Correct/Wrong buzzer, celebration sounds | P0 |

### Data Structure (extend `emoji-core.json`)

```json
{
  "sense_id": "apple.emoji.01",
  "word": "apple",
  "emoji": "🍎",
  "definition_zh": "蘋果",
  "audio": {
    "word_en": "/audio/emoji/words/apple.mp3",
    "word_zh": "/audio/emoji/words_zh/apple.mp3",
    "sentence_en": "/audio/emoji/sentences/apple.mp3"
  },
  "example": {
    "en": "I love to eat apples!",
    "zh": "我喜歡吃蘋果！"
  }
}
```

### Word Detail Page Spec

**Route**: `/learner/word/[senseId]`

**For emoji pack items:**
- Large emoji display (80px)
- English word with pronunciation button
- Chinese translation with audio
- Example sentence with audio
- "Practice" button → mini MCQ
- "Mark as known" button

### Audio Generation Options

1. **ElevenLabs API** - High quality, ~$0.001/word
2. **Google Cloud TTS** - Good quality, very cheap
3. **Manual recording** - Highest quality but time-consuming

### Handoff Checklist

```markdown
For the next chat session:

1. [ ] Generate audio files for all 200 emoji words
2. [ ] Create `/audio/emoji/` folder structure
3. [ ] Update `emoji-core.json` with audio paths
4. [ ] Build word detail page component
5. [ ] Add audio playback to MCQ cards
6. [ ] Add celebration sounds for correct answers
```

---

## 2. Separate Landing Page for Emoji MVP

### Rationale

- Current landing: "Kids earn money by learning" - needs parent financial motivation
- Emoji MVP: For very young children (4-8) who don't understand money
- Target: **Fun learning game** that parents can use with kids

### New Landing Page Structure

**Route**: `/emoji` or `/kids` or `/play`

```
Hero Section
├── Fun animated emoji characters
├── "Learn English with Emoji! 🎮"
├── Big "Play Now" button
└── No mention of money/earning

Features (kid-friendly)
├── 🎯 Match words with emojis
├── 🎵 Hear every word spoken
├── 🏆 Earn stars and badges
└── 📊 Parents can track progress

How It Works
├── Step 1: Parent creates account
├── Step 2: Add child's profile
├── Step 3: Hand device to child
└── Step 4: Kid plays, learns, has fun!

Parent Trust Section
├── "No ads, no in-app purchases"
├── "Spaced repetition for real retention"
├── Progress reports sent to parents
└── Safe, offline-capable
```

### Implementation Notes

- Reuse existing auth flow
- After signup, auto-select emoji pack
- Skip the "money motivation" onboarding
- Direct to Mine page immediately

---

## 3. Spaced Repetition for Emoji Pack ✅

**Status**: Already works!

The existing SRS system uses `sense_id` which emoji items have. When a child:

1. Forges a word (hollow status)
2. Completes verification MCQ
3. SRS schedules next review

The verification page already:
- Checks `miningQueue` for words to verify
- Shows emoji MCQs for emoji pack items
- Backend `/submit-batch` handles answer processing

**Minor Enhancement Needed**: Update the verification completion to mark words as "solid" (verified) in local state.

---

## 4. Better Celebrations & Audio

### Correct Answer Celebration

```tsx
// In EmojiMCQSession.tsx after correct answer

const playCelebration = () => {
  // Sound effect
  const audio = new Audio('/audio/sfx/correct.mp3')
  audio.play()
  
  // Visual: confetti burst
  confetti({
    particleCount: 50,
    spread: 60,
    origin: { y: 0.6 }
  })
  
  // Haptic feedback (mobile)
  if (navigator.vibrate) {
    navigator.vibrate(100)
  }
}
```

### Wrong Answer Feedback

```tsx
const playIncorrect = () => {
  // Gentle "try again" sound
  const audio = new Audio('/audio/sfx/incorrect.mp3')
  audio.play()
  
  // Show correct answer highlighted
  // Shake animation on wrong selection
}
```

### Word Audio on Show

When MCQ appears, auto-play the word pronunciation after 0.5s delay.

---

## 5. Parent → Child Quick Switch Flow

### The Challenge

Parents want to quickly let their kid use their phone/tablet for the emoji game, then easily get back to parent view.

### Proposed Solution: "Kid Mode" Button

**In Parent Dashboard:**

```
[Start Kid Mode] button
    ↓
Modal: "Select Child"
    ↓
Enter PIN (optional, parent sets in settings)
    ↓
Redirect to /learner/mine with:
  - Simplified UI (no wallet, no settings)
  - Large tap targets
  - "Exit" requires parent PIN
    ↓
Parent swipe/PIN to return to /parent/dashboard
```

### Implementation

1. **New state**: `kidModeActive: boolean` in Zustand
2. **Simplified LearnerTopBar** when kid mode active:
   - No wallet
   - No settings link
   - Just logo + pack indicator + streak
   - "Exit" button (PIN protected)

3. **Route guard**: When kid mode + parent tries to access `/parent/*`:
   - Show PIN modal
   - Wrong PIN = stay in kid mode
   - Right PIN = exit kid mode, go to parent

### UI in Parent Dashboard

Add to the top of Parent Dashboard:

```tsx
<div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 rounded-xl mb-6">
  <div className="flex items-center justify-between">
    <div>
      <h3 className="text-white font-bold">👶 孩子模式</h3>
      <p className="text-white/80 text-sm">讓孩子用您的設備練習</p>
    </div>
    <button className="bg-white text-purple-600 px-4 py-2 rounded-lg font-bold">
      開始
    </button>
  </div>
</div>
```

---

## Priority Order for Implementation

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| P0 | Dropdown selector | ✅ Done | UX Fix |
| P0 | Audio for words | 2h | Core Feature |
| P0 | Correct/Wrong sounds | 1h | Engagement |
| P1 | Word detail page | 3h | Depth |
| P1 | Kid Mode switch | 4h | Accessibility |
| P2 | Emoji landing page | 4h | Marketing |
| P2 | Sentence audio | 2h | Polish |

---

## Audio Files Needed (200 words)

Generate audio for these categories from `emoji-core.json`:

- 20 Food words
- 20 Animal words
- 20 Nature words
- 20 Feeling words
- 20 Place words
- 20 Object words
- 20 Action words
- 20 People words
- 20 Color words
- 20 Number words

**Estimated cost**: ~$0.20 with Google Cloud TTS or $2 with ElevenLabs

---

## Next Steps for Current Chat

1. ✅ Fix dropdown selector
2. Add audio playback infrastructure
3. Add celebration effects to MCQ
4. Create word detail page skeleton

## Handoff Items for Future Chats

1. Generate all 200 audio files
2. Build emoji-specific landing page
3. Implement Kid Mode flow
4. Add sentence audio and examples


