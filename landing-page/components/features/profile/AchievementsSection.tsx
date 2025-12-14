'use client'

import { useState } from 'react'
import { Achievement } from '@/services/gamificationApi'
import { AchievementCard } from './AchievementCard'

interface AchievementsSectionProps {
  achievements: Achievement[]
}

// Helper function for category labels
function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    onboarding: '新手入門',
    streak: '連勝',
    vocabulary: '詞彙',
    mastery: '精通',
    social: '社交',
    special: '特殊',
    hidden: '隱藏',
  }
  return labels[category] || category
}

export function AchievementsSection({ achievements }: AchievementsSectionProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // Get unique categories
  const categories = ['all', ...Array.from(new Set(achievements.map((a) => a.category)))]

  // Filter achievements
  const filteredAchievements =
    selectedCategory === 'all'
      ? achievements
      : achievements.filter((a) => a.category === selectedCategory)

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          🎖️ 成就
        </h2>
        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                selectedCategory === category
                  ? 'bg-white text-indigo-900'
                  : 'bg-white/10 text-white/80 hover:bg-white/20'
              }`}
            >
              {category === 'all' ? '全部' : getCategoryLabel(category)}
            </button>
          ))}
        </div>
      </div>

      {/* Achievements Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAchievements.map((achievement) => (
          <AchievementCard key={achievement.id} achievement={achievement} />
        ))}
      </div>
    </div>
  )
}

