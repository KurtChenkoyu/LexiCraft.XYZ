/**
 * React Query Client Configuration
 * 
 * Centralized configuration for server state management.
 */

import { QueryClient } from '@tanstack/react-query'

/**
 * Create and configure QueryClient
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data considered fresh for 5 minutes
      staleTime: 5 * 60 * 1000,
      
      // Cache data for 30 minutes
      gcTime: 30 * 60 * 1000, // previously cacheTime
      
      // Don't refetch on window focus (we use local store)
      refetchOnWindowFocus: false,
      
      // Retry failed requests 3 times
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      // Retry mutations once
      retry: 1,
    },
  },
})

/**
 * Query keys for type-safe cache invalidation
 */
export const queryKeys = {
  // User progress
  userProgress: ['userProgress'] as const,
  blockProgress: (senseId: string) => ['blockProgress', senseId] as const,
  
  // Survey
  surveySession: (sessionId: string) => ['survey', sessionId] as const,
  surveyHistory: ['surveyHistory'] as const,
  
  // Profile
  profile: ['profile'] as const,
  achievements: ['achievements'] as const,
  
  // Leaderboard
  leaderboard: (type: string) => ['leaderboard', type] as const,
}

