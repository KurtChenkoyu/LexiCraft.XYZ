/**
 * Vocabulary Store - Client-side in-memory vocabulary data
 * 
 * Provides instant lookups for vocabulary data without API calls.
 * Data is bundled with the app from vocabulary.json.
 */

import { Block, BlockDetail, BlockConnection } from '@/types/mine'

// Import vocabulary data - will be tree-shaken if not used
// @ts-ignore - JSON import
import vocabularyData from '@/data/vocabulary.json'

/**
 * Types for vocabulary data structure
 */
interface VocabularySense {
  id?: string
  word: string
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
  tier?: number
  validated?: boolean
  connections?: {
    related?: string[]
    opposite?: string[]
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

interface VocabularyWord {
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

interface GraphData {
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
 * Singleton that provides fast in-memory lookups for vocabulary data.
 */
class VocabularyStore {
  private data: VocabularyData
  private _isLoaded: boolean = false

  constructor() {
    this.data = vocabularyData as VocabularyData
    this._isLoaded = Object.keys(this.data.senses || {}).length > 0
  }

  /**
   * Check if vocabulary data is loaded
   */
  get isLoaded(): boolean {
    return this._isLoaded
  }

  /**
   * Get vocabulary version
   */
  get version(): string {
    return this.data.version || '0.0'
  }

  /**
   * Get sense count
   */
  get senseCount(): number {
    return Object.keys(this.data.senses || {}).length
  }

  /**
   * Get word count
   */
  get wordCount(): number {
    return Object.keys(this.data.words || {}).length
  }

  /**
   * Get a sense by ID
   */
  getSense(senseId: string): VocabularySense | null {
    return this.data.senses?.[senseId] || null
  }

  /**
   * Get all senses as a record
   */
  getAllSenses(): Record<string, VocabularySense> {
    return this.data.senses || {}
  }

  /**
   * Get a word by name
   */
  getWord(wordName: string): VocabularyWord | null {
    return this.data.words?.[wordName] || null
  }

  /**
   * Get all senses for a word
   */
  getSensesForWord(wordName: string): VocabularySense[] {
    const word = this.data.words?.[wordName]
    if (!word) return []
    
    return word.senses
      .map(senseId => this.data.senses?.[senseId])
      .filter((s): s is VocabularySense => s !== undefined)
  }

  /**
   * Get random senses from a frequency band or all senses
   */
  getRandomSensesInBand(
    band: number, 
    count: number = 10,
    excludeSenses: string[] = []
  ): VocabularySense[] {
    const excludeSet = new Set(excludeSenses)
    
    // If bandIndex exists, use it
    if (this.data.bandIndex?.[String(band)]) {
      const bandSenses = this.data.bandIndex[String(band)]
      const available = bandSenses.filter(sid => !excludeSet.has(sid))
      const shuffled = [...available].sort(() => Math.random() - 0.5)
      const selected = shuffled.slice(0, count)
      return selected
        .map(sid => this.data.senses?.[sid])
        .filter((s): s is VocabularySense => s !== undefined)
    }
    
    // Fallback: get random senses from all senses
    const allSenseIds = Object.keys(this.data.senses || {})
    const available = allSenseIds.filter(sid => !excludeSet.has(sid))
    const shuffled = [...available].sort(() => Math.random() - 0.5)
    const selected = shuffled.slice(0, count)
    
    return selected
      .map(sid => this.data.senses?.[sid])
      .filter((s): s is VocabularySense => s !== undefined)
  }

  /**
   * Get starter pack of blocks
   * Uses bandIndex if available, otherwise random selection
   */
  getStarterPack(limit: number = 50): Block[] {
    const allBlocks: Block[] = []
    
    // If bandIndex exists, use it for distribution
    if (this.data.bandIndex && Object.keys(this.data.bandIndex).length > 0) {
      const bandsConfig: [number, number][] = [
        [1000, 10],
        [2000, 10],
        [3000, 15],
        [4000, 15],
      ]

      for (const [band, count] of bandsConfig) {
        const senses = this.getRandomSensesInBand(band, count)
        for (const sense of senses) {
          allBlocks.push(this.senseToBlock(sense))
        }
      }
    } else {
      // Fallback: get random senses from all available
      const senses = this.getRandomSensesInBand(0, limit)
      for (const sense of senses) {
        allBlocks.push(this.senseToBlock(sense))
      }
    }

    // Shuffle and limit
    return allBlocks
      .sort(() => Math.random() - 0.5)
      .slice(0, limit)
  }

  /**
   * Get related sense IDs
   */
  getRelatedSenses(senseId: string): string[] {
    // Try relationships map first
    if (this.data.relationships?.[senseId]?.related) {
      return this.data.relationships[senseId].related
    }
    // Fallback to sense.connections
    const sense = this.data.senses?.[senseId] as any
    return sense?.connections?.related || []
  }

  /**
   * Get opposite sense IDs
   */
  getOppositeSenses(senseId: string): string[] {
    // Try relationships map first
    if (this.data.relationships?.[senseId]?.opposite) {
      return this.data.relationships[senseId].opposite
    }
    // Fallback to sense.connections
    const sense = this.data.senses?.[senseId] as any
    return sense?.connections?.opposite || []
  }

  /**
   * Get all connections for a sense
   */
  getConnections(senseId: string): BlockConnection[] {
    const connections: BlockConnection[] = []

    // Related senses
    for (const relatedId of this.getRelatedSenses(senseId)) {
      const sense = this.getSense(relatedId)
      if (sense) {
        connections.push({
          sense_id: relatedId,
          word: sense.word,
          type: 'RELATED_TO',
        })
      }
    }

    // Opposite senses
    for (const oppositeId of this.getOppositeSenses(senseId)) {
      const sense = this.getSense(oppositeId)
      if (sense) {
        connections.push({
          sense_id: oppositeId,
          word: sense.word,
          type: 'OPPOSITE_TO',
        })
      }
    }

    return connections
  }

  /**
   * Get full block detail with connections
   */
  getBlockDetail(senseId: string): BlockDetail | null {
    const sense = this.getSense(senseId)
    if (!sense) return null

    const connections = this.getConnections(senseId)

    // Build definition with explanation
    let definitionZh = sense.definition_zh || ''
    if (sense.definition_zh_explanation) {
      definitionZh = `${definitionZh} ${sense.definition_zh_explanation}`.trim()
    }

    let exampleZh = sense.example_zh || ''
    if (sense.example_zh_explanation) {
      exampleZh = `${exampleZh} ${sense.example_zh_explanation}`.trim()
    }

    // Get other senses of the same word
    const otherSenses = this.getSensesForWord(sense.word)
      .filter(s => s.id !== senseId)
      .map(s => ({
        sense_id: s.id,
        word: s.word,
        pos: s.pos,
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
      ((sense.connections?.related?.length || 0) + (sense.connections?.opposite?.length || 0))
    const baseXp = sense.value?.base_xp || 100
    const totalValue = sense.value?.total_xp || (baseXp + connectionCount * 10)
    
    return {
      sense_id: id,
      word: sense.word,
      definition_preview: (sense.definition_en || sense.definition_zh || '').slice(0, 100),
      tier: sense.tier || 1,
      base_xp: baseXp,
      connection_count: connectionCount,
      total_value: totalValue,
      status: 'raw', // Will be enriched with user progress
      rank: sense.frequency_rank ?? undefined,
    }
  }

  /**
   * Get random traps/distractors for MCQ/survey
   */
  getRandomTraps(
    excludeWord: string,
    count: number = 3,
    nearRank?: number
  ): VocabularySense[] {
    const candidates: VocabularySense[] = []

    if (nearRank) {
      // Get senses from nearby bands
      const searchRadius = 500
      for (const [bandStr, senseIds] of Object.entries(this.data.bandIndex || {})) {
        const band = parseInt(bandStr)
        const bandMin = band - 999
        const bandMax = band
        if (nearRank - searchRadius <= bandMax && nearRank + searchRadius >= bandMin) {
          for (const sid of senseIds) {
            const sense = this.data.senses?.[sid]
            if (sense && sense.word !== excludeWord) {
              candidates.push(sense)
            }
          }
        }
      }
    } else {
      // Get any random senses
      for (const sense of Object.values(this.data.senses || {})) {
        if (sense.word !== excludeWord) {
          candidates.push(sense)
        }
      }
    }

    // Random sample
    const shuffled = [...candidates].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, count)
  }

  /**
   * Search senses by frequency rank range
   */
  searchByRank(minRank: number, maxRank: number, limit: number = 10): VocabularySense[] {
    const results: VocabularySense[] = []

    for (const sense of Object.values(this.data.senses || {})) {
      const rank = sense.frequency_rank
      if (rank && rank >= minRank && rank <= maxRank) {
        results.push(sense)
        if (results.length >= limit) break
      }
    }

    return results
  }

  /**
   * Search senses by query string
   * Searches word, definitions (EN/ZH), and returns with relevance scores
   */
  searchSenses(
    query: string,
    options: {
      limit?: number
      cefrFilter?: string[]
      sortBy?: 'relevance' | 'cefr' | 'connections' | 'rank'
    } = {}
  ): Array<VocabularySense & { score: number; connection_count: number }> {
    const { limit = 50, cefrFilter, sortBy = 'relevance' } = options
    const normalizedQuery = query.toLowerCase().trim()
    const results: Array<VocabularySense & { score: number; connection_count: number }> = []

    for (const [senseId, sense] of Object.entries(this.data.senses || {})) {
      // Apply CEFR filter if specified
      if (cefrFilter && cefrFilter.length > 0 && !cefrFilter.includes(sense.cefr || '')) {
        continue
      }

      const word = sense.word?.toLowerCase() || ''
      const defEn = (sense.definition_en || sense.definition || '').toLowerCase()
      const defZh = sense.definition_zh || ''

      // Calculate relevance score
      let score = 0

      if (normalizedQuery === '') {
        // Empty query = browsing mode, give base score
        score = 50
      } else {
        // Exact word match = highest score
        if (word === normalizedQuery) {
          score = 100
        }
        // Word starts with query
        else if (word.startsWith(normalizedQuery)) {
          score = 80
        }
        // Word contains query
        else if (word.includes(normalizedQuery)) {
          score = 60
        }
        // Definition contains query (English)
        else if (defEn.includes(normalizedQuery)) {
          score = 40
        }
        // Definition contains query (Chinese)
        else if (defZh.includes(normalizedQuery)) {
          score = 30
        }
      }

      if (score > 0) {
        const connections = this.getConnections(senseId)
        results.push({
          ...sense,
          id: senseId,
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
   * Get hop connections for a sense (multi-hop network)
   * Returns words that are 1, 2, or more hops away
   */
  getHopConnections(senseId: string, maxHops: number = 2): {
    hop1: string[]
    hop2: string[]
    totalNetwork: number
  } {
    const hop1 = new Set<string>()
    const hop2 = new Set<string>()
    const visited = new Set<string>([senseId])

    // Get direct connections (hop 1)
    const directConnections = this.getConnections(senseId)
    for (const conn of directConnections) {
      hop1.add(conn.sense_id)
      visited.add(conn.sense_id)
    }

    // Get second-degree connections (hop 2)
    if (maxHops >= 2) {
      for (const firstHopId of hop1) {
        const secondConnections = this.getConnections(firstHopId)
        for (const conn of secondConnections) {
          if (!visited.has(conn.sense_id)) {
            hop2.add(conn.sense_id)
            visited.add(conn.sense_id)
          }
        }
      }
    }

    return {
      hop1: Array.from(hop1),
      hop2: Array.from(hop2),
      totalNetwork: hop1.size + hop2.size,
    }
  }

  /**
   * Calculate network value for a sense
   * Based on connections and their connections
   */
  calculateNetworkValue(senseId: string): {
    directValue: number
    networkValue: number
    networkMultiplier: number
  } {
    const sense = this.getSense(senseId)
    const baseXp = sense?.value?.base_xp || 100
    const hops = this.getHopConnections(senseId)
    
    // Direct connections add 10 XP each
    const directValue = baseXp + (hops.hop1.length * 10)
    
    // Network value includes 2nd-degree connections (5 XP each)
    const networkBonus = hops.hop2.length * 5
    const networkValue = directValue + networkBonus
    
    // Multiplier for display
    const networkMultiplier = networkValue / baseXp

    return {
      directValue,
      networkValue,
      networkMultiplier: Math.round(networkMultiplier * 10) / 10,
    }
  }

  /**
   * Get graph data for visualization
   */
  getGraphData(): GraphData | null {
    // Try to use pre-computed graph_data
    if (this.data.graph_data) {
      return this.data.graph_data
    }

    // Fallback: build from senses and relationships
    const nodes: GraphNode[] = []
    const edges: GraphEdge[] = []
    const edgeSet = new Set<string>()

    for (const [senseId, sense] of Object.entries(this.data.senses || {})) {
      // Add node
      const senseData = sense as any
      nodes.push({
        id: senseId,
        word: senseData.word || '',
        pos: senseData.pos || '',
        value: senseData.value?.total_xp || 100,
        tier: senseData.tier || 1,
        definition_en: (senseData.definition_en || '').slice(0, 100),
        definition_zh: (senseData.definition_zh || '').slice(0, 50),
      })

      // Add edges from relationships or connections
      const rels = this.data.relationships?.[senseId] || senseData.connections || {}
      
      for (const relatedId of (rels.related || [])) {
        const edgeKey = [senseId, relatedId].sort().join('-')
        if (!edgeSet.has(edgeKey)) {
          edgeSet.add(edgeKey)
          edges.push({ source: senseId, target: relatedId, type: 'related' })
        }
      }
      
      for (const oppositeId of (rels.opposite || [])) {
        const edgeKey = [senseId, oppositeId].sort().join('-')
        if (!edgeSet.has(edgeKey)) {
          edgeSet.add(edgeKey)
          edges.push({ source: senseId, target: oppositeId, type: 'opposite' })
        }
      }
    }

    return { nodes, edges }
  }

  /**
   * Get all sense IDs
   */
  getAllSenseIds(): string[] {
    return Object.keys(this.data.senses || {})
  }
}

// Export singleton instance
export const vocabulary = new VocabularyStore()

// Export types for external use
export type { VocabularySense, VocabularyWord, VocabularyData, GraphData, GraphNode, GraphEdge }

