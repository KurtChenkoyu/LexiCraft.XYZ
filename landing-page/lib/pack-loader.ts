/**
 * Pack Loader - Loads and manages vocabulary packs
 * 
 * Handles:
 * - Loading pack JSON files
 * - Caching in IndexedDB
 * - Generating MCQs from pack vocabulary
 * 
 * @see .cursorrules - "Bootstrap Frontloading Strategy"
 */

import { PackFile, PackVocabularyItem, EmojiMCQ, EmojiMCQOption, VocabularyPack } from './pack-types'
import { localStore } from './local-store'

// Available packs (extend as we add more)
const PACK_REGISTRY: Record<string, () => Promise<PackFile>> = {
  'emoji_core': () => import('@/data/packs/emoji-core.json').then(m => m.default as PackFile),
  // Future packs:
  // 'emoji_animals': () => import('@/data/packs/emoji-animals.json'),
  // 'emoji_food': () => import('@/data/packs/emoji-food.json'),
}

class PackLoader {
  private loadedPacks: Map<string, PackFile> = new Map()
  private isLoading: boolean = false

  /**
   * Get list of available packs
   */
  getAvailablePacks(): string[] {
    return Object.keys(PACK_REGISTRY)
  }

  /**
   * Load a pack by ID
   */
  async loadPack(packId: string): Promise<PackFile | null> {
    // Return cached if available
    if (this.loadedPacks.has(packId)) {
      return this.loadedPacks.get(packId)!
    }

    // Check IndexedDB cache (try both cache keys for compatibility)
    // Bootstrap caches as 'emoji_vocabulary' (just vocabulary array)
    // packLoader caches as 'pack_emoji_core' (full PackFile)
    let cached: PackFile | null = null
    
    if (packId === 'emoji_core') {
      // Try Bootstrap's cache key first (faster - just vocabulary)
      const vocabCache = await localStore.getCache<PackVocabularyItem[]>('emoji_vocabulary')
      if (vocabCache && vocabCache.length > 0) {
        // Reconstruct PackFile from vocabulary (we don't have full pack metadata, but that's OK)
        // For emoji_core, we can create a minimal PackFile
        cached = {
          pack: {
            id: 'emoji_core',
            name: 'Core Emoji',
            name_zh: '核心表情符號',
            description: '200 essential emoji words',
            description_zh: '200個核心表情符號單字',
            word_count: vocabCache.length,
            difficulty_range: [1, 5],
            categories: Array.from(new Set(vocabCache.map(v => v.category))),
          },
          vocabulary: vocabCache,
        } as PackFile
        this.loadedPacks.set(packId, cached)
        if (process.env.NODE_ENV === 'development') {
          console.log(`⚡ Loaded emoji pack from Bootstrap cache (${vocabCache.length} words)`)
        }
        return cached
      }
    }
    
    // Try packLoader's cache key
    cached = await localStore.getCache<PackFile>(`pack_${packId}`)
    if (cached) {
      this.loadedPacks.set(packId, cached)
      return cached
    }

    // Load from registry
    const loader = PACK_REGISTRY[packId]
    if (!loader) {
      console.warn(`Pack not found: ${packId}`)
      return null
    }

    try {
      const pack = await loader()
      this.loadedPacks.set(packId, pack)
      
      // Cache in IndexedDB (30 days)
      await localStore.setCache(`pack_${packId}`, pack, 30 * 24 * 60 * 60 * 1000)
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`📦 Loaded pack: ${packId} (${pack.vocabulary.length} words)`)
      }
      
