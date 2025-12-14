/**
 * Vocabulary Pack System Types
 * 
 * Supports multiple vocabulary packs (emoji, themed, etc.)
 * Each pack is self-contained with metadata and vocabulary items.
 * 
 * @see .cursorrules - "Bootstrap Frontloading Strategy"
 */

// Pack metadata
export interface VocabularyPack {
  id: string              // 'emoji_core', 'emoji_animals'
  name: string            // 'Core Emoji'
  name_zh: string         // '核心表情'
  description: string     // English description
  description_zh: string  // Chinese description
  emoji: string           // Pack icon: '🎯'
  difficulty: 1 | 2 | 3 | 4 | 5
  word_count: number
  categories: string[]
  is_free: boolean        // For future monetization
  sort_order: number
  min_age?: number        // Recommended age range
  max_age?: number
}

// Vocabulary item in a pack
export interface PackVocabularyItem {
  sense_id: string        // 'apple.emoji.01'
  word: string            // 'apple'
  emoji: string           // '🍎'
  definition_zh: string   // '蘋果'
  category: string        // 'food'
  difficulty: number      // 1-5 within the pack
  // Optional extended fields for future
  pronunciation?: string  // IPA or phonetic
  example?: string        // Example sentence
  audio_url?: string      // Audio file URL (backward compatibility)
  audio_variants?: string[]  // Array of audio variant filenames (e.g., ["apple_nova.mp3", "apple_coral.mp3", ...])
}

// Full pack file structure
export interface PackFile {
  pack: VocabularyPack
  vocabulary: PackVocabularyItem[]
}

// MCQ types for emoji matching
export interface EmojiMCQ {
  id: string
  type: 'word_to_emoji' | 'emoji_to_word'
  question: {
    text?: string         // "apple" for word_to_emoji
    emoji?: string        // "🍎" for emoji_to_word
    prompt: string        // "What emoji matches this word?"
    prompt_zh: string     // "哪個表情符號配對這個單字？"
  }
  options: EmojiMCQOption[]
  correct_index: number
  difficulty: number
  category: string
  sense_id: string        // Reference back to vocabulary item
}

export interface EmojiMCQOption {
  text?: string           // Word text for emoji_to_word
  emoji?: string          // Emoji for word_to_emoji
  is_correct: boolean
}

// User's pack progress
export interface PackProgress {
  pack_id: string
  words_learned: number
  words_total: number
  accuracy: number
  last_studied: string    // ISO date
  streak_days: number
}

// User's active pack selection
export interface ActivePackSelection {
  pack_ids: string[]      // Active packs (can be multiple)
  primary_pack_id: string // Main pack for new words
}


