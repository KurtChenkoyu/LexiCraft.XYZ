/**
 * Gamification API Service
 * 
 * Provides type-safe methods for learner profile, achievements, goals,
 * leaderboards, and notifications endpoints.
 */

import {
  authenticatedGet,
  authenticatedPost,
  authenticatedPut,
  authenticatedDelete,
} from '@/lib/api-client'

// ============================================
// Types
// ============================================

export interface LevelInfo {
  level: number
  total_xp: number
  xp_to_next_level: number
  xp_in_current_level: number
  progress_percentage: number
}

export interface Achievement {
  id: string
  code: string
  name_en: string
  name_zh: string | null
  description_en: string | null
  description_zh: string | null
  icon: string | null
  category: string
  tier: string
  requirement_type?: string
  requirement_value?: number
  xp_reward?: number
  crystal_reward?: number
  points_bonus?: number
  unlocked: boolean
  unlocked_at: string | null
  progress: number
  progress_percentage?: number
}

export interface StreakInfo {
  current_streak: number
  longest_streak: number
  streak_at_risk: boolean
  days_until_risk: number | null
}

export interface LearnerProfile {
  user_id: string
  level: LevelInfo
  vocabulary_size: number
  current_streak: number
  words_learned_this_week: number
  words_learned_this_month: number
  recent_achievements: Achievement[]
  total_achievements: number
  unlocked_achievements: number
}

export interface Goal {
  id: string
  goal_type: string
  target_value: number
  current_value: number
  start_date: string | null
  end_date: string | null
  status: string
  created_at: string | null
  completed_at: string | null
  progress_percentage: number
}

export interface GoalSuggestion {
  goal_type: string
  target_value: number
  end_date: string
  reason: string
}

export interface CreateGoalRequest {
  goal_type: string
  target_value: number
  end_date: string
}

export interface LeaderboardEntry {
  rank: number
  user_id: string
  name: string
  email: string | null
  score: number
  longest_streak: number
  current_streak: number
  is_me?: boolean
}

export interface UserRank {
  rank: number
  user_id: string
  score: number
  period: string
  metric: string
}

export interface Notification {
  id: string
  type: string
  title_en: string
  title_zh: string | null
  message_en: string | null
  message_zh: string | null
  data: Record<string, any>
  read: boolean
  created_at: string
}

export interface CoachDashboard {
  learner_id: string
  overview: {
    level: number
    total_xp: number
    vocabulary_size: number
    current_streak: number
    unlocked_achievements: number
    total_achievements: number
  }
  vocabulary: {
    vocabulary_size: number
    frequency_bands: Record<string, number>
    growth_rate_per_week: number
    growth_timeline: Array<{ date: string; vocabulary_size: number; words_learned: number }>
  }
  activity: {
    words_learned_this_week: number
    words_learned_this_month: number
    activity_streak_days: number
    learning_rate_per_week: number
    last_active_date: string | null
  }
  performance: {
    total_reviews: number
    retention_rate: number
    avg_response_time_ms: number
    total_correct: number
  }
  trends: Array<{
    date: string
    words_learned: number
    vocabulary_size: number
    reviews_completed: number
  }>
  insights: Array<{
    type: string
    title: string
    message: string
    priority: string
    data?: Record<string, any>
  }>
  peer_comparison: Array<{
    metric: string
    learner_value: number
    peer_average: number
    peer_percentile: number
  }>
  goals: Goal[]
  achievements: {
    total: number
    unlocked: number
    recent: Achievement[]
  }
}

export interface DashboardResponse {
  learner_profile: Record<string, any>
  vocabulary: {
    vocabulary_size: number
    frequency_bands: Record<string, number>
    growth_rate_per_week: number
  }
  activity: {
    words_learned_this_week: number
    words_learned_this_month: number
    activity_streak_days: number
    learning_rate_per_week: number
    last_active_date: string | null
  }
  performance: {
    algorithm: string
    total_reviews: number
    total_correct: number
    retention_rate: number
    cards_learning: number
    cards_familiar: number
    cards_known: number
    cards_mastered: number
    cards_leech: number
    avg_interval_days: number
    reviews_today: number
  }
  points: {
    total_earned: number
    available_points: number
    locked_points: number
    withdrawn_points: number
  }
  gamification: {
    level: number
    total_xp: number
    xp_to_next_level: number
    xp_in_current_level: number
    progress_percentage: number
    unlocked_achievements: number
    total_achievements: number
    recent_achievements: Achievement[]
  }
}

