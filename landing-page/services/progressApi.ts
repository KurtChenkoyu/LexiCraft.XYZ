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
   * 
   * @param learnerId Optional learner ID to fetch progress for a specific learner
   *                  (defaults to parent's own learner profile)
   */
  getUserProgress: async (learnerId?: string): Promise<UserProgressResponse> => {
    try {
      const url = learnerId 
        ? `/api/v1/mine/progress?learner_id=${learnerId}`
        : '/api/v1/mine/progress'
      
      return await authenticatedGet<UserProgressResponse>(url)
    } catch (error: any) {
      const status = error?.response?.status
      const requestUrl = error?.config?.url

      // Only log non-timeout, non-401 errors (401 is usually "not logged in" or bad env)
      if (
        status !== 401 &&
        error.code !== 'ECONNABORTED' &&
        !error.message?.includes('timeout')
      ) {
        console.error('Failed to fetch progress:', {
          status,
          url: requestUrl,
          detail: error?.response?.data || error.message,
        })
      } else if (status === 401 && process.env.NODE_ENV === 'development') {
        // Dev-only hint for auth / env misconfigurations
        console.warn(
          '⚠️ progressApi.getUserProgress unauthorized (401). Check Supabase session and NEXT_PUBLIC_API_URL / SUPABASE_JWT_SECRET.',
          { url: requestUrl },
        )
      }

      // Return empty progress on error (new user, auth issue, or server problem)
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
  startForging: async (senseId: string, learnerId?: string): Promise<StartForgingResponse> => {
    const body = learnerId ? { learner_id: learnerId } : {}
    
    // DEBUG: Log request details
    if (process.env.NODE_ENV === 'development') {
      console.log('[progressApi.startForging] Sending request:', {
        senseId,
        learnerId,
        body,
        hasLearnerId: !!learnerId,
      })
    }
    
    return authenticatedPost<StartForgingResponse>(
      `/api/v1/mine/blocks/${senseId}/start`,
      body,
    )
  },

  /**
   * Get verification schedule info for a sense_id
   * Used to submit verification results with SRS integration
   * 
   * @param senseId The learning point ID (sense_id)
   * @param learnerId Optional learner ID to fetch schedules for a specific learner
   * @returns Object with learning_progress_id and verification_schedule_id if found, null otherwise
   */
  getVerificationScheduleInfo: async (senseId: string, learnerId?: string): Promise<{ learning_progress_id: number, verification_schedule_id: number } | null> => {
    try {
      const url = learnerId 
        ? `/api/v1/verification/due?limit=100&learner_id=${learnerId}`
        : '/api/v1/verification/due?limit=100'
      
      const dueCards = await authenticatedGet<Array<{
        verification_schedule_id: number
        learning_progress_id: number
        learning_point_id: string
        word: string | null
        scheduled_date: string
        days_overdue: number
        mastery_level: string
        retention_predicted: number | null
      }>>(url)
      
      // Find the card matching this sense_id
      const matchingCard = dueCards.find(card => card.learning_point_id === senseId)
      if (!matchingCard) return null
      
      return {
        learning_progress_id: matchingCard.learning_progress_id,
        verification_schedule_id: matchingCard.verification_schedule_id
      }
    } catch (error) {
      console.warn(`Failed to get verification schedule info for ${senseId}:`, error)
      return null
    }
  },
}

