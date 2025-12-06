'use client'

import { useState, useCallback, useMemo } from 'react'
import { BlockDetail as BlockDetailType, BlockConnection, OtherSense } from '@/types/mine'
import { localStore } from '@/lib/local-store'
import { syncService } from '@/services/syncService'
import { Spinner } from '@/components/ui'
import { vocabulary } from '@/lib/vocabulary'
import { useIsMobile } from '@/hooks/useMediaQuery'
import { BottomSheet } from '@/components/ui/BottomSheet'

interface BlockDetailModalProps {
  blockDetail: BlockDetailType | null
  isLoading: boolean
  onClose: () => void
  onStatusChange?: (senseId: string, status: 'raw' | 'hollow' | 'solid') => void
  onNavigateToSense?: (senseId: string) => void  // Navigate to another sense
}

/**
 * Format POS tag to human-readable Chinese
 */
function formatPOS(pos: string | undefined): string {
  if (!pos) return ''
  const posMap: Record<string, string> = {
    'n': '名詞',
    'v': '動詞',
    'adj': '形容詞',
    'adv': '副詞',
    'prep': '介詞',
    'conj': '連接詞',
    'pron': '代名詞',
    'det': '限定詞',
    'interj': '感嘆詞',
  }
  return posMap[pos.toLowerCase()] || pos.toUpperCase()
}

