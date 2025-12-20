/**
 * Vocabulary Store - IndexedDB-backed vocabulary data
 * 
 * Provides async lookups for vocabulary data from IndexedDB.
 * No direct import of vocabulary.json - loads from IndexedDB hydrated by web worker.
 */

import { Block, BlockDetail, BlockConnection } from '@/types/mine'
// Lazy import to prevent SSR issues - vocabularyDB is only accessed in async methods
import type { VocabularySenseIndexed } from './vocabularyDB'
import { isVocabularyReady } from './vocabularyDB'

// Lazy getter for vocabularyDB to prevent SSR access
async function getVocabularyDB() {
  const { vocabularyDB } = await import('./vocabularyDB')
  return vocabularyDB
}

/**
 * Types for vocabulary data structure
 */
export interface VocabularySense {
  id?: string
  word: string
  lemma?: string  // Base form extracted from sense_id (e.g., 'be' for 'be.v.01')
  definition_en?: string
  definition?: string
  definition_zh?: string
  definition_zh_explanation?: string
  example_en?: string
  example_zh?: string
  example_zh_explanation?: string
  pos?: string | null
  enriched?: boolean
  frequency_rank?: number | null
  cefr?: string
  rank?: number  // Renamed from tier to rank (word complexity 1-7)
  validated?: boolean
  connections?: {
    // OLD (kept from WordNet)
    confused?: Array<{ sense_id: string; reason: string }>
    
    // NEW (Gemini-generated pedagogical data)
    synonyms?: {
      sense_ids: string[]
      display_words: string[]
    }
    antonyms?: {
      sense_ids: string[]
      display_words: string[]
    }
    collocations?: Array<{
      phrase: string
      cefr?: string              // A1, A2, B1, B2, C1, C2
      register?: string          // formal, neutral, informal
      meaning: string
      meaning_zh: string
      example: string
      example_en_explanation?: string  // Teaches English mental model
      example_zh_explanation: string   // Teaches English thinking in Chinese
    }>
    word_family?: {
      noun?: string[]
      verb?: string[]
      adjective?: string[]
      adverb?: string[]
    }
    forms?: {
      comparative?: string[]
      superlative?: string[]
      past?: string[]
      past_participle?: string[]
      plural?: string[]
    }
    similar_words?: {
      sense_ids: string[]
      display_words: string[]
    }
  }
  collocation_sources?: {
    ngsl?: number
    wordnet?: number
    datamuse?: number
  }
  connection_counts?: {
    related?: number
    opposite?: number
    total?: number
  }
  value?: {
    base_xp?: number
    connection_bonus?: number
    total_xp?: number
  }
}

export interface VocabularyWord {
  name: string
  frequency_rank: number | null
  moe_level: number | null
  ngsl_rank: number | null
  senses: string[]
}

interface VocabularyRelationships {
  related: string[]
  opposite: string[]
}

interface GraphNode {
  id: string
  word: string
  pos: string
  value: number
  tier: number
  definition_en: string
  definition_zh: string
}

interface GraphEdge {
  source: string
  target: string
  type: 'related' | 'opposite'
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface VocabularyData {
  version: string
  exportedAt?: string
  generated_at?: string
  words: Record<string, VocabularyWord>
  senses: Record<string, VocabularySense>
  relationships?: Record<string, VocabularyRelationships>
  bandIndex?: Record<string, string[]>
  graph_data?: GraphData
}

/**
 * Vocabulary Store Class
 * 
 * Singleton that provides async IndexedDB lookups for vocabulary data.
 * Maintains an in-memory cache for frequently accessed data.
 */
class VocabularyStore {
  private cache = new Map<string, VocabularySense>()
  private lemmaIndex = new Map<string, string[]>()
  private version: string = '3.0-stage3'
  
  /**
   * Extract lemma from sense_id.
   * e.g., 'be.v.01' -> 'be', 'apple.n.01' -> 'apple'
   */
  private extractLemma(senseId: string): string {
    const parts = senseId.split('.')
    return parts[0] || senseId
  }
  
  /**
   * Clear all in-memory caches. 
   * MUST be called when vocabulary is refreshed to prevent stale data.
   */
  clearCache(): void {
    this.cache.clear()
    this.lemmaIndex.clear()
    console.log('🗑️ VocabularyStore cache cleared')
  }

  /**
   * Check if vocabulary data is loaded in IndexedDB
   */
  async isLoaded(): Promise<boolean> {
    const isReady = await isVocabularyReady()
    return isReady
  }

