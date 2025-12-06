'use client'

import { useState } from 'react'
import { BlockDetail as BlockDetailType } from '@/types/mine'
import { mineApi } from '@/services/mineApi'
import { Spinner } from '@/components/ui'

interface BlockDetailModalProps {
  blockDetail: BlockDetailType | null
  isLoading: boolean
  onClose: () => void
}

export function BlockDetailModal({
  blockDetail,
  isLoading,
  onClose,
}: BlockDetailModalProps) {
  const [isStarting, setIsStarting] = useState(false)
  const [started, setStarted] = useState(false)

  const handleStartForging = async () => {
    if (!blockDetail || blockDetail.user_progress) {
      return // Already started
    }

    setIsStarting(true)
    try {
      await mineApi.startForging(blockDetail.sense_id)
      setStarted(true)
      // Refresh after a moment
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    } catch (err) {
      console.error('Failed to start forging:', err)
      alert('開始鍛造失敗，請重試')
    } finally {
      setIsStarting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8">
          <Spinner size="lg" className="text-cyan-600 mb-4" />
          <p className="text-gray-600">載入中...</p>
        </div>
      </div>
    )
  }

  if (!blockDetail) {
    return null
  }

  const getTierBadge = () => {
    const stars = '⭐'.repeat(Math.min(blockDetail.tier, 4))
    return stars
  }

  const canStartForging =
    !blockDetail.user_progress && !started && !isStarting

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                {blockDetail.word}
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">{getTierBadge()}</span>
                <span className="text-sm text-gray-600">
                  {blockDetail.total_value} XP
                </span>
                {blockDetail.connection_count > 0 && (
                  <span className="text-sm text-gray-500">
                    ({blockDetail.connection_count} 連接)
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Definitions */}
          <div className="space-y-4 mb-6">
            {blockDetail.definition_en && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">英文定義</h3>
                <p className="text-gray-700">{blockDetail.definition_en}</p>
              </div>
            )}
            {blockDetail.definition_zh && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">中文解釋</h3>
                <p className="text-gray-700">{blockDetail.definition_zh}</p>
              </div>
            )}
          </div>

          {/* Examples */}
          {(blockDetail.example_en || blockDetail.example_zh) && (
            <div className="space-y-4 mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">例句</h3>
              {blockDetail.example_en && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700 italic">
                    "{blockDetail.example_en}"
                  </p>
                </div>
              )}
              {blockDetail.example_zh && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700">{blockDetail.example_zh}</p>
                </div>
              )}
            </div>
          )}

          {/* Connections */}
          {blockDetail.connections.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">相關字塊</h3>
              <div className="flex flex-wrap gap-2">
                {blockDetail.connections.map((conn) => (
                  <div
                    key={conn.sense_id}
                    className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-lg text-sm"
                  >
                    {conn.word}
                    {conn.status && (
                      <span className="ml-2 text-xs">
                        {conn.status === 'solid' && '🟨'}
                        {conn.status === 'hollow' && '🧱'}
                        {conn.status === 'raw' && '🪨'}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* User Progress */}
          {blockDetail.user_progress && (
            <div className="mb-6 p-4 bg-green-50 rounded-lg">
              <h3 className="font-semibold text-green-900 mb-2">學習進度</h3>
              <div className="text-sm text-green-700">
                <p>狀態: {blockDetail.user_progress.status}</p>
                {blockDetail.user_progress.mastery_level && (
                  <p>熟練度: {blockDetail.user_progress.mastery_level}</p>
                )}
                {blockDetail.user_progress.started_at && (
                  <p>
                    開始時間:{' '}
                    {new Date(blockDetail.user_progress.started_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            {canStartForging && (
              <button
                onClick={handleStartForging}
                disabled={isStarting}
                className="flex-1 px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {isStarting ? '開始中...' : '開始鍛造'}
              </button>
            )}
            {started && (
              <div className="flex-1 px-6 py-3 bg-green-100 text-green-800 rounded-lg font-semibold text-center">
                已開始鍛造！
              </div>
            )}
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-semibold transition-colors"
            >
              關閉
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

