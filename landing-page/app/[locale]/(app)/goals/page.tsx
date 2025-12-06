'use client'

import { useEffect, useState, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Link } from '@/i18n/routing'
import { goalsApi, Goal, GoalSuggestion, CreateGoalRequest } from '@/services/gamificationApi'

// Goal type labels and icons
const goalTypeConfig: Record<string, { label: string; labelZh: string; icon: string }> = {
  daily_words: { label: 'Daily Words', labelZh: '每日單字', icon: '📅' },
  weekly_words: { label: 'Weekly Words', labelZh: '每週單字', icon: '📆' },
  monthly_words: { label: 'Monthly Words', labelZh: '每月單字', icon: '📊' },
  streak: { label: 'Streak', labelZh: '連勝目標', icon: '🔥' },
  vocabulary_size: { label: 'Vocabulary Size', labelZh: '詞彙量目標', icon: '📚' },
}

export default function GoalsPage() {
  const { user } = useAuth()
  const userId = user?.id

  const [goals, setGoals] = useState<Goal[]>([])
  const [suggestions, setSuggestions] = useState<GoalSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const hasFetched = useRef(false)

  // Form state
  const [newGoal, setNewGoal] = useState<CreateGoalRequest>({
    goal_type: 'weekly_words',
    target_value: 10,
    end_date: getDefaultEndDate(),
  })

  // Fetch goals - only once per user
  useEffect(() => {
    const fetchData = async () => {
      if (!userId || hasFetched.current) return
      hasFetched.current = true

      try {
        setIsLoading(true)
        const [goalsData, suggestionsData] = await Promise.all([
          goalsApi.getGoals(),
          goalsApi.getSuggestions(),
        ])
        setGoals(goalsData)
        setSuggestions(suggestionsData)
      } catch (err) {
        console.error('Failed to fetch goals:', err)
        setError('無法載入目標')
      } finally {
        setIsLoading(false)
      }
    }

    if (userId) {
      fetchData()
    }
  }, [userId])

  // Create goal
  const handleCreateGoal = async () => {
    try {
      setIsCreating(true)
      const created = await goalsApi.createGoal(newGoal)
      setGoals([created, ...goals])
      setShowCreateModal(false)
      setNewGoal({ goal_type: 'weekly_words', target_value: 10, end_date: getDefaultEndDate() })
    } catch (err) {
      console.error('Failed to create goal:', err)
      alert('建立目標失敗')
    } finally {
      setIsCreating(false)
    }
  }

  // Delete goal
  const handleDeleteGoal = async (goalId: string) => {
    if (!confirm('確定要刪除此目標嗎？')) return

    try {
      await goalsApi.deleteGoal(goalId)
      setGoals(goals.filter((g) => g.id !== goalId))
    } catch (err) {
      console.error('Failed to delete goal:', err)
      alert('刪除目標失敗')
    }
  }

  // Use suggestion
  const handleUseSuggestion = (suggestion: GoalSuggestion) => {
    setNewGoal({
      goal_type: suggestion.goal_type,
      target_value: suggestion.target_value,
      end_date: suggestion.end_date,
    })
    setShowCreateModal(true)
  }

  // Separate active and completed goals
  const activeGoals = goals.filter((g) => g.status === 'active')
  const completedGoals = goals.filter((g) => g.status === 'completed')
  const failedGoals = goals.filter((g) => g.status === 'failed')

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-cyan-900 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white/80 text-lg">載入中...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-cyan-900 pt-20 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              🎯 學習目標
            </h1>
            <p className="text-white/60 mt-2">設定目標，追蹤進度，達成成就</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-5 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition-all flex items-center gap-2"
          >
            <span>+</span> 新增目標
          </button>
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white/80 mb-4 flex items-center gap-2">
              💡 建議目標
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleUseSuggestion(suggestion)}
                  className="bg-white/10 backdrop-blur-xl rounded-xl p-4 border border-white/20 hover:bg-white/15 transition-all text-left group"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">
                      {goalTypeConfig[suggestion.goal_type]?.icon || '🎯'}
                    </span>
                    <span className="text-white font-semibold">
                      {goalTypeConfig[suggestion.goal_type]?.labelZh || suggestion.goal_type}
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-cyan-400 mb-1">
                    {suggestion.target_value}
                  </div>
                  <div className="text-white/60 text-sm">{suggestion.reason}</div>
                  <div className="mt-3 text-cyan-400 text-sm group-hover:translate-x-1 transition-transform">
                    使用此建議 →
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Active Goals */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-white/80 mb-4 flex items-center gap-2">
            ⚡ 進行中的目標 ({activeGoals.length})
          </h2>
          {activeGoals.length === 0 ? (
            <div className="bg-white/5 rounded-xl p-8 text-center border border-white/10">
              <p className="text-white/60">還沒有進行中的目標</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 text-cyan-400 hover:text-cyan-300"
              >
                建立第一個目標 →
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {activeGoals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} onDelete={handleDeleteGoal} />
              ))}
            </div>
          )}
        </div>

        {/* Completed Goals */}
        {completedGoals.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white/80 mb-4 flex items-center gap-2">
              ✅ 已完成 ({completedGoals.length})
            </h2>
            <div className="space-y-4">
              {completedGoals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} onDelete={handleDeleteGoal} />
              ))}
            </div>
          </div>
        )}

        {/* Failed Goals */}
        {failedGoals.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white/80 mb-4 flex items-center gap-2">
              ❌ 未達成 ({failedGoals.length})
            </h2>
            <div className="space-y-4 opacity-60">
              {failedGoals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} onDelete={handleDeleteGoal} />
              ))}
            </div>
          </div>
        )}

        {/* Back Link */}
        <div className="text-center mt-8">
          <Link href="/profile" className="text-white/60 hover:text-white transition-colors">
            ← 返回個人資料
          </Link>
        </div>
      </div>

      {/* Create Goal Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-white/20">
            <h3 className="text-xl font-bold text-white mb-6">建立新目標</h3>

            {/* Goal Type */}
            <div className="mb-4">
              <label className="block text-white/80 text-sm mb-2">目標類型</label>
              <select
                value={newGoal.goal_type}
                onChange={(e) => setNewGoal({ ...newGoal, goal_type: e.target.value })}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                {Object.entries(goalTypeConfig).map(([type, config]) => (
                  <option key={type} value={type} className="bg-slate-800">
                    {config.icon} {config.labelZh}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Value */}
            <div className="mb-4">
              <label className="block text-white/80 text-sm mb-2">目標數值</label>
              <input
                type="number"
                value={newGoal.target_value}
                onChange={(e) => setNewGoal({ ...newGoal, target_value: parseInt(e.target.value) || 0 })}
                min="1"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            {/* End Date */}
            <div className="mb-6">
              <label className="block text-white/80 text-sm mb-2">截止日期</label>
              <input
                type="date"
                value={newGoal.end_date}
                onChange={(e) => setNewGoal({ ...newGoal, end_date: e.target.value })}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-3 bg-white/10 rounded-xl text-white hover:bg-white/20 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateGoal}
                disabled={isCreating}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl text-white font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                {isCreating ? '建立中...' : '建立目標'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

// Goal Card Component
function GoalCard({ goal, onDelete }: { goal: Goal; onDelete: (id: string) => void }) {
  const config = goalTypeConfig[goal.goal_type] || { label: goal.goal_type, labelZh: goal.goal_type, icon: '🎯' }
  const isActive = goal.status === 'active'
  const isCompleted = goal.status === 'completed'

  return (
    <div
      className={`bg-white/10 backdrop-blur-xl rounded-xl p-5 border transition-all ${
        isCompleted
          ? 'border-green-500/50 bg-green-500/10'
          : isActive
          ? 'border-white/20 hover:bg-white/15'
          : 'border-red-500/30'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="text-3xl">{config.icon}</div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-white font-semibold">{config.labelZh}</h3>
              {isCompleted && <span className="text-green-400">✅</span>}
            </div>
            <div className="text-2xl font-bold text-cyan-400">
              {goal.current_value} / {goal.target_value}
            </div>
            <div className="text-white/60 text-sm mt-1">
              截止：{goal.end_date?.split('T')[0] || '未設定'}
            </div>
          </div>
        </div>

        {isActive && (
          <button
            onClick={() => onDelete(goal.id)}
            className="text-white/40 hover:text-red-400 transition-colors p-2"
          >
            ✕
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <div className="h-3 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              isCompleted
                ? 'bg-gradient-to-r from-green-400 to-emerald-500'
                : 'bg-gradient-to-r from-cyan-400 to-blue-500'
            }`}
            style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-sm text-white/60 mt-1">
          <span>{goal.progress_percentage}% 完成</span>
          {isCompleted && goal.completed_at && (
            <span>完成於 {new Date(goal.completed_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>
    </div>
  )
}

// Helper function for default end date (7 days from now)
function getDefaultEndDate(): string {
  const date = new Date()
  date.setDate(date.getDate() + 7)
  return date.toISOString().split('T')[0]
}