  /**
   * Get sense count
   */
  async senseCount(): Promise<number> {
    const db = await getVocabularyDB()
    return await db.senses.count()
  }

  /**
   * Get word count (unique lemmas)
   */
  async wordCount(): Promise<number> {
    if (this.lemmaIndex.size === 0) {
      await this.buildLemmaIndex()
    }
    return this.lemmaIndex.size
  }

  /**
   * Build lemma index from IndexedDB (lazy load)
   */
  private async buildLemmaIndex(): Promise<void> {
    if (this.lemmaIndex.size > 0) return // Already built
    
    const db = await getVocabularyDB()
    const allSenses = await db.senses.toArray()
    for (const sense of allSenses) {
      const lemma = this.extractLemma(sense.id).toLowerCase()
      if (!this.lemmaIndex.has(lemma)) {
        this.lemmaIndex.set(lemma, [])
      }
      this.lemmaIndex.get(lemma)!.push(sense.id)
    }
    console.log(`Built lemma index: ${this.lemmaIndex.size} lemmas from ${allSenses.length} senses`)
  }

  /**
   * Get a sense by ID (with caching)
   */
  async getSense(senseId: string): Promise<VocabularySense | null> {
    // Check cache first
    if (this.cache.has(senseId)) {
      return this.cache.get(senseId)!
    }
    
    // Query IndexedDB
    const db = await getVocabularyDB()
    const sense = await db.senses.get(senseId)
    if (sense) {
      const vocabSense = { ...sense, id: sense.id }
      this.cache.set(senseId, vocabSense)
      return vocabSense
    }
    
    return null
  }

  /**
   * Get multiple senses by IDs (batch query)
   */
  async getSenses(senseIds: string[]): Promise<VocabularySense[]> {
    const results: VocabularySense[] = []
    const toFetch: string[] = []
    
    // Check cache first
    for (const id of senseIds) {
      const cached = this.cache.get(id)
      if (cached) {
        results.push(cached)
      } else {
        toFetch.push(id)
      }
    }
    
    // Fetch missing from IndexedDB
    if (toFetch.length > 0) {
      const db = await getVocabularyDB()
      const fetched = await db.senses.bulkGet(toFetch)
      for (const sense of fetched) {
        if (sense) {
          const vocabSense = { ...sense, id: sense.id }
          this.cache.set(sense.id, vocabSense)
          results.push(vocabSense)
        }
      }
    }
    
    return results
  }

  /**
   * Get word info by lemma
   */
  async getWord(wordName: string): Promise<VocabularyWord | null> {
    if (this.lemmaIndex.size === 0) {
      await this.buildLemmaIndex()
    }
    
    const lemma = wordName.toLowerCase()
    const senseIds = this.lemmaIndex.get(lemma)
    if (!senseIds || senseIds.length === 0) return null
    
    // Get first sense for frequency info
    const firstSense = await this.getSense(senseIds[0])
    
    return {
      name: lemma,
      frequency_rank: firstSense?.frequency_rank ?? null,
      moe_level: null,
      ngsl_rank: null,
      senses: senseIds
    }
  }

  /**
   * Get all senses for a word (by lemma)
   */
  async getSensesForWord(wordName: string): Promise<VocabularySense[]> {
    if (this.lemmaIndex.size === 0) {
      await this.buildLemmaIndex()
    }
    
    const lemma = wordName.toLowerCase()
    const senseIds = this.lemmaIndex.get(lemma) || []
    
    return await this.getSenses(senseIds)
  }

  /**
   * Get all sense IDs for a word (by lemma)
   */
  async getSenseIdsForWord(wordName: string): Promise<string[]> {
    if (this.lemmaIndex.size === 0) {
      await this.buildLemmaIndex()
    }
    
    const lemma = wordName.toLowerCase()
    return this.lemmaIndex.get(lemma) || []
  }

  /**
   * Get random senses from a frequency band
   */
  async getRandomSensesInBand(
    minRank: number,
    maxRank: number,
    count: number = 10,
    excludeSenses: string[] = []
  ): Promise<VocabularySense[]> {
    const excludeSet = new Set(excludeSenses)
    
    // Query IndexedDB for senses in rank range
    const db = await getVocabularyDB()
    const senses = await db.senses
      .where('frequency_rank')
      .between(minRank, maxRank)
      .toArray()
    
    // Filter and shuffle
    const available = senses.filter(s => !excludeSet.has(s.id))
    const shuffled = [...available].sort(() => Math.random() - 0.5)
    
    return shuffled.slice(0, count).map(s => ({ ...s, id: s.id }))
  }

