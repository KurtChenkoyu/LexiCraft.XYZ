'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUserData } from '@/contexts/UserDataContext'

const STORAGE_KEY = 'lexicraft_preferred_role'

type UserRole = 'learner' | 'parent' | 'coach' | 'admin'

interface RolePreference {
  /** Currently active role for the user */
  currentRole: UserRole
  /** Set the preferred role (persists to localStorage) */
  setRole: (role: UserRole) => void
  /** Check if user has parent role */
  isParent: boolean
  /** Check if user has learner role */
  isLearner: boolean
  /** Check if user has coach role */
  isCoach: boolean
  /** All roles the user has */
  roles: UserRole[]
  /** Whether the user has multiple roles and can switch */
  canSwitchRoles: boolean
}

/**
 * Hook for managing user role preference
 * 
 * - Stores the last-used role in localStorage
 * - Defaults to 'learner' if no preference is set
 * - Provides role checking utilities
 */
export function useRolePreference(): RolePreference {
  const { profile } = useUserData()
  const [currentRole, setCurrentRole] = useState<UserRole>('learner')

  // Get user's roles from profile
  const roles = (profile?.roles || ['learner']) as UserRole[]
  const isParent = roles.includes('parent')
  const isLearner = roles.includes('learner')
  const isCoach = roles.includes('coach')
  const canSwitchRoles = roles.length > 1

  // Load preference from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    const savedRole = localStorage.getItem(STORAGE_KEY) as UserRole | null
    
    if (savedRole && roles.includes(savedRole)) {
      // Use saved preference if valid
      setCurrentRole(savedRole)
    } else if (roles.length > 0) {
      // Default to first role (usually 'learner')
      setCurrentRole(roles[0])
    }
  }, [roles])

  // Save preference to localStorage
  const setRole = useCallback((role: UserRole) => {
    if (!roles.includes(role)) {
      console.warn(`User does not have role: ${role}`)
      return
    }

    setCurrentRole(role)
    
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, role)
    }
  }, [roles])

  return {
    currentRole,
    setRole,
    isParent,
    isLearner,
    isCoach,
    roles,
    canSwitchRoles,
  }
}

export default useRolePreference

