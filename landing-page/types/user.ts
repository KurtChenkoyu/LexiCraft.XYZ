/**
 * User and Child Types
 * 
 * Shared types for user management across the application.
 */

export interface Child {
  id: string
  name: string | null
  age: number | null
  grade?: string | null
  created_at?: string
}

export interface UserBalance {
  available_points: number
  locked_points: number
  total_earned?: number
  withdrawn_points?: number
}

export interface UserProfile {
  id: string
  email: string
  name?: string
  role?: 'parent' | 'learner' | 'admin'
  created_at?: string
}