  /**
   * Get starter pack of blocks
   */
  async getStarterPack(limit: number = 50): Promise<Block[]> {
    const allBlocks: Block[] = []
    
    // Debug: Check if vocabularyDB is accessible
    const db = await getVocabularyDB()
    const dbCount = await db.senses.count()
    console.log('🎲 getStarterPack: vocabularyDB count =', dbCount)
    
    // Distribution across frequency bands
    const bandsConfig: [number, number, number][] = [
      [1, 1000, 10],     // Band 1: 10 words
      [1001, 2000, 10],  // Band 2: 10 words
      [2001, 3000, 15],  // Band 3: 15 words
      [3001, 4000, 15],  // Band 4: 15 words
    ]

    for (const [minRank, maxRank, count] of bandsConfig) {
      console.log(`🎲 Fetching ${count} words from rank ${minRank}-${maxRank}...`)
      const senses = await this.getRandomSensesInBand(minRank, maxRank, count)
      console.log(`🎲 Got ${senses.length} senses from band`)
      for (const sense of senses) {
        allBlocks.push(this.senseToBlock(sense))
      }
    }

    console.log(`🎲 Total blocks generated: ${allBlocks.length}`)
    
    // Shuffle and limit
    return allBlocks
      .sort(() => Math.random() - 0.5)
      .slice(0, limit)
  }

  /**
   * Get related sense IDs
   */
  async getRelatedSenses(senseId: string): Promise<string[]> {
    const sense = await this.getSense(senseId)
    // In new schema, use synonyms + similar_words
    const related = [
      ...(sense?.connections?.synonyms?.sense_ids || []),
      ...(sense?.connections?.similar_words?.sense_ids || [])
    ]
    return related
  }

  /**
   * Get opposite sense IDs
   */
  async getOppositeSenses(senseId: string): Promise<string[]> {
    const sense = await this.getSense(senseId)
    // In new schema, use antonyms
    return sense?.connections?.antonyms?.sense_ids || []
  }

  /**
   * Get all connections for a sense
   */
  async getConnections(senseId: string): Promise<BlockConnection[]> {
    const connections: BlockConnection[] = []
    const sense = await this.getSense(senseId)
    const conns = sense?.connections || {}

    // Collect all connection IDs from new schema
    const synonymIds = conns.synonyms?.sense_ids || []
    const antonymIds = conns.antonyms?.sense_ids || []
    const similarIds = conns.similar_words?.sense_ids || []
    const confusedIds = (conns.confused || []).map(c => c.sense_id)

    // Batch fetch all connected senses
    const allIds = [...synonymIds, ...antonymIds, ...similarIds, ...confusedIds]
    const connectedSenses = await this.getSenses(allIds)
    const senseMap = new Map(connectedSenses.map(s => [s.id!, s]))

    // Build connections array
    for (const synId of synonymIds) {
      const synSense = senseMap.get(synId)
      if (synSense) {
        connections.push({
          sense_id: synId,
          word: synSense.word,
          type: 'SYNONYM',
        })
      }
    }

    for (const antId of antonymIds) {
      const antSense = senseMap.get(antId)
      if (antSense) {
        connections.push({
          sense_id: antId,
          word: antSense.word,
          type: 'ANTONYM',
        })
      }
    }

    for (const similarId of similarIds) {
      const similarSense = senseMap.get(similarId)
      if (similarSense) {
        connections.push({
          sense_id: similarId,
          word: similarSense.word,
          type: 'SIMILAR',
        })
      }
    }

    for (const confId of confusedIds) {
      const confSense = senseMap.get(confId)
      if (confSense) {
        connections.push({
          sense_id: confId,
          word: confSense.word,
          type: 'CONFUSED_WITH',
        })
      }
    }

    return connections
  }

  /**
   * Get collocations/phrases for a sense
   */
  async getCollocations(senseId: string): Promise<string[]> {
    const sense = await this.getSense(senseId)
    return (sense?.connections?.collocations || []).map(c => c.phrase)
  }

  /**
   * Get derivations for a sense
   */
  async getDerivations(senseId: string): Promise<string[]> {
    const sense = await this.getSense(senseId)
    // In new schema, return all words from word_family
    const family = sense?.connections?.word_family || {}
    return Object.values(family).flat()
  }

