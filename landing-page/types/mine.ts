/**
 * Mine Types
 * 
 * Type definitions for The Mine (vocabulary universe) exploration.
 */

export interface BlockConnection {
  sense_id: string
  word: string
  type: string
  status?: 'raw' | 'hollow' | 'solid'
}

export interface Block {
  sense_id: string
  word: string
  definition_preview: string
  rank: number  // Renamed from tier to rank (word complexity 1-7)
  base_xp: number
  connection_count: number
  total_value: number
  status: 'raw' | 'hollow' | 'solid'
  source?: string
  emoji?: string  // For emoji pack vocabulary
  translation?: string  // Optional translation (can be toggled off for immersion)
  category?: string  // Optional category/classification
  difficulty?: number  // Optional difficulty level (1-3 for star ratings)
}

export interface OtherSense {
  sense_id: string
  word: string
  pos?: string
  definition_preview: string
}

export interface BlockDetail {
  sense_id: string
  word: string
  pos?: string  // Part of speech (n, v, adj, adv, etc.)
  rank: number  // Renamed from tier to rank (word complexity 1-7)
  base_xp: number
  connection_count: number
  total_value: number
  definition_en?: string
  definition_zh?: string
  example_en?: string
  example_zh?: string
  connections: BlockConnection[]
  other_senses?: OtherSense[]  // Other meanings of the same word
  user_progress?: {
    status?: string
    rank?: number  // Renamed from tier to rank
    started_at?: string
    mastery_level?: string
  }
}

export interface UserStats {
  total_discovered: number
  solid_count: number
  hollow_count: number
  raw_count: number
}

export interface MineExploreResponse {
  mode: 'starter' | 'personalized'
  blocks: Block[]
  user_stats: UserStats
  gaps_count?: number
  prerequisites_count?: number
}

export interface StartForgingResponse {
  success: boolean
  learning_progress_id: number
  sense_id: string
  status: string
  message: string
}

