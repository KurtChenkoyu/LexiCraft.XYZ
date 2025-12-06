'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/contexts/UserDataContext'
import { Link } from '@/i18n/routing'
import { coachProfileApi, CoachDashboard } from '@/services/gamificationApi'

export default function CoachDashboardPage() {
  const { user } = useAuth()
  const { children, selectedChildId, selectChild, isLoading: childrenLoading } = useUserData()

  const [dashboard, setDashboard] = useState<CoachDashboard | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboard = async () => {
      if (!selectedChildId) return

      try {
        setIsLoading(true)
        setError(null)
        const data = await coachProfileApi.getDashboard(selectedChildId)
        setDashboard(data)
      } catch (err: any) {
        console.error('Failed to fetch coach dashboard:', err)
        setError(err?.response?.data?.detail || '無法載入儀表板')
      } finally {
        setIsLoading(false)
      }
    }

    if (selectedChildId && !childrenLoading) {
      fetchDashboard()
    }
  }, [selectedChildId, childrenLoading])

  // Loading state
  if (childrenLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-cyan-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">載入中...</p>
        </div>
      </main>
    )
  }

  // No children state
  if (children.length === 0) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 pt-20 pb-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="bg-white rounded-2xl shadow-xl p-12">
            <div className="text-6xl mb-4">👨‍👩‍👧</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">還沒有學習者</h1>
            <p className="text-gray-600 mb-6">請先在設定中新增孩子</p>
            <Link
              href="/settings"
              className="inline-block px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-semibold transition-colors"
            >
              前往設定 →
            </Link>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 pt-20 pb-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              📊 學習分析
            </h1>
            <p className="text-gray-600 mt-1">了解孩子的學習進度和表現</p>
          </div>

          {/* Child Selector */}
          {children.length > 1 && (
            <select
              value={selectedChildId || ''}
              onChange={(e) => selectChild(e.target.value)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            >
              {children.map((child) => (
                <option key={child.id} value={child.id}>
                  {child.name || '未命名'} {child.age ? `(${child.age}歲)` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 text-red-600 hover:text-red-700"
            >
              重試
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && !error && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-cyan-600 border-t-transparent mx-auto mb-4"></div>
            <p className="text-gray-600">載入學習數據...</p>
          </div>
        )}

        {/* Dashboard Content */}
        {dashboard && !isLoading && (
          <>
            {/* Overview Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard
                icon="📚"
                value={dashboard.overview.vocabulary_size}
                label="單字量"
                trend={dashboard.vocabulary.growth_rate_per_week > 0 ? `+${dashboard.vocabulary.growth_rate_per_week.toFixed(1)}/週` : undefined}
              />
              <StatCard
                icon="⚡"
                value={dashboard.overview.total_xp}
                label="總經驗值"
                sublabel={`Level ${dashboard.overview.level}`}
              />
              <StatCard
                icon="🔥"
                value={dashboard.overview.current_streak}
                label="連勝天數"
              />
              <StatCard
                icon="🏆"
                value={dashboard.overview.unlocked_achievements}
                label="成就解鎖"
                sublabel={`/ ${dashboard.overview.total_achievements}`}
              />
            </div>

            {/* Performance & Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Activity Section */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  📅 學習活動
                </h2>
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">本週學習</span>
                    <span className="font-bold text-cyan-600">{dashboard.activity.words_learned_this_week} 單字</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">本月學習</span>
                    <span className="font-bold text-cyan-600">{dashboard.activity.words_learned_this_month} 單字</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">學習速率</span>
                    <span className="font-bold text-cyan-600">{dashboard.activity.learning_rate_per_week.toFixed(1)} 單字/週</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">最後活動</span>
                    <span className="text-gray-800">
                      {dashboard.activity.last_active_date
                        ? new Date(dashboard.activity.last_active_date).toLocaleDateString()
                        : '無'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Performance Section */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  📈 學習表現
                </h2>
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">總複習次數</span>
                    <span className="font-bold text-green-600">{dashboard.performance.total_reviews}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">記憶率</span>
                    <span className={`font-bold ${dashboard.performance.retention_rate >= 0.8 ? 'text-green-600' : dashboard.performance.retention_rate >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {(dashboard.performance.retention_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">平均反應時間</span>
                    <span className="text-gray-800">{(dashboard.performance.avg_response_time_ms / 1000).toFixed(1)} 秒</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">正確次數</span>
                    <span className="text-gray-800">{dashboard.performance.total_correct}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Insights */}
            {dashboard.insights.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  💡 學習洞察
                </h2>
                <div className="space-y-4">
                  {dashboard.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}

            {/* Goals */}
            {dashboard.goals.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  🎯 學習目標
                </h2>
                <div className="space-y-4">
                  {dashboard.goals.filter(g => g.status === 'active').map((goal) => (
                    <div key={goal.id} className="bg-gray-50 rounded-xl p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-semibold text-gray-900">{getGoalTypeLabel(goal.goal_type)}</span>
                        <span className="text-cyan-600 font-bold">
                          {goal.current_value} / {goal.target_value}
                        </span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-cyan-500 rounded-full"
                          style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between text-sm text-gray-500 mt-1">
                        <span>{goal.progress_percentage}% 完成</span>
                        <span>截止：{goal.end_date?.split('T')[0]}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Achievements */}
            {dashboard.achievements.recent.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  🏅 最近成就
                </h2>
                <div className="flex flex-wrap gap-3">
                  {dashboard.achievements.recent.map((achievement) => (
                    <div
                      key={achievement.id}
                      className="flex items-center gap-2 px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg"
                    >
                      <span className="text-2xl">{achievement.icon || '🏅'}</span>
                      <span className="font-medium text-gray-900">
                        {achievement.name_zh || achievement.name_en}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Back Link */}
        <div className="text-center mt-8">
          <Link href="/dashboard" className="text-gray-600 hover:text-gray-900 transition-colors">
            ← 返回儀表板
          </Link>
        </div>
      </div>
    </main>
  )
}

// Stat Card Component
function StatCard({
  icon,
  value,
  label,
  trend,
  sublabel,
}: {
  icon: string
  value: number
  label: string
  trend?: string
  sublabel?: string
}) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-5">
      <div className="flex items-start justify-between">
        <span className="text-3xl">{icon}</span>
        {trend && <span className="text-xs text-green-600 font-medium">{trend}</span>}
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold text-gray-900">
          {value.toLocaleString()}
          {sublabel && <span className="text-sm font-normal text-gray-500"> {sublabel}</span>}
        </div>
        <div className="text-gray-600 text-sm">{label}</div>
      </div>
    </div>
  )
}

// Insight Card Component
function InsightCard({
  insight,
}: {
  insight: {
    type: string
    title: string
    message: string
    priority: string
    data?: Record<string, any>
  }
}) {
  const typeConfig: Record<string, { icon: string; bgColor: string; borderColor: string }> = {
    improvement: { icon: '✅', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
    concern: { icon: '⚠️', bgColor: 'bg-red-50', borderColor: 'border-red-200' },
    milestone: { icon: '🎯', bgColor: 'bg-purple-50', borderColor: 'border-purple-200' },
    recommendation: { icon: '💡', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' },
  }

  const config = typeConfig[insight.type] || typeConfig.recommendation

  return (
    <div className={`${config.bgColor} border ${config.borderColor} rounded-xl p-4`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{config.icon}</span>
        <div>
          <h3 className="font-semibold text-gray-900">{insight.title}</h3>
          <p className="text-gray-600 text-sm mt-1">{insight.message}</p>
        </div>
      </div>
    </div>
  )
}

// Helper function for goal type labels
function getGoalTypeLabel(goalType: string): string {
  const labels: Record<string, string> = {
    daily_words: '每日單字',
    weekly_words: '每週單字',
    monthly_words: '每月單字',
    streak: '連勝目標',
    vocabulary_size: '詞彙量目標',
  }
  return labels[goalType] || goalType
}