  /**
   * Get morphological forms for a sense
   */
  async getMorphologicalForms(senseId: string): Promise<string[]> {
    const sense = await this.getSense(senseId)
    // In new schema, return all forms
    const forms = sense?.connections?.forms || {}
    return Object.values(forms).flat()
  }

  /**
   * Get full block detail with connections
   */
  async getBlockDetail(senseId: string): Promise<BlockDetail | null> {
    const sense = await this.getSense(senseId)
    if (!sense) return null

    const connections = await this.getConnections(senseId)

    // Build definition with explanation
    let definitionZh = sense.definition_zh || ''
    if (sense.definition_zh_explanation) {
      definitionZh = `${definitionZh} ${sense.definition_zh_explanation}`.trim()
    }

    let exampleZh = sense.example_zh || ''
    if (sense.example_zh_explanation) {
      exampleZh = `${exampleZh} ${sense.example_zh_explanation}`.trim()
    }

    // Get other senses of the same lemma (base word)
    // Use lemma for lookup, not word (e.g., "doctor" not "docs")
    const lookupWord = sense.lemma || this.extractLemma(senseId) || sense.word
    const allSensesForWord = await this.getSensesForWord(lookupWord)
    
    // Filter and deduplicate
    const seenIds = new Set<string>()
    const otherSenses = allSensesForWord
      .filter(s => {
        if (!s.id || s.id === senseId || seenIds.has(s.id)) return false
        seenIds.add(s.id)
        return true
      })
      .map(s => ({
        sense_id: s.id as string,
        word: s.word,
        pos: s.pos || undefined,
        definition_preview: (s.definition_en || s.definition || '').slice(0, 80),
      }))

    return {
      sense_id: senseId,
      word: sense.word,
      pos: sense.pos || undefined,
      tier: 1,
      base_xp: 100,
      connection_count: connections.length,
      total_value: 100 + connections.length * 10,
      rank: sense.frequency_rank ?? undefined,
      definition_en: sense.definition_en || '',
      definition_zh: definitionZh,
      example_en: sense.example_en || '',
      example_zh: exampleZh,
      connections,
      other_senses: otherSenses,
    }
  }

  /**
   * Convert sense to Block format
   */
  private senseToBlock(sense: VocabularySense, senseId?: string): Block {
    const id = senseId || sense.id || `${sense.word}.unknown`
    const connectionCount = sense.connection_counts?.total || 
      ((sense.connections?.synonyms?.sense_ids?.length || 0) + 
       (sense.connections?.antonyms?.sense_ids?.length || 0) + 
       (sense.connections?.similar_words?.sense_ids?.length || 0))
    const baseXp = sense.value?.base_xp || 100
    const totalValue = sense.value?.total_xp || (baseXp + connectionCount * 10)
    
    return {
      sense_id: id,
      word: sense.word,
      definition_preview: (sense.definition_en || sense.definition_zh || '').slice(0, 100),
      rank: sense.rank || sense.tier || 1,  // Use rank (new) or fallback to tier (legacy)
      base_xp: baseXp,
      connection_count: connectionCount,
      total_value: totalValue,
      status: 'raw',
      rank: sense.frequency_rank ?? undefined,
    }
  }

  /**
   * Get random traps/distractors for MCQ/survey
   */
  async getRandomTraps(
    excludeWord: string,
    count: number = 3,
    nearRank?: number
  ): Promise<VocabularySense[]> {
    let candidates: VocabularySenseIndexed[]

    const db = await getVocabularyDB()
    if (nearRank) {
      // Get senses from nearby frequency range
      const searchRadius = 500
      candidates = await db.senses
        .where('frequency_rank')
        .between(Math.max(1, nearRank - searchRadius), nearRank + searchRadius)
        .filter(s => s.word !== excludeWord)
        .toArray()
    } else {
      // Get random senses (limit to first 5000 for performance)
      candidates = await db.senses
        .where('frequency_rank')
        .between(1, 5000)
        .filter(s => s.word !== excludeWord)
        .toArray()
    }

    // Random sample
    const shuffled = [...candidates].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, count).map(s => ({ ...s, id: s.id }))
  }

  /**
   * Search senses by frequency rank range
   */
  async searchByRank(minRank: number, maxRank: number, limit: number = 10): Promise<VocabularySense[]> {
    const db = await getVocabularyDB()
    const results = await db.senses
      .where('frequency_rank')
      .between(minRank, maxRank)
      .limit(limit)
      .toArray()

    return results.map(s => ({ ...s, id: s.id }))
  }

