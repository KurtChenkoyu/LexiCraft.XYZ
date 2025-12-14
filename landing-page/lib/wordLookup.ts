/**
 * WordLookupService - Robust word/sense lookup with intelligent fallback
 * 
 * This service handles the complexity of looking up words that may exist as:
 * - Direct sense_id (e.g., "happy.a.01")
 * - Word with multiple senses (e.g., "bank" -> bank.n.01, bank.n.02, bank.v.01)
 * - Inflected forms (e.g., "running" -> "run")
 * - Words not in curriculum
 */

import { vocabulary, type VocabularySense } from './vocabulary'

// ============================================
// Types
// ============================================

export type LookupResultType = 
  | 'exact_sense'      // Direct sense_id match
  | 'single_sense'     // Word has exactly one sense
  | 'multiple_senses'  // Word has multiple senses (needs picker)
  | 'fuzzy_match'      // Found via stemming/alternate forms
  | 'not_found'        // Not in vocabulary

export interface LookupResult {
  type: LookupResultType
  senses: VocabularySense[]
  originalQuery: string
  matchedForm?: string  // The form that actually matched (for fuzzy)
  message?: string      // User-facing message
}

export interface NavigationHistoryEntry {
  senseId: string
  word: string
  timestamp: number
}

// ============================================
// Stemming Rules
// ============================================

const SUFFIX_RULES: Array<{ suffix: string; replacement: string }> = [
  // Adverbs
  { suffix: 'ly', replacement: '' },
  
  // Verb forms
  { suffix: 'ing', replacement: '' },
  { suffix: 'ing', replacement: 'e' },  // running -> run, making -> make
  { suffix: 'ed', replacement: '' },
  { suffix: 'ed', replacement: 'e' },   // loved -> love
  { suffix: 'ied', replacement: 'y' },  // tried -> try
  
  // Plurals
  { suffix: 'ies', replacement: 'y' },  // babies -> baby
  { suffix: 'es', replacement: '' },
  { suffix: 's', replacement: '' },
  
  // Comparatives/Superlatives
  { suffix: 'ier', replacement: 'y' },  // happier -> happy
  { suffix: 'iest', replacement: 'y' }, // happiest -> happy
  { suffix: 'er', replacement: '' },
  { suffix: 'est', replacement: '' },
  
  // Nouns from verbs
  { suffix: 'tion', replacement: 'te' }, // celebration -> celebrate
  { suffix: 'ation', replacement: 'e' }, // imagination -> imagine
  { suffix: 'ment', replacement: '' },   // achievement -> achieve
  { suffix: 'ness', replacement: '' },   // happiness -> happy
  { suffix: 'ity', replacement: '' },    // clarity -> clear
]

// ============================================
// WordLookupService
// ============================================

class WordLookupService {
  private navigationHistory: NavigationHistoryEntry[] = []
  private maxHistorySize = 50

  /**
   * Main lookup method - handles all lookup scenarios
   */
  async lookup(query: string): Promise<LookupResult> {
    const normalizedQuery = query.trim().toLowerCase()
    
    if (!normalizedQuery) {
      return {
        type: 'not_found',
        senses: [],
        originalQuery: query,
        message: 'Empty query'
      }
    }

    // 1. Try as direct sense_id
    const directSense = await this.lookupBySenseId(normalizedQuery)
    if (directSense) {
      return {
        type: 'exact_sense',
        senses: [directSense],
        originalQuery: query
      }
    }

    // 2. Try as word (may return multiple senses)
    const wordSenses = await vocabulary.getSensesForWord(normalizedQuery)
    if (wordSenses.length > 0) {
      return {
        type: wordSenses.length === 1 ? 'single_sense' : 'multiple_senses',
        senses: wordSenses,
        originalQuery: query
      }
    }

    // 3. Try alternate forms (stemming)
    const fuzzyResult = await this.lookupWithStemming(normalizedQuery)
    if (fuzzyResult.senses.length > 0) {
      return {
        ...fuzzyResult,
        type: 'fuzzy_match',
        originalQuery: query
      }
    }

    // 4. Not found
    return {
      type: 'not_found',
      senses: [],
      originalQuery: query,
      message: `"${query}" is not in the vocabulary`
    }
  }

