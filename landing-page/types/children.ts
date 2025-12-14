/**
 * Child-related types for parent-learner features
 */

export interface ChildSummary {
  id: string
  name: string | null
  age: number | null
  email: string
  // Summary stats
  level: number
  total_xp: number
  current_streak: number
  vocabulary_size: number
  words_learned_this_week: number
  last_active_date: string | null
}