// ============================================
// Learner Profile API
// ============================================

export const learnerProfileApi = {
  /**
   * Get complete learner profile (gamified view)
   */
  getProfile: async (): Promise<LearnerProfile> => {
    return authenticatedGet<LearnerProfile>('/api/v1/profile/learner')
  },

  /**
   * Get all achievements with progress
   */
  getAchievements: async (): Promise<Achievement[]> => {
    return authenticatedGet<Achievement[]>('/api/v1/profile/learner/achievements')
  },

  /**
   * Get level and XP information
   */
  getLevelInfo: async (): Promise<LevelInfo> => {
    return authenticatedGet<LevelInfo>('/api/v1/profile/learner/level')
  },

  /**
   * Get streak information
   */
  getStreaks: async (): Promise<StreakInfo> => {
    return authenticatedGet<StreakInfo>('/api/v1/profile/learner/streaks')
  },

  /**
   * Check and unlock achievements
   */
  checkAchievements: async (): Promise<{ newly_unlocked: Achievement[]; count: number }> => {
    return authenticatedPost('/api/v1/profile/learner/check-achievements')
  },
}

// ============================================
// Goals API
// ============================================

export const goalsApi = {
  /**
   * Get all goals
   */
  getGoals: async (): Promise<Goal[]> => {
    return authenticatedGet<Goal[]>('/api/v1/goals')
  },

  /**
   * Create a new goal
   */
  createGoal: async (goal: CreateGoalRequest): Promise<Goal> => {
    return authenticatedPost<Goal>('/api/v1/goals', goal)
  },

  /**
   * Update a goal
   */
  updateGoal: async (goalId: string, goal: CreateGoalRequest): Promise<Goal> => {
    return authenticatedPut<Goal>(`/api/v1/goals/${goalId}`, goal)
  },

  /**
   * Delete a goal
   */
  deleteGoal: async (goalId: string): Promise<{ message: string }> => {
    return authenticatedDelete(`/api/v1/goals/${goalId}`)
  },

  /**
   * Get goal suggestions
   */
  getSuggestions: async (): Promise<GoalSuggestion[]> => {
    return authenticatedGet<GoalSuggestion[]>('/api/v1/goals/suggestions')
  },

  /**
   * Complete a goal manually
   */
  completeGoal: async (goalId: string): Promise<Goal> => {
    return authenticatedPost<Goal>(`/api/v1/goals/${goalId}/complete`)
  },
}

// ============================================
// Leaderboards API
// ============================================

export const leaderboardsApi = {
  /**
   * Get global leaderboard
   * Returns empty array if API fails (table may not exist yet)
   */
  getGlobal: async (
    period: 'weekly' | 'monthly' | 'all_time' = 'weekly',
    limit: number = 50,
    metric: 'xp' | 'words' | 'streak' = 'xp'
  ): Promise<LeaderboardEntry[]> => {
    try {
      return await authenticatedGet<LeaderboardEntry[]>(
        `/api/v1/leaderboards/global?period=${period}&limit=${limit}&metric=${metric}`
      )
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Leaderboard API unavailable:', error)
      }
      return [] // Return empty - UI will show "暫無排行資料"
    }
  },

  /**
   * Get friends leaderboard
   * Returns empty array if API fails
   */
  getFriends: async (
    period: 'weekly' | 'monthly' | 'all_time' = 'weekly',
    metric: 'xp' | 'words' | 'streak' = 'xp'
  ): Promise<LeaderboardEntry[]> => {
    try {
      return await authenticatedGet<LeaderboardEntry[]>(
        `/api/v1/leaderboards/friends?period=${period}&metric=${metric}`
      )
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Friends leaderboard API unavailable:', error)
      }
      return []
    }
  },

  /**
   * Get user's rank
   * Returns null if API fails
   */
  getRank: async (
    period: 'weekly' | 'monthly' | 'all_time' = 'weekly',
    metric: 'xp' | 'words' | 'streak' = 'xp'
  ): Promise<UserRank | null> => {
    try {
      return await authenticatedGet<UserRank>(
        `/api/v1/leaderboards/rank?period=${period}&metric=${metric}`
      )
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('User rank API unavailable:', error)
      }
      return null
    }
  },

  /**
   * Add a connection (friend or classmate)
   */
  addConnection: async (
    connectedUserId: string,
    connectionType: 'friend' | 'classmate' = 'friend'
  ): Promise<{ message: string }> => {
    return authenticatedPost(
      `/api/v1/leaderboards/connections/${connectedUserId}?connection_type=${connectionType}`
    )
  },

  /**
   * Get connections
   */
  getConnections: async (): Promise<Array<{
    user_id: string
    connection_type: string
    name: string
    email: string | null
  }>> => {
    return authenticatedGet('/api/v1/leaderboards/connections')
  },
}

