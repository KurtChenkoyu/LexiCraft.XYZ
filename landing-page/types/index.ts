/**
 * Shared Types
 * 
 * Central export point for all shared TypeScript types.
 * Feature-specific types remain in their respective service files.
 */

// User types
export * from './user'

// API types
export * from './api'

// Re-export commonly used types from services for convenience
export type {
  // Gamification
  LevelInfo,
  Achievement,
  StreakInfo,
  LearnerGamificationProfile,
  Goal,
  LeaderboardEntry,
  Notification,
} from '@/services/gamificationApi'

export type {
  // MCQ
  MCQData,
  MCQResult,
} from '@/services/mcqApi'

export type {
  // Survey
  SurveyResult,
  QuestionPayload,
  AnswerSubmission,
} from '@/services/surveyApi'

