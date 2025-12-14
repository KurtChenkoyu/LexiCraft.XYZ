'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { learnerProfileApi, Achievement } from '@/services/gamificationApi'
import { AchievementCard, tierColors, tierBgColors } from '@/components/features/profile'

/**
 * Parent Achievements Page
 * 
 * Achievement gallery for parents to view child progress.
 * 
 * URL: /parent/achievements
 */

// Category metadata for display
const CATEGORY_META: Record<string, { label: string; icon: string; description: string }> = {
  onboarding: { 
    label: '新手入門', 
    icon: '🌱', 
    description: '完成基本任務，開始你的學習之旅' 
  },
  streak: { 
    label: '連勝', 
    icon: '🔥', 
    description: '維持每日學習習慣' 
  },
  vocabulary: { 
    label: '詞彙', 
    icon: '📚', 
    description: '累積你的詞彙量' 
  },
  mastery: { 
    label: '精通', 
    icon: '✅', 
    description: '通過驗證掌握詞彙' 
  },
  social: { 
    label: '社交', 
    icon: '👥', 
    description: '與其他學習者互動' 
  },
  special: { 
    label: '特殊', 
    icon: '⭐', 
    description: '特殊事件與挑戰' 
  },
  hidden: { 
    label: '隱藏', 
    icon: '🔮', 
    description: '發現隱藏的成就' 
  },
}

// Tier sorting order
const TIER_ORDER = ['bronze', 'silver', 'gold', 'platinum']

export default function AchievementsPage() {
  const { user } = useAuth()
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedTier, setSelectedTier] = useState<string>('all')
  const [showUnlockedOnly, setShowUnlockedOnly] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!user?.id) return

    const fetchAchievements = async () => {
      try {
        const data = await learnerProfileApi.getAchievements()
        setAchievements(data)
      } catch (error) {
        console.error('Failed to fetch achievements:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchAchievements()
  }, [user?.id])

  // Get unique categories and tiers
  const categories = ['all', ...Array.from(new Set(achievements.map(a => a.category)))]
  const tiers = ['all', ...TIER_ORDER.filter(t => achievements.some(a => a.tier === t))]

  // Filter achievements
  const filteredAchievements = achievements.filter(a => {
    if (selectedCategory !== 'all' && a.category !== selectedCategory) return false
    if (selectedTier !== 'all' && a.tier !== selectedTier) return false
    if (showUnlockedOnly && !a.unlocked) return false
    return true
  })

  // Group by category for display
  const groupedByCategory = filteredAchievements.reduce((acc, achievement) => {
    const cat = achievement.category
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(achievement)
    return acc
  }, {} as Record<string, Achievement[]>)

  // Stats
  const totalUnlocked = achievements.filter(a => a.unlocked).length
  const totalAchievements = achievements.length
  const totalXP = achievements.filter(a => a.unlocked).reduce((sum, a) => sum + (a.xp_reward || 0), 0)
  const totalCrystals = achievements.filter(a => a.unlocked).reduce((sum, a) => sum + (a.crystal_reward || 0), 0)

  return (
    <>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🏆 成就系統</h1>
        <p className="text-gray-600">解鎖成就，獲得獎勵</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl p-4 border border-gray-200 text-center shadow-sm">
          <div className="text-3xl font-bold text-gray-900">{totalUnlocked}</div>
          <div className="text-sm text-gray-600">已解鎖</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 text-center shadow-sm">
          <div className="text-3xl font-bold text-gray-900">{totalAchievements}</div>
          <div className="text-sm text-gray-600">總成就</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 text-center shadow-sm">
          <div className="text-3xl font-bold text-yellow-500">{totalXP}</div>
          <div className="text-sm text-gray-600">獲得 XP</div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 text-center shadow-sm">
          <div className="text-3xl font-bold text-purple-500">{totalCrystals}</div>
          <div className="text-sm text-gray-600">獲得 💎</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl p-4 border border-gray-200 mb-8 shadow-sm">
        <div className="flex justify-between text-sm text-gray-700 mb-2">
          <span>整體進度</span>
          <span>{totalUnlocked} / {totalAchievements} ({totalAchievements > 0 ? Math.round(totalUnlocked / totalAchievements * 100) : 0}%)</span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div 
            className="h-full bg-cyan-500 rounded-full transition-all duration-500"
            style={{ width: `${totalAchievements > 0 ? (totalUnlocked / totalAchievements * 100) : 0}%` }}
          />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 border border-gray-200 mb-8 shadow-sm">
        <div className="flex flex-col sm:flex-row gap-4 flex-wrap">
          {/* Category Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs text-gray-600 mb-1 block">類別</label>
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    selectedCategory === cat
                      ? 'bg-cyan-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {cat === 'all' ? '全部' : (
                    <span className="flex items-center gap-1">
                      <span>{CATEGORY_META[cat]?.icon || '📌'}</span>
                      <span>{CATEGORY_META[cat]?.label || cat}</span>
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Tier Filter */}
          <div className="min-w-[150px]">
            <label className="text-xs text-gray-600 mb-1 block">等級</label>
            <div className="flex flex-wrap gap-2">
              {tiers.map(tier => (
                <button
                  key={tier}
                  onClick={() => setSelectedTier(tier)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                    selectedTier === tier
                      ? tier === 'all' 
                        ? 'bg-cyan-600 text-white'
                        : `bg-gradient-to-r ${tierColors[tier as keyof typeof tierColors]} text-white`
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {tier === 'all' ? '全部' : tier.charAt(0).toUpperCase() + tier.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Show Unlocked Only Toggle */}
          <div className="flex items-end">
            <button
              onClick={() => setShowUnlockedOnly(!showUnlockedOnly)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                showUnlockedOnly
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              ✅ 僅顯示已解鎖
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-gray-300 border-t-cyan-600 rounded-full animate-spin" />
          <p className="text-gray-600 mt-4">載入成就中...</p>
        </div>
      )}

      {/* Achievement Grid - Grouped by Category */}
      {!isLoading && selectedCategory === 'all' ? (
        <div className="space-y-8">
          {Object.entries(groupedByCategory).map(([category, categoryAchievements]) => (
            <div key={category} className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <div className="flex items-center gap-3 mb-6">
                <span className="text-3xl">{CATEGORY_META[category]?.icon || '📌'}</span>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    {CATEGORY_META[category]?.label || category}
                  </h2>
                  <p className="text-sm text-gray-600">
                    {CATEGORY_META[category]?.description || ''}
                  </p>
                </div>
                <div className="ml-auto text-sm text-gray-600">
                  {categoryAchievements.filter(a => a.unlocked).length} / {categoryAchievements.length}
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {categoryAchievements.map(achievement => (
                  <AchievementCard key={achievement.id} achievement={achievement} />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : !isLoading && (
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAchievements.map(achievement => (
              <AchievementCard key={achievement.id} achievement={achievement} />
            ))}
          </div>
          {filteredAchievements.length === 0 && (
            <div className="text-center py-12 text-gray-600">
              <span className="text-4xl mb-4 block">🔍</span>
              沒有符合條件的成就
            </div>
          )}
        </div>
      )}
    </>
  )
}