// ============================================
// Notifications API
// ============================================

export const notificationsApi = {
  /**
   * Get notifications
   */
  getNotifications: async (
    unreadOnly: boolean = false,
    limit: number = 50
  ): Promise<Notification[]> => {
    return authenticatedGet<Notification[]>(
      `/api/v1/notifications?unread_only=${unreadOnly}&limit=${limit}`
    )
  },

  /**
   * Mark notifications as read
   */
  markAsRead: async (notificationIds: string[]): Promise<{ message: string; count: number }> => {
    return authenticatedPost('/api/v1/notifications/read', { notification_ids: notificationIds })
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async (): Promise<{ message: string; count: number }> => {
    return authenticatedPost('/api/v1/notifications/read-all')
  },

  /**
   * Get unread count
   */
  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    return authenticatedGet('/api/v1/notifications/unread-count')
  },

  /**
   * Check streak risk
   */
  checkStreakRisk: async (): Promise<{ message: string; notification: Notification | null }> => {
    return authenticatedPost('/api/v1/notifications/check-streak-risk')
  },

  /**
   * Check milestones
   */
  checkMilestones: async (): Promise<{
    message: string
    count: number
    notifications: Notification[]
  }> => {
    return authenticatedPost('/api/v1/notifications/check-milestones')
  },
}

// ============================================
// Coach/Parent Profile API
// ============================================

export const coachProfileApi = {
  /**
   * Get coach dashboard for a learner
   */
  getDashboard: async (learnerId: string): Promise<CoachDashboard> => {
    return authenticatedGet<CoachDashboard>(`/api/v1/profile/coach/${learnerId}`)
  },

  /**
   * Get detailed analytics
   */
  getAnalytics: async (learnerId: string): Promise<{
    vocabulary_growth: {
      timeline: Array<{ date: string; vocabulary_size: number; words_learned: number }>
      current_size: number
      growth_rate: number
    }
    weekly_activity: Array<{ week_start: string; week_end: string; words_learned: number }>
    xp_earnings: {
      history: Array<{ xp_amount: number; source: string; earned_at: string }>
      summary: { total_xp: number; total_earnings: number; by_source: Record<string, any> }
    }
  }> => {
    return authenticatedGet(`/api/v1/profile/coach/${learnerId}/analytics`)
  },

  /**
   * Get insights
   */
  getInsights: async (learnerId: string): Promise<{
    insights: Array<{
      type: string
      title: string
      message: string
      priority: string
      data?: Record<string, any>
    }>
    generated_at: string
  }> => {
    return authenticatedGet(`/api/v1/profile/coach/${learnerId}/insights`)
  },

  /**
   * Get peer comparison
   */
  getPeerComparison: async (learnerId: string): Promise<{
    comparisons: Array<{
      metric: string
      learner_value: number
      peer_average: number
      peer_percentile: number
    }>
    note: string
  }> => {
    return authenticatedGet(`/api/v1/profile/coach/${learnerId}/compare`)
  },
}

// ============================================
// Dashboard API (enhanced)
// ============================================

export const dashboardApi = {
  /**
   * Get complete dashboard with gamification
   */
  getDashboard: async (): Promise<DashboardResponse> => {
    return authenticatedGet<DashboardResponse>('/api/v1/dashboard')
  },
}


