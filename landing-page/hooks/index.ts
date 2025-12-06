/**
 * Custom Hooks
 * 
 * Central export point for all custom React hooks.
 */

// Re-export hooks from contexts for convenience
export { useAuth } from '@/contexts/AuthContext'
export { useUserData } from '@/contexts/UserDataContext'

// Feature-specific hooks
export { useNotifications } from './useNotifications'
export { useProfile } from './useProfile'
export { useGoals } from './useGoals'
export { useLeaderboard } from './useLeaderboard'