  /**
   * Search senses by query string
   */
  async searchSenses(
    query: string,
    options: {
      limit?: number
      cefrFilter?: string[]
      sortBy?: 'relevance' | 'cefr' | 'connections' | 'rank'
    } = {}
  ): Promise<Array<VocabularySense & { score: number; connection_count: number }>> {
    const { limit = 50, cefrFilter, sortBy = 'relevance' } = options
    const normalizedQuery = query.toLowerCase().trim()
    const results: Array<VocabularySense & { score: number; connection_count: number }> = []

    // Query IndexedDB - for empty query or browsing, get top frequency words
    const db = await getVocabularyDB()
    let candidates: VocabularySenseIndexed[]
    if (normalizedQuery === '') {
      candidates = await db.senses
        .where('frequency_rank')
        .between(1, 3000)
        .limit(200)
        .toArray()
    } else {
      // Get words that start with or contain the query
      candidates = await db.senses
        .where('word')
        .startsWith(normalizedQuery)
        .toArray()
      
      // Also search by lemma (extracted from sense_id or lemma field)
      // This finds 'be' when searching for 'be' even if word is 'were'
      if (this.lemmaIndex.size === 0) {
        await this.buildLemmaIndex()
      }
      const lemmaMatches = this.lemmaIndex.get(normalizedQuery) || []
      if (lemmaMatches.length > 0) {
        const lemmaSenses = await this.getSenses(lemmaMatches)
        for (const sense of lemmaSenses) {
          if (!candidates.some(c => c.id === sense.id)) {
            candidates.push(sense as VocabularySenseIndexed)
          }
        }
      }
      
      // Also search for words/lemmas containing the query (if too few results)
      if (candidates.length < limit) {
        const allSenses = await db.senses.limit(2000).toArray()
        const containing = allSenses.filter(s => {
          const word = s.word?.toLowerCase() || ''
          const lemma = this.extractLemma(s.id).toLowerCase()
          return (word.includes(normalizedQuery) || lemma.includes(normalizedQuery)) &&
            !candidates.some(c => c.id === s.id)
        })
        candidates = [...candidates, ...containing]
      }
    }

    // Apply CEFR filter
    if (cefrFilter && cefrFilter.length > 0) {
      candidates = candidates.filter(s => cefrFilter.includes(s.cefr || ''))
    }

    // Calculate relevance scores
    for (const sense of candidates) {
      const word = sense.word?.toLowerCase() || ''
      const lemma = this.extractLemma(sense.id).toLowerCase()
      const defEn = (sense.definition_en || sense.definition || '').toLowerCase()
      const defZh = sense.definition_zh || ''

      let score = 0

      if (normalizedQuery === '') {
        score = 50 // Base score for browsing mode
      } else {
        // Prioritize lemma matches (finds 'be' even when word is 'were')
        if (lemma === normalizedQuery) score = 100  // Exact lemma match
        else if (word === normalizedQuery) score = 95  // Exact word match
        else if (lemma.startsWith(normalizedQuery)) score = 85  // Lemma starts with
        else if (word.startsWith(normalizedQuery)) score = 80  // Word starts with
        else if (lemma.includes(normalizedQuery)) score = 65  // Lemma contains
        else if (word.includes(normalizedQuery)) score = 60  // Word contains
        else if (defEn.includes(normalizedQuery)) score = 40
        else if (defZh.includes(normalizedQuery)) score = 30
      }

      if (score > 0) {
        const connections = await this.getConnections(sense.id)
        results.push({
          ...sense,
          id: sense.id,
          score,
          connection_count: connections.length,
        })
      }
    }

    // Sort results
    results.sort((a, b) => {
      switch (sortBy) {
        case 'cefr':
          const cefrOrder = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
          const aIdx = cefrOrder.indexOf(a.cefr || 'C2')
          const bIdx = cefrOrder.indexOf(b.cefr || 'C2')
          return aIdx - bIdx
        case 'connections':
          return b.connection_count - a.connection_count
        case 'rank':
          return (a.frequency_rank || 99999) - (b.frequency_rank || 99999)
        case 'relevance':
        default:
          return b.score - a.score
      }
    })

    return results.slice(0, limit)
  }

  /**
   * Get all sense IDs (warning: expensive operation)
   */
  async getAllSenseIds(): Promise<string[]> {
    const db = await getVocabularyDB()
    const senses = await db.senses.toCollection().primaryKeys()
    return senses
  }
}

// Export singleton instance
export const vocabulary = new VocabularyStore()

// Export types already defined above with export keyword
