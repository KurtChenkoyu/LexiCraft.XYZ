/**
 * Words API Service
 * 
 * Handles word learning actions with One-Shot Payload pattern.
 * All responses include complete gamification data for instant feedback.
 */

import { authenticatedPost } from '@/lib/api-client'

// Gamification types (shared with MCQ - consider extracting to shared types)
export interface LevelUnlock {
  code: string
  type: string
  name_en: string
  name_zh?: string
  description_en?: string
  description_zh?: string
  icon?: string
  unlocked_at_level?: number
}

export interface LevelUpInfo {
  old_level: number
  new_level: number
  rewards?: string[]
  new_unlocks?: LevelUnlock[]
}

export interface AchievementUnlockedInfo {
  id: string
  code: string
  name_en: string
  name_zh?: string
  description_en?: string
  description_zh?: string
  icon?: string
  xp_reward: number
  crystal_reward?: number
  points_bonus: number
}

export interface GamificationResult {
  xp_gained: number
  total_xp: number
  current_level: number
  xp_to_next_level: number
  xp_in_current_level: number
  progress_percentage: number
  streak_extended: boolean
  streak_days: number
  streak_multiplier?: number
  level_up: LevelUpInfo | null
  achievements_unlocked: AchievementUnlockedInfo[]
}

export interface StartVerificationResponse {
  success: boolean
  learning_progress_id: number
  verification_schedule_id: number
  learning_point_id: string
  status: string
  scheduled_date: string
  algorithm_type: string
  mastery_level: string
  message: string
  // One-Shot Payload: gamification data included in response
  gamification: GamificationResult | null
}

export interface StartVerificationRequest {
  learning_point_id: string
  tier: number  // Parameter name kept as tier for API compatibility, but represents word rank
  initial_difficulty?: number
}

/**
 * Start verification for a word (learn a new word)
 * 
 * Returns complete gamification data for instant feedback:
 * - XP gained (with streak multiplier)
 * - Level up info (if occurred)
 * - Achievements unlocked (if any)
 * - Streak status
 */
export async function startVerification(
  senseId: string,
  tier: number,
  initialDifficulty: number = 0.5
): Promise<StartVerificationResponse> {
  return authenticatedPost<StartVerificationResponse>(
    '/api/v1/words/start-verification',
    {
      learning_point_id: senseId,
      tier,
      initial_difficulty: initialDifficulty,
    }
  )
}

// Export as object for consistent API pattern
export const wordsApi = {
  startVerification,
}

