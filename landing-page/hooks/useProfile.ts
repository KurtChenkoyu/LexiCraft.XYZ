'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  learnerProfileApi,
  LearnerProfile,
  Achievement,
  StreakInfo,
} from '@/services/gamificationApi'
import { useAuth } from '@/contexts/AuthContext'

interface UseProfileReturn {
  profile: LearnerProfile | null
  achievements: Achievement[]
  streaks: StreakInfo | null
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useProfile(): UseProfileReturn {
  const { user } = useAuth()
  const [profile, setProfile] = useState<LearnerProfile | null>(null)
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [streaks, setStreaks] = useState<StreakInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProfile = useCallback(async () => {
    if (!user) {
      setProfile(null)
      setAchievements([])
      setStreaks(null)
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      const [profileData, achievementsData, streaksData] = await Promise.all([
        learnerProfileApi.getProfile(),
        learnerProfileApi.getAchievements(),
        learnerProfileApi.getStreaks(),
      ])

      setProfile(profileData)
      setAchievements(achievementsData)
      setStreaks(streaksData)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch profile:', err)
      setError('無法載入個人資料')
    } finally {
      setIsLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchProfile()
  }, [fetchProfile])

  return {
    profile,
    achievements,
    streaks,
    isLoading,
    error,
    refresh: fetchProfile,
  }
}

