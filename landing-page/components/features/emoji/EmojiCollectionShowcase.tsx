'use client'

import { useMemo } from 'react'
import { useAppStore, selectActiveLearner } from '@/stores/useAppStore'
import type { CollectedWord } from '@/stores/useAppStore'

/**
 * EmojiCollectionShowcase - Trophy room for mastered emoji words
 * 
 * Shows only mastered words (status = 'mastered' or 'solid')
 * - Organized by category (shelves/rows)
 * - Animated emojis (user-provided assets)
 * - Sparkle effects for mastered words
 * - Empty state: "Keep learning to unlock more!"
 */
export function EmojiCollectionShowcase() {
  const activeLearner = useAppStore(selectActiveLearner)
  
  // ⚡ Read collectedWords directly from store (no filtering needed!)
  const collectedWords = useAppStore((state) => state.collectedWords) || []

  // Filter out archived words from main view (they go to separate Archive tab)
  const activeCollectedWords = useMemo(() => {
    return collectedWords.filter(w => !w.isArchived)
  }, [collectedWords])

  // Just group by category and sort (no filtering by status!)
  const masteredWords = useMemo(() => {
    if (activeCollectedWords.length === 0) return []
    
    const grouped = activeCollectedWords.reduce((acc, word) => {
      const category = word.category || '其他'
      if (!acc[category]) acc[category] = []
      acc[category].push(word)
      return acc
    }, {} as Record<string, CollectedWord[]>)
    
    const sorted = Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .flatMap(([_, words]) => words)
    
    return sorted
  }, [activeCollectedWords])

  // Separate archived words for Archive tab
  const archivedWords = useMemo(() => {
    return collectedWords.filter(w => w.isArchived)
  }, [collectedWords])
  
  // Get unique categories for mastered words (memoized)
  const categories = useMemo(() => {
    return Array.from(new Set(masteredWords.map(w => w.category))).sort()
  }, [masteredWords])
  
  if (masteredWords.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <div className="text-6xl mb-4">📦</div>
        <h3 className="text-2xl font-bold text-white mb-2">還沒有收藏任何詞彙</h3>
        <p className="text-slate-400 mb-6">繼續學習來解鎖更多收藏！</p>
        <a
          href="/learner/mine"
          className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-medium transition-colors"
        >
          前往礦區
        </a>
      </div>
    )
  }
  
  return (
    <div className="space-y-8">
      {/* Header Stats */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">✨ 我的收藏</h2>
            <p className="text-slate-400">
              已收藏 <span className="text-cyan-400 font-semibold">{masteredWords.length}</span> 個詞彙
            </p>
          </div>
          <div className="text-6xl">💎</div>
        </div>
      </div>
      
      {/* Collection by Category */}
      {categories.map(category => {
        const categoryWords = masteredWords.filter(w => w.category === category)
        
        return (
          <div key={category} className="space-y-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <span>{category}</span>
              <span className="text-sm text-slate-400">({categoryWords.length})</span>
            </h3>
            
            {/* Shelf/Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
              {categoryWords.map(word => {
                const srsLevel = word.masteryLevel || 'learning'
                
                // Visual styles based on SRS mastery level
                const getVisualStyle = () => {
                  switch (srsLevel) {
                    case 'learning':
                      return {
                        opacity: 'opacity-60',
                        glow: 'shadow-[0_0_8px_rgba(239,68,68,0.3)]',
                        badge: '🔥',
                        badgeColor: 'bg-red-500/20 text-red-400'
                      }
                    case 'familiar':
                      return {
                        opacity: 'opacity-80',
                        glow: 'shadow-[0_0_8px_rgba(251,191,36,0.4)]',
                        badge: '⚡',
                        badgeColor: 'bg-amber-500/20 text-amber-400'
                      }
                    case 'known':
                      return {
                        opacity: 'opacity-90',
                        glow: 'shadow-[0_0_8px_rgba(59,130,246,0.4)]',
                        badge: '💙',
                        badgeColor: 'bg-blue-500/20 text-blue-400'
                      }
                    case 'mastered':
                      return {
                        opacity: 'opacity-100',
                        glow: 'shadow-[0_0_12px_rgba(234,179,8,0.5)]',
                        badge: '✨',
                        badgeColor: 'bg-yellow-500/20 text-yellow-400'
                      }
                    case 'burned':
                      return {
                        opacity: 'opacity-100',
                        glow: 'shadow-[0_0_16px_rgba(234,179,8,0.8)]',
                        badge: '🏆',
                        badgeColor: 'bg-yellow-500/30 text-yellow-300'
                      }
                    default:
                      return {
                        opacity: 'opacity-60',
                        glow: 'shadow-[0_0_8px_rgba(239,68,68,0.3)]',
                        badge: '🔥',
                        badgeColor: 'bg-red-500/20 text-red-400'
                      }
                  }
                }
                
                const style = getVisualStyle()
                
                return (
                  <div
                    key={word.sense_id}
                    className={`group relative bg-slate-800/50 hover:bg-slate-700/50 rounded-xl p-4 transition-all hover:scale-110 border border-slate-700/50 hover:border-yellow-500/50 ${style.opacity} ${style.glow}`}
                  >
                    {/* Sparkle Effect (only for mastered/burned) */}
                    {(srsLevel === 'mastered' || srsLevel === 'burned') && (
                      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                        <div className="absolute top-1 right-1 text-yellow-400 animate-pulse">✨</div>
                        <div className="absolute bottom-1 left-1 text-yellow-400 animate-pulse" style={{ animationDelay: '0.2s' }}>✨</div>
                      </div>
                    )}
                    
                    {/* Timestamp tooltip for payout validation */}
                    {word.masteredAt && (
                      <div className="absolute bottom-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="text-[8px] text-slate-500 bg-slate-900/80 px-1 py-0.5 rounded">
                          {new Date(word.masteredAt).toLocaleDateString('zh-TW')}
                        </div>
                      </div>
                    )}
                    
                    {/* Animated Emoji (user will provide animated assets) */}
                    <div className="text-5xl mb-2 text-center transform group-hover:scale-110 transition-transform">
                      {word.emoji}
                    </div>
                    
                    {/* Word */}
                    <div className="text-center">
                      <div className="text-xs font-semibold text-white mb-1 line-clamp-1">{word.word}</div>
                      <div className="text-[10px] text-slate-400 line-clamp-2">{word.definition_zh}</div>
                    </div>
                    
                    {/* SRS Level Badge */}
                    <div className={`absolute top-2 right-2 ${style.badgeColor} px-1.5 py-0.5 rounded text-[10px]`}>
                      {style.badge}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
      
      {/* Progress Encouragement */}
      <div className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-xl p-6 border border-cyan-500/30 text-center">
        <p className="text-white font-semibold mb-2">
          繼續學習來解鎖更多收藏！
        </p>
        <p className="text-slate-300 text-sm">
          已收藏 {masteredWords.length} 個詞彙
        </p>
      </div>
    </div>
  )
}

