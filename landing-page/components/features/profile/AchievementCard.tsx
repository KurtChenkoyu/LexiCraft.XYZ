'use client'

import { Achievement } from '@/services/gamificationApi'

// Achievement tier colors
export const tierColors = {
  bronze: 'from-amber-600 to-amber-700',
  silver: 'from-gray-400 to-gray-500',
  gold: 'from-yellow-400 to-yellow-500',
  platinum: 'from-purple-400 to-purple-500',
}

export const tierBgColors = {
  bronze: 'bg-amber-100 border-amber-300',
  silver: 'bg-gray-100 border-gray-300',
  gold: 'bg-yellow-100 border-yellow-300',
  platinum: 'bg-purple-100 border-purple-300',
}

interface AchievementCardProps {
  achievement: Achievement
}

export function AchievementCard({ achievement }: AchievementCardProps) {
  const isUnlocked = achievement.unlocked
  const progress = achievement.progress_percentage || 0

  return (
    <div
      className={`relative rounded-xl p-5 border-2 transition-all ${
        isUnlocked
          ? `${tierBgColors[achievement.tier as keyof typeof tierBgColors] || tierBgColors.bronze} shadow-lg`
          : 'bg-white/5 border-white/10 opacity-60'
      }`}
    >
      {/* Tier Badge */}
      <div className="absolute top-3 right-3">
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-bold text-white bg-gradient-to-r ${
            tierColors[achievement.tier as keyof typeof tierColors] || tierColors.bronze
          }`}
        >
          {achievement.tier.toUpperCase()}
        </span>
      </div>

      {/* Icon and Title */}
      <div className="flex items-start gap-3 mb-3">
        <span className={`text-4xl ${isUnlocked ? '' : 'grayscale'}`}>
          {achievement.icon || '🏅'}
        </span>
        <div className="flex-1 min-w-0">
          <h3 className={`font-bold truncate ${isUnlocked ? 'text-gray-900' : 'text-white'}`}>
            {achievement.name_zh || achievement.name_en}
          </h3>
          <p className={`text-sm line-clamp-2 ${isUnlocked ? 'text-gray-600' : 'text-white/60'}`}>
            {achievement.description_zh || achievement.description_en}
          </p>
        </div>
      </div>

      {/* Progress or Reward */}
      {isUnlocked ? (
        <div className={`text-sm font-medium ${isUnlocked ? 'text-gray-700' : 'text-white/80'}`}>
          ✅ 已解鎖 · +{achievement.xp_reward || 0} XP
        </div>
      ) : (
        <div>
          <div className="flex justify-between text-xs text-white/60 mb-1">
            <span>進度</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  )
}

