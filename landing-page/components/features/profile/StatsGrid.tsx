'use client'

import { LearnerProfile, StreakInfo } from '@/services/gamificationApi'

interface StatsGridProps {
  profile: LearnerProfile | null
  streaks: StreakInfo | null
}

export function StatsGrid({ profile, streaks }: StatsGridProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
      {/* Streak */}
      <StatCard
        emoji="🔥"
        value={streaks?.current_streak || 0}
        label="天連續學習"
        warning={streaks?.streak_at_risk ? '今日還未學習！' : undefined}
      />

      {/* Vocabulary */}
      <StatCard
        emoji="📚"
        value={profile?.vocabulary_size || 0}
        label="單字已學會"
      />

      {/* This Week */}
      <StatCard
        emoji="📅"
        value={profile?.words_learned_this_week || 0}
        label="本週學習"
      />

      {/* Achievements */}
      <StatCard
        emoji="🏆"
        value={`${profile?.unlocked_achievements || 0}/${profile?.total_achievements || 0}`}
        label="成就解鎖"
      />
    </div>
  )
}

interface StatCardProps {
  emoji: string
  value: number | string
  label: string
  warning?: string
}

function StatCard({ emoji, value, label, warning }: StatCardProps) {
  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-colors">
      <div className="text-4xl mb-2">{emoji}</div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-white/60 text-sm">{label}</div>
      {warning && (
        <div className="mt-2 text-xs text-orange-400 flex items-center gap-1">
          <span>⚠️</span> {warning}
        </div>
      )}
    </div>
  )
}