  /**
   * Lookup by direct sense_id
   */
  private async lookupBySenseId(senseId: string): Promise<VocabularySense | null> {
    // Check if it looks like a sense_id (word.pos.num format)
    if (!senseId.includes('.')) {
      return null
    }
    return await vocabulary.getSense(senseId)
  }

  /**
   * Try alternate word forms using stemming rules
   */
  private async lookupWithStemming(word: string): Promise<{ senses: VocabularySense[]; matchedForm: string }> {
    for (const rule of SUFFIX_RULES) {
      if (word.endsWith(rule.suffix) && word.length > rule.suffix.length + 2) {
        const stem = word.slice(0, -rule.suffix.length) + rule.replacement
        const senses = await vocabulary.getSensesForWord(stem)
        if (senses.length > 0) {
          return { senses, matchedForm: stem }
        }
      }
    }
    
    // Try common variations
    const variations = [
      word.replace(/([^aeiou])ed$/, '$1'),  // stopped -> stop
      word.replace(/([^aeiou])ing$/, '$1'), // stopping -> stop
    ]
    
    for (const variation of variations) {
      if (variation !== word) {
        const senses = await vocabulary.getSensesForWord(variation)
        if (senses.length > 0) {
          return { senses, matchedForm: variation }
        }
      }
    }
    
    return { senses: [], matchedForm: '' }
  }

  /**
   * Smart navigate - lookup and return the best sense to navigate to
   * Used by chip click handlers
   */
  async smartNavigate(word: string, preferredSenseId?: string): Promise<string | null> {
    // 1. If preferred sense_id provided and exists, use it
    if (preferredSenseId) {
      const sense = await vocabulary.getSense(preferredSenseId)
      if (sense) {
        return preferredSenseId
      }
    }

    // 2. Do full lookup
    const result = await this.lookup(word)
    
    switch (result.type) {
      case 'exact_sense':
      case 'single_sense':
        return result.senses[0]?.id || null
        
      case 'multiple_senses':
        // Return first sense for now - caller should handle picker
        // Could return all and let caller decide
        return result.senses[0]?.id || null
        
      case 'fuzzy_match':
        return result.senses[0]?.id || null
        
      case 'not_found':
      default:
        return null
    }
  }

  /**
   * Check if a word exists in vocabulary (quick check)
   */
  async exists(wordOrSenseId: string): Promise<boolean> {
    const result = await this.lookup(wordOrSenseId)
    return result.type !== 'not_found'
  }

  // ============================================
  // Navigation History
  // ============================================

  /**
   * Push a navigation entry to history
   */
  pushHistory(senseId: string, word: string): void {
    // Don't add duplicate consecutive entries
    const last = this.navigationHistory[this.navigationHistory.length - 1]
    if (last?.senseId === senseId) {
      return
    }

    this.navigationHistory.push({
      senseId,
      word,
      timestamp: Date.now()
    })

    // Trim to max size
    if (this.navigationHistory.length > this.maxHistorySize) {
      this.navigationHistory = this.navigationHistory.slice(-this.maxHistorySize)
    }
  }

  /**
   * Pop and return the previous entry (for back navigation)
   */
  popHistory(): NavigationHistoryEntry | null {
    if (this.navigationHistory.length <= 1) {
      return null
    }
    // Remove current
    this.navigationHistory.pop()
    // Return previous (but don't remove it yet)
    return this.navigationHistory[this.navigationHistory.length - 1] || null
  }

  /**
   * Get current history stack
   */
  getHistory(): NavigationHistoryEntry[] {
    return [...this.navigationHistory]
  }

  /**
   * Clear history
   */
  clearHistory(): void {
    this.navigationHistory = []
  }

  /**
   * Check if we can go back
   */
  canGoBack(): boolean {
    return this.navigationHistory.length > 1
  }
}

// Export singleton instance
export const wordLookup = new WordLookupService()

// Export types
export type { VocabularySense }


