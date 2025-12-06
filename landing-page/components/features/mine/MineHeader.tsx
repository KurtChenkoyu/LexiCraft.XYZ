'use client'

import { UserStats } from '@/types/mine'

interface MineHeaderProps {
  mode: 'starter' | 'personalized'
  userStats: UserStats
  gapsCount?: number
  prerequisitesCount?: number
  onRefreshSuggestions?: () => void
}

export function MineHeader({
  mode,
  userStats,
  gapsCount,
  prerequisitesCount,
  onRefreshSuggestions,
}: MineHeaderProps) {
  return (
    <div className="mb-8">
      <div className="text-center mb-6">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
          {mode === 'starter' ? '探索礦區' : '你的挖礦路徑'}
        </h1>
        <div className="flex items-center justify-center gap-4">
        <p className="text-xl text-gray-600">
          {mode === 'starter' ? (
            '選擇字塊開始挖礦，系統會從你的探索中了解你的程度'
          ) : (
            <>
              根據你的評估結果，發現了{' '}
              {gapsCount && gapsCount > 0 && (
                <span className="font-semibold text-cyan-600">{gapsCount} 個知識缺口</span>
              )}
              {prerequisitesCount && prerequisitesCount > 0 && (
                <>
                  {' '}和{' '}
                  <span className="font-semibold text-purple-600">
                    {prerequisitesCount} 個前置字塊
                  </span>
                </>
              )}
            </>
          )}
        </p>
          {mode === 'starter' && onRefreshSuggestions && (
            <button
              onClick={onRefreshSuggestions}
              className="px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg text-gray-700 text-sm transition-colors flex items-center gap-2 shadow-sm"
              title="重新產生建議字塊"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              換一批
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {userStats.total_discovered}
            </div>
            <div className="text-sm text-gray-600 mt-1">已發現</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {userStats.solid_count}
            </div>
            <div className="text-sm text-gray-600 mt-1">實心磚</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {userStats.hollow_count}
            </div>
            <div className="text-sm text-gray-600 mt-1">鍛造中</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-400">
              {userStats.raw_count}
            </div>
            <div className="text-sm text-gray-600 mt-1">原始字塊</div>
          </div>
        </div>
      </div>
    </div>
  )
}

