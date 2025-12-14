/**
 * Progress API Service
 * 
 * Handles user progress data (separate from vocabulary data).
 * Vocabulary data comes from local store, progress comes from server.
 */

import { authenticatedGet, authenticatedPost } from '@/lib/api-client'

/**
 * User learning progress for a single block
 */
export interface BlockProgress {
  sense_id: string
  status: 'raw' | 'hollow' | 'solid' | 'learning' | 'pending' | 'verified' | 'mastered'
  tier?: number
  started_at?: string
  mastery_level?: string
}

/**
 * User statistics from the server
 */
export interface UserProgressStats {
  total_discovered: number
  solid_count: number
  hollow_count: number
  raw_count: number
}

/**
 * Response from the progress endpoint
 */
export interface UserProgressResponse {
  progress: BlockProgress[]
  stats: UserProgressStats
}

/**
 * Start forging response (with Delta Strategy fields)
 */
export interface StartForgingResponse {
  success: boolean
  learning_progress_id: number
  sense_id: string
  status: string
  message: string
  // Delta Strategy fields (instant UI update)
  delta_xp?: number
  delta_sparks?: number
  delta_discovered?: number
  delta_hollow?: number
}

/**
 * Progress API Client
 */
export const progressApi = {
  /**
   * Get user's learning progress for all blocks
   */
  getUserProgress: async (): Promise<UserProgressResponse> => {
    try {
      return await authenticatedGet<UserProgressResponse>('/api/v1/mine/progress')
    } catch (error) {
      // Return empty progress on error (new user or server issue)
      console.error('Failed to fetch progress:', error)
      return {
        progress: [],
        stats: {
          total_discovered: 0,
          solid_count: 0,
          hollow_count: 0,
          raw_count: 0,
        }
      }
    }
  },

  /**
   * Get progress for a specific block
   */
  getBlockProgress: async (senseId: string): Promise<BlockProgress | null> => {
    try {
      return await authenticatedGet<BlockProgress>(`/api/v1/mine/progress/${senseId}`)
    } catch (error) {
      console.error('Failed to fetch block progress:', error)
      return null
    }
  },

  /**
   * Start forging a block (begin learning process)
   */
  startForging: async (senseId: string): Promise<StartForgingResponse> => {
    return authenticatedPost<StartForgingResponse>(
      `/api/v1/mine/blocks/${senseId}/start`
    )
  },
}

