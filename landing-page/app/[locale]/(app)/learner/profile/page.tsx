'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useAppStore, selectLearnerProfile, selectAchievements, selectActivePack, selectEmojiStats } from '@/stores/useAppStore'
import {
  learnerProfileApi,
  LearnerGamificationProfile,
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
import { StudyDesk } from '@/components/features/building'

// Default empty profile - show UI immediately, never block
const defaultProfile: LearnerGamificationProfile = {
  user_id: '',
  level: { 
    level: 1, 
    total_xp: 0, 
    xp_to_next_level: 100, 
    xp_in_current_level: 0, 
    progress_percentage: 0 
  },
  vocabulary_size: 0,
  current_streak: 0,
  words_learned_this_week: 0,
  words_learned_this_month: 0,
  recent_achievements: [],
  total_achievements: 0,
  unlocked_achievements: 0,
}

export default function ProfilePage() {
  const { user } = useAuth()
  
  // ZUSTAND-FIRST: Read from store (instant, pre-loaded by Bootstrap)
  const cachedProfile = useAppStore(selectLearnerProfile)
  const cachedAchievements = useAppStore(selectAchievements)
  const activePack = useAppStore(selectActivePack)
  const emojiStats = useAppStore(selectEmojiStats) // ⚡ Pre-loaded by Bootstrap
  
  // Use cached data if available, otherwise defaults
  const [profile, setProfile] = useState<LearnerGamificationProfile>(cachedProfile || defaultProfile)
  const [achievements, setAchievements] = useState<Achievement[]>(cachedAchievements || [])
  const [streaks, setStreaks] = useState<StreakInfo | null>(null)
  const [isOffline, setIsOffline] = useState(false)
  
  const isEmojiPack = activePack?.id === 'emoji_core'

  // Sync with Zustand when it updates (from background sync)
  useEffect(() => {
    if (cachedProfile) setProfile(cachedProfile)
  }, [cachedProfile])
  
  useEffect(() => {
    if (cachedAchievements) setAchievements(cachedAchievements)
  }, [cachedAchievements])

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

        {/* Emoji Pack Stats */}
        {isEmojiPack && emojiStats && (
          <div className="mt-6 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-xl p-6 border border-cyan-500/30">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              🎯 表情包統計
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="text-slate-400 text-sm mb-1">已收集</div>
                <div className="text-2xl font-bold text-cyan-400">
                  {emojiStats.collectedWords} / {emojiStats.totalWords}
                </div>
                <div className="h-2 bg-slate-700 rounded-full mt-2 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all"
                    style={{ width: `${(emojiStats.collectedWords / emojiStats.totalWords) * 100}%` }}
                  />
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="text-slate-400 text-sm mb-1">已掌握</div>
                <div className="text-2xl font-bold text-yellow-400">{emojiStats.masteredWords}</div>
                <div className="text-xs text-slate-500 mt-1">詞彙</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="text-slate-400 text-sm mb-1">學習中</div>
                <div className="text-2xl font-bold text-orange-400">{emojiStats.learningWords}</div>
                <div className="text-xs text-slate-500 mt-1">詞彙</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="text-slate-400 text-sm mb-1">連勝</div>
                <div className="text-2xl font-bold text-emerald-400">{profile.current_streak}</div>
                <div className="text-xs text-slate-500 mt-1">天</div>
              </div>
            </div>
          </div>
        )}

        {/* Study Desk - One Room MVP */}
        <div className="mt-8 mb-8 flex justify-center">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <StudyDesk 
              wordsLearned={profile.vocabulary_size} 
              size="lg"
            />
          </div>
        </div>
        
        <StatsGrid profile={profile} streaks={streaks} />

        <RecentAchievements achievements={profile.recent_achievements || []} />

        <AchievementsSection achievements={achievements} />

        <ProfileQuickActions />
      </div>
    </main>
  )
}
