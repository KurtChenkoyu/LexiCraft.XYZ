'use client'

import { useState, useEffect, useCallback } from 'react'
import { leaderboardsApi, LeaderboardEntry, UserRank } from '@/services/gamificationApi'
import { useAuth } from '@/contexts/AuthContext'

type Period = 'weekly' | 'monthly' | 'all_time'
type Metric = 'xp' | 'words' | 'streak'

interface UseLeaderboardReturn {
  globalLeaderboard: LeaderboardEntry[]
  friendsLeaderboard: LeaderboardEntry[]
  userRank: UserRank | null
  period: Period
  metric: Metric
  isLoading: boolean
  error: string | null
  setPeriod: (period: Period) => void
  setMetric: (metric: Metric) => void
  refresh: () => Promise<void>
}

export function useLeaderboard(): UseLeaderboardReturn {
  const { user } = useAuth()
  const [globalLeaderboard, setGlobalLeaderboard] = useState<LeaderboardEntry[]>([])
  const [friendsLeaderboard, setFriendsLeaderboard] = useState<LeaderboardEntry[]>([])
  const [userRank, setUserRank] = useState<UserRank | null>(null)
  const [period, setPeriod] = useState<Period>('weekly')
  const [metric, setMetric] = useState<Metric>('xp')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLeaderboards = useCallback(async () => {
    if (!user) {
      setGlobalLeaderboard([])
      setFriendsLeaderboard([])
      setUserRank(null)
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      const [global, friends, rank] = await Promise.all([
        leaderboardsApi.getGlobal(period, 50, metric),
        leaderboardsApi.getFriends(period, metric),
        leaderboardsApi.getRank(period, metric),
      ])

      setGlobalLeaderboard(global)
      setFriendsLeaderboard(friends)
      setUserRank(rank)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch leaderboards:', err)
      setError('無法載入排行榜')
    } finally {
      setIsLoading(false)
    }
  }, [user, period, metric])

  useEffect(() => {
    fetchLeaderboards()
  }, [fetchLeaderboards])

  return {
    globalLeaderboard,
    friendsLeaderboard,
    userRank,
    period,
    metric,
    isLoading,
    error,
    setPeriod,
    setMetric,
    refresh: fetchLeaderboards,
  }
}

