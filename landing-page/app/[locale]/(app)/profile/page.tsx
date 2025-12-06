'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import {
  learnerProfileApi,
  LearnerProfile,
  Achievement,
  StreakInfo,
} from '@/services/gamificationApi'
import {
  LevelBadge,
  StatsGrid,
  RecentAchievements,
  AchievementsSection,
  ProfileQuickActions,
} from '@/components/features/profile'

// Default empty profile - show UI immediately, never block
const defaultProfile: LearnerProfile = {
  user_id: '',
  level: { level: 1, xp: 0, xp_to_next: 100 },
  total_xp: 0,
  words_learned: 0,
  current_streak: 0,
  longest_streak: 0,
  recent_achievements: [],
}

export default function ProfilePage() {
  const { user } = useAuth()
  
  // Start with defaults - UI renders INSTANTLY
  const [profile, setProfile] = useState<LearnerProfile>(defaultProfile)
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [streaks, setStreaks] = useState<StreakInfo | null>(null)
  const [isOffline, setIsOffline] = useState(false)

  // Background fetch - non-blocking, updates UI silently
  useEffect(() => {
    if (!user?.id) return

    // Fetch in background - never blocks UI
    const fetchData = async () => {
      try {
        const [profileData, achievementsData, streaksData] = await Promise.all([
          learnerProfileApi.getProfile().catch(() => null),
          learnerProfileApi.getAchievements().catch(() => null),
          learnerProfileApi.getStreaks().catch(() => null),
        ])

        if (profileData) setProfile(profileData)
        if (achievementsData) setAchievements(achievementsData)
        if (streaksData) setStreaks(streaksData)
        setIsOffline(false)
      } catch {
        setIsOffline(true)
      }
    }

    fetchData()
  }, [user?.id])

  // ALWAYS show UI - never loading state, never error page
  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 pt-20 pb-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Offline indicator - subtle, non-blocking */}
        {isOffline && (
          <div className="mb-4 flex items-center justify-center gap-2 text-white/50 text-sm">
            <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
            離線模式
          </div>
        )}
        
        <LevelBadge levelInfo={profile.level} />
        
        <StatsGrid profile={profile} streaks={streaks} />

        <RecentAchievements achievements={profile.recent_achievements || []} />

        <AchievementsSection achievements={achievements} />

        <ProfileQuickActions />
      </div>
    </main>
  )
}