// CEFR level colors
const cefrColors: Record<string, { bg: string; text: string; border: string }> = {
  'A1': { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-300' },
  'A2': { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
  'B1': { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300' },
  'B2': { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
  'C1': { bg: 'bg-rose-100', text: 'text-rose-700', border: 'border-rose-300' },
  'C2': { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300' },
}

export function BlockDetailModal({
  blockDetail,
  isLoading,
  onClose,
  onStatusChange,
  onNavigateToSense,
}: BlockDetailModalProps) {
  const [isStarting, setIsStarting] = useState(false)
  const [started, setStarted] = useState(false)
  const [localStatus, setLocalStatus] = useState<'raw' | 'hollow' | 'solid' | null>(null)
  const isMobile = useIsMobile()

  // Compute CEFR, hops, and network value
  const enrichedData = useMemo(() => {
    if (!blockDetail) return null

    const sense = vocabulary.getSense(blockDetail.sense_id)
    const hops = vocabulary.getHopConnections(blockDetail.sense_id)
    const networkValue = vocabulary.calculateNetworkValue(blockDetail.sense_id)

    return {
      cefr: sense?.cefr,
      hops,
      networkValue,
      frequencyRank: sense?.frequency_rank,
    }
  }, [blockDetail])

  /**
   * Handle start forging with OPTIMISTIC UPDATE
   * 1. Update UI immediately
   * 2. Save to local store
   * 3. Queue server sync (background)
   */
  const handleStartForging = useCallback(async () => {
    if (!blockDetail || blockDetail.user_progress || started) {
      return // Already started
    }

    // 1. OPTIMISTIC UPDATE - Update UI immediately
    setIsStarting(true)
    setLocalStatus('hollow')
    setStarted(true)
    
    // Notify parent about status change
    onStatusChange?.(blockDetail.sense_id, 'hollow')

    try {
      // 2. Save to local store
      await localStore.saveProgress(blockDetail.sense_id, 'hollow', {
        startedAt: new Date().toISOString(),
      })

      // 3. Queue server sync (background, non-blocking)
      syncService.queueAction('START_FORGING', blockDetail.sense_id)
        .then(() => {
          console.log('Forging action queued for sync')
        })
        .catch((err) => {
          console.error('Failed to queue action:', err)
        })

    } catch (err) {
      console.error('Failed to save progress locally:', err)
      // Don't revert - optimistic update should stick
      // Server sync will happen eventually
    } finally {
      setIsStarting(false)
    }
  }, [blockDetail, started, onStatusChange])

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 text-center">
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

  // Determine current status (local status takes precedence)
  const currentStatus = localStatus || 
    (blockDetail.user_progress?.status === 'verified' || blockDetail.user_progress?.status === 'mastered' ? 'solid' :
     blockDetail.user_progress?.status === 'learning' || blockDetail.user_progress?.status === 'pending' ? 'hollow' :
     blockDetail.user_progress ? 'hollow' : 'raw')

  const canStartForging = currentStatus === 'raw' && !started && !isStarting

  // Content component to avoid duplication
  const ModalContent = () => (
    <div className={isMobile ? 'p-4' : 'p-6'}>
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-3xl font-bold text-gray-900">
                {blockDetail.word}
              </h2>
                {/* POS tag */}
                {blockDetail.pos && (
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-sm font-medium">
                    {formatPOS(blockDetail.pos)}
                  </span>
                )}
                {/* Status indicator */}
                <span className="text-2xl">
                  {currentStatus === 'solid' && '🟨'}
                  {currentStatus === 'hollow' && '🧱'}
                  {currentStatus === 'raw' && '🪨'}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold">{getTierBadge()}</span>
                <span className="text-sm text-gray-600">
                  {blockDetail.total_value} XP
                </span>
                {blockDetail.connection_count > 0 && (
                  <span className="text-sm text-gray-500">
                    ({blockDetail.connection_count} 連接)
                  </span>
                )}
                {/* CEFR Badge */}
                {enrichedData?.cefr && (
                  <span className={`px-2 py-0.5 text-xs font-bold rounded border ${
                    cefrColors[enrichedData.cefr]?.bg || 'bg-gray-100'
                  } ${cefrColors[enrichedData.cefr]?.text || 'text-gray-700'} ${
                    cefrColors[enrichedData.cefr]?.border || 'border-gray-300'
                  }`}>
                    {enrichedData.cefr}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl leading-none p-2"
              aria-label="關閉"
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

          {/* Network Stats - Hops and Value */}
          {enrichedData && (
            <div className="mb-6 p-4 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-xl border border-cyan-100">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <span className="text-lg">🕸️</span>
                詞彙網絡
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                {/* Direct connections (Hop 1) */}
                <div className="bg-white/80 rounded-lg p-3">
                  <div className="text-2xl font-bold text-cyan-600">
                    {enrichedData.hops.hop1.length}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">直接連結</div>
                  <div className="text-[10px] text-gray-400">(1 hop)</div>
                </div>
                
                {/* Second-degree connections (Hop 2) */}
                <div className="bg-white/80 rounded-lg p-3">
                  <div className="text-2xl font-bold text-blue-600">
                    {enrichedData.hops.hop2.length}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">二度連結</div>
                  <div className="text-[10px] text-gray-400">(2 hops)</div>
                </div>
                
                {/* Total network */}
                <div className="bg-white/80 rounded-lg p-3">
                  <div className="text-2xl font-bold text-purple-600">
                    {enrichedData.hops.totalNetwork}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">網絡規模</div>
                  <div className="text-[10px] text-gray-400">total reach</div>
                </div>
                
                {/* Network value */}
                <div className="bg-white/80 rounded-lg p-3">
                  <div className="text-2xl font-bold text-amber-600">
                    {enrichedData.networkValue.networkMultiplier}×
                  </div>
                  <div className="text-xs text-gray-500 mt-1">網絡乘數</div>
                  <div className="text-[10px] text-gray-400">
                    {enrichedData.networkValue.networkValue} XP
                  </div>
                </div>
              </div>
              
              {/* Frequency rank if available */}
              {enrichedData.frequencyRank && (
                <div className="mt-3 pt-3 border-t border-cyan-100 text-center text-sm text-gray-600">
                  詞頻排名：<span className="font-semibold text-cyan-700">#{enrichedData.frequencyRank}</span>
                </div>
              )}
            </div>
          )}

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

          {/* Other Senses of the Same Word */}
          {blockDetail.other_senses && blockDetail.other_senses.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">
                「{blockDetail.word}」的其他意思
              </h3>
              <div className="space-y-2">
                {blockDetail.other_senses.map((sense) => (
                  <button
                    key={sense.sense_id}
                    onClick={() => onNavigateToSense?.(sense.sense_id)}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors group"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{sense.word}</span>
                      {sense.pos && (
                        <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                          {formatPOS(sense.pos)}
                        </span>
                      )}
                      <span className="text-cyan-600 text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                        點擊查看 →
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{sense.definition_preview}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Connections */}
          {blockDetail.connections.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">相關字塊</h3>
              <div className="flex flex-wrap gap-2">
                {blockDetail.connections.map((conn) => (
                  <button
                    key={conn.sense_id}
                    onClick={() => onNavigateToSense?.(conn.sense_id)}
                    className="px-3 py-1.5 bg-cyan-100 hover:bg-cyan-200 text-cyan-800 rounded-lg text-sm flex items-center gap-1.5 transition-colors cursor-pointer"
                    title={`查看「${conn.word}」`}
                  >
                    <span>{conn.word}</span>
                    {conn.type === 'OPPOSITE_TO' && (
                      <span className="text-xs text-cyan-600 bg-cyan-200 px-1 rounded">(反義)</span>
                    )}
                    {conn.status && (
                      <span className="text-xs">
                        {conn.status === 'solid' && '🟨'}
                        {conn.status === 'hollow' && '🧱'}
                        {conn.status === 'raw' && '🪨'}
                      </span>
                    )}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">點擊任一字塊可預覽其內容</p>
            </div>
          )}

          {/* User Progress */}
          {(blockDetail.user_progress || localStatus) && (
            <div className="mb-6 p-4 bg-green-50 rounded-lg">
              <h3 className="font-semibold text-green-900 mb-2">學習進度</h3>
              <div className="text-sm text-green-700">
                <p>
                  狀態: {
                    currentStatus === 'solid' ? '已掌握' :
                    currentStatus === 'hollow' ? '學習中' : '未開始'
                  }
                </p>
                {blockDetail.user_progress?.mastery_level && (
                  <p>熟練度: {blockDetail.user_progress.mastery_level}</p>
                )}
                {blockDetail.user_progress?.started_at && (
                  <p>
                    開始時間:{' '}
                    {new Date(blockDetail.user_progress.started_at).toLocaleDateString('zh-TW')}
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
                className="flex-1 px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isStarting ? (
                  <span className="flex items-center justify-center gap-2">
                    <Spinner size="sm" className="text-white" />
                    開始中...
                  </span>
                ) : (
                  '開始鍛造'
                )}
              </button>
            )}
            {started && (
              <div className="flex-1 px-6 py-3 bg-green-100 text-green-800 rounded-lg font-semibold text-center flex items-center justify-center gap-2">
                <span>✓</span>
                <span>已開始鍛造！</span>
              </div>
            )}
            {currentStatus === 'hollow' && !started && (
              <button
                className="flex-1 px-6 py-3 bg-amber-100 text-amber-800 rounded-lg font-semibold text-center"
                disabled
              >
                學習中...
              </button>
            )}
            {currentStatus === 'solid' && (
              <div className="flex-1 px-6 py-3 bg-yellow-100 text-yellow-800 rounded-lg font-semibold text-center">
                已掌握 🎉
              </div>
            )}
            {/* Hide close button on mobile (use sheet drag or X) */}
            {!isMobile && (
              <button
                onClick={onClose}
                className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-semibold transition-colors"
              >
                關閉
              </button>
            )}
          </div>
        </div>
  )

  // Mobile: Use BottomSheet
  if (isMobile) {
    return (
      <BottomSheet
        isOpen={!!blockDetail}
        onClose={onClose}
        title={blockDetail?.word}
        maxHeight={95}
      >
        <ModalContent />
      </BottomSheet>
    )
  }

  // Desktop: Centered modal
  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <ModalContent />
      </div>
    </div>
  )
}