      return pack
    } catch (error) {
      console.error(`Failed to load pack ${packId}:`, error)
      return null
    }
  }

  /**
   * Get pack metadata only (without loading full vocabulary)
   */
  async getPackMetadata(packId: string): Promise<VocabularyPack | null> {
    const pack = await this.loadPack(packId)
    return pack?.pack || null
  }

  /**
   * Get vocabulary items from a pack
   */
  async getVocabulary(packId: string): Promise<PackVocabularyItem[]> {
    const pack = await this.loadPack(packId)
    return pack?.vocabulary || []
  }

  /**
   * Get vocabulary item by sense_id
   */
  async getItem(packId: string, senseId: string): Promise<PackVocabularyItem | null> {
    const vocab = await this.getVocabulary(packId)
    return vocab.find(v => v.sense_id === senseId) || null
  }

  /**
   * Get vocabulary items by category
   */
  async getByCategory(packId: string, category: string): Promise<PackVocabularyItem[]> {
    const vocab = await this.getVocabulary(packId)
    return vocab.filter(v => v.category === category)
  }

  /**
   * Get vocabulary items by difficulty
   */
  async getByDifficulty(packId: string, difficulty: number): Promise<PackVocabularyItem[]> {
    const vocab = await this.getVocabulary(packId)
    return vocab.filter(v => v.difficulty === difficulty)
  }

  /**
   * Generate MCQs for a vocabulary item
   * Creates both word→emoji and emoji→word questions
   */
  async generateMCQs(
    packId: string, 
    senseId: string,
    distractorCount: number = 3
  ): Promise<EmojiMCQ[]> {
    const pack = await this.loadPack(packId)
    if (!pack) return []

    const item = pack.vocabulary.find(v => v.sense_id === senseId)
    if (!item) return []

    const mcqs: EmojiMCQ[] = []

    // Get distractors from same category first, then fill from others
    const sameCategory = pack.vocabulary.filter(
      v => v.category === item.category && v.sense_id !== senseId
    )
    const otherCategory = pack.vocabulary.filter(
      v => v.category !== item.category && v.sense_id !== senseId
    )

    // Shuffle and pick distractors
    const shuffled = [...sameCategory.sort(() => Math.random() - 0.5)]
    if (shuffled.length < distractorCount) {
      shuffled.push(...otherCategory.sort(() => Math.random() - 0.5))
    }
    const distractors = shuffled.slice(0, distractorCount)

    // MCQ Type 1: Word → Emoji
    const wordToEmojiOptions: EmojiMCQOption[] = [
      { emoji: item.emoji, is_correct: true },
      ...distractors.map(d => ({ emoji: d.emoji, is_correct: false }))
    ].sort(() => Math.random() - 0.5)

    mcqs.push({
      id: `${senseId}_w2e`,
      type: 'word_to_emoji',
      question: {
        text: item.word,
        prompt: `Which emoji matches "${item.word}"?`,
        prompt_zh: `哪個表情符號配對 "${item.word}"？`
      },
      options: wordToEmojiOptions,
      correct_index: wordToEmojiOptions.findIndex(o => o.is_correct),
      difficulty: item.difficulty,
      category: item.category,
      sense_id: senseId
    })

    // MCQ Type 2: Emoji → Word
    const emojiToWordOptions: EmojiMCQOption[] = [
      { text: item.word, is_correct: true },
      ...distractors.map(d => ({ text: d.word, is_correct: false }))
    ].sort(() => Math.random() - 0.5)

    mcqs.push({
      id: `${senseId}_e2w`,
      type: 'emoji_to_word',
      question: {
        emoji: item.emoji,
        prompt: `Which word matches ${item.emoji}?`,
        prompt_zh: `哪個單字配對 ${item.emoji}？`
      },
      options: emojiToWordOptions,
      correct_index: emojiToWordOptions.findIndex(o => o.is_correct),
      difficulty: item.difficulty,
      category: item.category,
      sense_id: senseId
    })

    return mcqs
  }

  /**
   * Generate a batch of MCQs for multiple items
   */
  async generateMCQBatch(
    packId: string,
    senseIds: string[],
    mcqsPerItem: number = 2
  ): Promise<EmojiMCQ[]> {
    const allMcqs: EmojiMCQ[] = []
    
    for (const senseId of senseIds) {
      const mcqs = await this.generateMCQs(packId, senseId)
      allMcqs.push(...mcqs.slice(0, mcqsPerItem))
    }

    // Shuffle the batch
    return allMcqs.sort(() => Math.random() - 0.5)
  }

  /**
   * Get starter pack items (for Mine page)
   * Returns items sorted by difficulty
   */
  async getStarterItems(
    packId: string,
    count: number = 50
  ): Promise<PackVocabularyItem[]> {
    const vocab = await this.getVocabulary(packId)
    
    // Sort by difficulty (easiest first)
    const sorted = [...vocab].sort((a, b) => a.difficulty - b.difficulty)
    
    return sorted.slice(0, count)
  }

  /**
   * Get random items for practice
   */
  async getRandomItems(
    packId: string,
    count: number = 10,
    excludeSenseIds: string[] = []
  ): Promise<PackVocabularyItem[]> {
    const vocab = await this.getVocabulary(packId)
    
    const available = vocab.filter(v => !excludeSenseIds.includes(v.sense_id))
    const shuffled = available.sort(() => Math.random() - 0.5)
    
    return shuffled.slice(0, count)
  }

  /**
   * Clear cached packs
   */
  async clearCache(): Promise<void> {
    this.loadedPacks.clear()
    for (const packId of Object.keys(PACK_REGISTRY)) {
      await localStore.deleteCache(`pack_${packId}`)
    }
  }
}

// Singleton instance
export const packLoader = new PackLoader()


