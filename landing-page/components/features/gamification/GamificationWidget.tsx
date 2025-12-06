'use client'

import { useEffect, useState, useRef } from 'react'
import { Link } from '@/i18n/routing'
import { useAuth } from '@/contexts/AuthContext'
import { dashboardApi, DashboardResponse } from '@/services/gamificationApi'

export function GamificationWidget() {
  const { user } = useAuth()
  const userId = user?.id
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const hasFetched = useRef(false)

  useEffect(() => {
    const fetchData = async () => {
      if (!userId || hasFetched.current) return
      hasFetched.current = true

      try {
        const dashboardData = await dashboardApi.getDashboard()
        setData(dashboardData)
      } catch (err) {
        console.error('Failed to fetch gamification data:', err)
      } finally {
        setIsLoading(false)
      }
    }

    if (userId) {
      fetchData()
    }
  }, [userId])

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
        <div className="animate-pulse">
          <div className="h-6 bg-white/20 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-white/20 rounded w-2/3 mb-2"></div>
          <div className="h-4 bg-white/20 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (!data) return null

  const { gamification, activity } = data

  return (
    <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl shadow-lg p-6 text-white overflow-hidden relative">
      {/* Background decoration */}
      <div className="absolute -right-8 -top-8 w-32 h-32 bg-white/10 rounded-full"></div>
      <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-white/5 rounded-full"></div>

      <div className="relative">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold flex items-center gap-2">
            🎮 學習進度
          </h3>
          <Link
            href="/profile"
            className="text-sm text-white/80 hover:text-white transition-colors"
          >
            查看更多 →
          </Link>
        </div>

        {/* Level & XP */}
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-2xl font-black shadow-lg">
            {gamification.level}
          </div>
          <div className="flex-1">
            <div className="text-sm text-white/80 mb-1">
              Level {gamification.level} · {gamification.total_xp} XP
            </div>
            <div className="h-2 bg-white/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full transition-all"
                style={{ width: `${gamification.progress_percentage}%` }}
              ></div>
            </div>
            <div className="text-xs text-white/60 mt-1">
              {gamification.xp_in_current_level} / {gamification.xp_to_next_level} XP
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-xl font-bold">🔥 {activity.activity_streak_days}</div>
            <div className="text-xs text-white/80">連勝</div>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-xl font-bold">📚 {activity.words_learned_this_week}</div>
            <div className="text-xs text-white/80">本週</div>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-xl font-bold">🏆 {gamification.unlocked_achievements}</div>
            <div className="text-xs text-white/80">成就</div>
          </div>
        </div>

        {/* Recent Achievement */}
        {gamification.recent_achievements.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-500/20 rounded-lg border border-yellow-400/30">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-xl">{gamification.recent_achievements[0].icon || '🏅'}</span>
              <span className="font-medium">
                {gamification.recent_achievements[0].name_zh || gamification.recent_achievements[0].name_en}
              </span>
              <span className="text-yellow-300 text-xs">剛剛解鎖!</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Compact version for smaller spaces
export function GamificationWidgetCompact() {
  const { user } = useAuth()
  const userId = user?.id
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const hasFetched = useRef(false)

  useEffect(() => {
    const fetchData = async () => {
      if (!userId || hasFetched.current) return
      hasFetched.current = true

      try {
        const dashboardData = await dashboardApi.getDashboard()
        setData(dashboardData)
      } catch (err) {
        console.error('Failed to fetch gamification data:', err)
      } finally {
        setIsLoading(false)
      }
    }

    if (userId) {
      fetchData()
    }
  }, [userId])

  if (isLoading || !data) return null

  const { gamification, activity } = data

  return (
    <Link
      href="/profile"
      className="flex items-center gap-3 px-4 py-2 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-lg hover:from-indigo-500/30 hover:to-purple-500/30 transition-all border border-indigo-500/30"
    >
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-sm font-bold text-white">
        {gamification.level}
      </div>
      <div className="flex-1 min-w-0">
        <div className="h-1.5 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full"
            style={{ width: `${gamification.progress_percentage}%` }}
          ></div>
        </div>
        <div className="text-xs text-white/60 mt-0.5">{gamification.total_xp} XP</div>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span>🔥 {activity.activity_streak_days}</span>
      </div>
    </Link>
  )
}


