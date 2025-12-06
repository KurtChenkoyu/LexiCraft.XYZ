'use client'

import { Achievement } from '@/services/gamificationApi'
import { tierBgColors } from './AchievementCard'

interface RecentAchievementsProps {
  achievements: Achievement[]
}

export function RecentAchievements({ achievements }: RecentAchievementsProps) {
  if (!achievements || achievements.length === 0) return null

  return (
    <div className="mb-12">
      <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
        ✨ 最近解鎖
      </h2>
      <div className="flex flex-wrap gap-4">
        {achievements.map((achievement) => (
          <div
            key={achievement.id}
            className={`relative overflow-hidden rounded-xl p-4 border-2 ${
              tierBgColors[achievement.tier as keyof typeof tierBgColors] || tierBgColors.bronze
            } animate-pulse-slow`}
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">{achievement.icon || '🏅'}</span>
              <div>
                <div className="font-bold text-gray-900">{achievement.name_zh || achievement.name_en}</div>
                <div className="text-sm text-gray-600">
                  +{achievement.xp_reward || 0} XP
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

