'use client'

import { useEffect, useState, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Link } from '@/i18n/routing'
import { goalsApi, Goal, GoalSuggestion, CreateGoalRequest } from '@/services/gamificationApi'

/**
 * Parent Goals Page
 * 
 * Goal tracking for parents.
 * 
 * URL: /parent/goals
 */

// Goal type labels and icons
const goalTypeConfig: Record<string, { label: string; labelZh: string; icon: string }> = {
  daily_words: { label: 'Daily Words', labelZh: '每日單字', icon: '📅' },
  weekly_words: { label: 'Weekly Words', labelZh: '每週單字', icon: '📆' },
  monthly_words: { label: 'Monthly Words', labelZh: '每月單字', icon: '📊' },
  streak: { label: 'Streak', labelZh: '連勝目標', icon: '⚡' },
  vocabulary_size: { label: 'Vocabulary Size', labelZh: '詞彙量目標', icon: '📚' },
}

export default function GoalsPage() {
  const { user } = useAuth()
  const userId = user?.id

  // Start with defaults - UI renders INSTANTLY
  const [goals, setGoals] = useState<Goal[]>([])
  const [suggestions, setSuggestions] = useState<GoalSuggestion[]>([])
  const [isOffline, setIsOffline] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const hasFetched = useRef(false)

  // Form state
  const [newGoal, setNewGoal] = useState<CreateGoalRequest>({
    goal_type: 'weekly_words',
    target_value: 10,
    end_date: getDefaultEndDate(),
  })

  // Background fetch - non-blocking, updates UI silently
  useEffect(() => {
    if (!userId || hasFetched.current) return
    hasFetched.current = true

    const fetchData = async () => {
      try {
        setIsOffline(false)
        const [goalsData, suggestionsData] = await Promise.all([
          goalsApi.getGoals().catch(() => []),
          goalsApi.getSuggestions().catch(() => []),
        ])
        if (goalsData) setGoals(goalsData)
        if (suggestionsData) setSuggestions(suggestionsData)
      } catch (err) {
        console.error('Failed to fetch goals:', err)
        setIsOffline(true)
      }
    }

    fetchData()
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

  return (
    <>
      {/* Offline indicator */}
      {isOffline && (
        <div className="mb-4 flex items-center gap-2 text-amber-600 text-sm">
          <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
          離線模式 - 顯示快取數據
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            🎯 學習目標
          </h1>
          <p className="text-gray-600 mt-2">設定目標，追蹤進度，達成成就</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-5 py-3 bg-cyan-600 rounded-xl text-white font-semibold hover:bg-cyan-700 transition-all flex items-center gap-2"
        >
          <span>+</span> 新增目標
        </button>
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            💡 建議目標
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleUseSuggestion(suggestion)}
                className="bg-white rounded-xl p-4 border border-gray-200 hover:border-cyan-300 transition-all text-left group shadow-sm"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">
                    {goalTypeConfig[suggestion.goal_type]?.icon || '🎯'}
                  </span>
                  <span className="text-gray-900 font-semibold">
                    {goalTypeConfig[suggestion.goal_type]?.labelZh || suggestion.goal_type}
                  </span>
                </div>
                <div className="text-2xl font-bold text-cyan-600 mb-1">
                  {suggestion.target_value}
                </div>
                <div className="text-gray-600 text-sm">{suggestion.reason}</div>
                <div className="mt-3 text-cyan-600 text-sm group-hover:translate-x-1 transition-transform">
                  使用此建議 →
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Active Goals */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          ⚡ 進行中的目標 ({activeGoals.length})
        </h2>
        {activeGoals.length === 0 ? (
          <div className="bg-gray-50 rounded-xl p-8 text-center border border-gray-200">
            <p className="text-gray-600">還沒有進行中的目標</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-cyan-600 hover:text-cyan-700"
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
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
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
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
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
        <Link href="/parent/dashboard" className="text-gray-600 hover:text-gray-900 transition-colors">
          ← 返回控制台
        </Link>
      </div>

      {/* Create Goal Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <h3 className="text-xl font-bold text-gray-900 mb-6">建立新目標</h3>

            {/* Goal Type */}
            <div className="mb-4">
              <label className="block text-gray-700 text-sm mb-2">目標類型</label>
              <select
                value={newGoal.goal_type}
                onChange={(e) => setNewGoal({ ...newGoal, goal_type: e.target.value })}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                {Object.entries(goalTypeConfig).map(([type, config]) => (
                  <option key={type} value={type}>
                    {config.icon} {config.labelZh}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Value */}
            <div className="mb-4">
              <label className="block text-gray-700 text-sm mb-2">目標數值</label>
              <input
                type="number"
                value={newGoal.target_value}
                onChange={(e) => setNewGoal({ ...newGoal, target_value: parseInt(e.target.value) || 0 })}
                min="1"
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            {/* End Date */}
            <div className="mb-6">
              <label className="block text-gray-700 text-sm mb-2">截止日期</label>
              <input
                type="date"
                value={newGoal.end_date}
                onChange={(e) => setNewGoal({ ...newGoal, end_date: e.target.value })}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-3 bg-gray-100 rounded-xl text-gray-700 hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateGoal}
                disabled={isCreating}
                className="flex-1 px-4 py-3 bg-cyan-600 rounded-xl text-white font-semibold hover:bg-cyan-700 transition-all disabled:opacity-50"
              >
                {isCreating ? '建立中...' : '建立目標'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// Goal Card Component
function GoalCard({ goal, onDelete }: { goal: Goal; onDelete: (id: string) => void }) {
  const config = goalTypeConfig[goal.goal_type] || { label: goal.goal_type, labelZh: goal.goal_type, icon: '🎯' }
  const isActive = goal.status === 'active'
  const isCompleted = goal.status === 'completed'

  return (
    <div
      className={`bg-white rounded-xl p-5 border shadow-sm transition-all ${
        isCompleted
          ? 'border-green-200 bg-green-50'
          : isActive
          ? 'border-gray-200 hover:border-cyan-300'
          : 'border-red-200'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="text-3xl">{config.icon}</div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-gray-900 font-semibold">{config.labelZh}</h3>
              {isCompleted && <span className="text-green-500">✅</span>}
            </div>
            <div className="text-2xl font-bold text-cyan-600">
              {goal.current_value} / {goal.target_value}
            </div>
            <div className="text-gray-600 text-sm mt-1">
              截止：{goal.end_date?.split('T')[0] || '未設定'}
            </div>
          </div>
        </div>

        {isActive && (
          <button
            onClick={() => onDelete(goal.id)}
            className="text-gray-400 hover:text-red-500 transition-colors p-2"
          >
            ✕
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              isCompleted
                ? 'bg-green-500'
                : 'bg-cyan-500'
            }`}
            style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-sm text-gray-600 mt-1">
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

