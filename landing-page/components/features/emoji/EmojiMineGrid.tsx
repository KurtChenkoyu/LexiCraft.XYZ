'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { packLoader } from '@/lib/pack-loader'
import { PackVocabularyItem } from '@/lib/pack-types'
import { useAppStore, selectActiveLearner, selectEmojiVocabulary, selectEmojiProgress } from '@/stores/useAppStore'

interface EmojiMineGridProps {
  onWordClick?: (senseId: string) => void
}

/**
 * EmojiMineGrid - Collection grid for emoji pack vocabulary
 * 
 * Shows all 200 emoji words in a responsive grid with:
 * - Infinite scroll (load 6 at a time)
 * - Status indicators (new, learning, reviewing, mastered)
 * - Category filters
 * - Progress bar
 * - Tap emoji → Navigate to verification
 */
export function EmojiMineGrid({ onWordClick }: EmojiMineGridProps) {
  const router = useRouter()
  const activeLearner = useAppStore(selectActiveLearner)
  
  // ⚡ Read from Zustand (pre-loaded by Bootstrap)
  const emojiVocabulary = useAppStore(selectEmojiVocabulary)
  const emojiProgress = useAppStore(selectEmojiProgress)
  
  // Fallback: Load on-demand if Zustand data is null
  const [allWords, setAllWords] = useState<PackVocabularyItem[]>(emojiVocabulary || [])
  const [progress, setProgress] = useState<Map<string, string>>(emojiProgress || new Map())
  const [loading, setLoading] = useState(!emojiVocabulary) // Only loading if no Zustand data
  
  const [displayedWords, setDisplayedWords] = useState<PackVocabularyItem[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [displayCount, setDisplayCount] = useState(6) // Start with 6 visible
  
  const observerRef = useRef<IntersectionObserver | null>(null)
  const loadMoreRef = useRef<HTMLDivElement>(null)
  
  // Sync with Zustand when it updates
  useEffect(() => {
    if (emojiVocabulary) {
      setAllWords(emojiVocabulary)
      setLoading(false)
    }
  }, [emojiVocabulary])
  
  useEffect(() => {
    // Sync with Zustand: update local state when store changes OR learner switches
    if (!activeLearner) {
      // No learner selected → clear local progress
      setProgress(new Map())
      return
    }

    if (emojiProgress === null) {
      // Store cleared for this learner - clear local state to trigger fallback effect
      if (process.env.NODE_ENV === 'development') {
        console.log('🔄 EmojiMineGrid: emojiProgress is null, clearing local progress for learner', activeLearner.id)
      }
      setProgress(new Map())
    } else if (emojiProgress instanceof Map) {
      // Store has data (may be empty Map or filled) - always sync to local state
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ EmojiMineGrid: syncing', emojiProgress.size, 'items from Zustand for learner', activeLearner.id)
      }
      setProgress(emojiProgress)
    }
  }, [emojiProgress, activeLearner?.id])
  
  // Load on-demand if Zustand data is null (fallback)
  useEffect(() => {
    if (!emojiVocabulary) {
      const loadVocabulary = async () => {
        setLoading(true)
        try {
          const packData = await packLoader.loadPack('emoji_core')
          if (packData) {
            setAllWords(packData.vocabulary)
          }
        } catch (error) {
          console.error('Failed to load emoji pack:', error)
        } finally {
          setLoading(false)
        }
      }
      loadVocabulary()
    }
  }, [emojiVocabulary])
  
  // Load progress on-demand if Zustand data is null OR empty (fallback)
  useEffect(() => {
    const activeLearnerId = activeLearner?.id
    // NOTE: EmojiMineGrid is now a pure consumer of the store.
    // All emoji progress for a learner is loaded via:
    //   Bootstrap → downloadService.syncProgress → localStore/importProgress
    //   and switchLearner(), which both update emojiProgress in Zustand.
    // This component must NOT talk to progressApi or localStore directly.
    if (!activeLearnerId) {
      return
    }
  }, [emojiProgress, activeLearner?.id])
  
  // Filter by category
  useEffect(() => {
    if (!selectedCategory) {
      setDisplayedWords(allWords.slice(0, displayCount))
      setHasMore(allWords.length > displayCount)
    } else {
      const filtered = allWords.filter(w => w.category === selectedCategory)
      setDisplayedWords(filtered.slice(0, displayCount))
      setHasMore(filtered.length > displayCount)
    }
  }, [selectedCategory, allWords, displayCount])
  
  // Infinite scroll with Intersection Observer
  useEffect(() => {
    if (!hasMore || loading) return
    
    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setDisplayCount(prev => {
            const newCount = prev + 6
            const filtered = selectedCategory 
              ? allWords.filter(w => w.category === selectedCategory)
              : allWords
            setHasMore(newCount < filtered.length)
            return newCount
          })
        }
      },
      { threshold: 0.1 }
    )
    
    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current)
    }
    
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [hasMore, loading, selectedCategory, allWords])
  
  // Get status for a word
  const getStatus = (senseId: string): 'new' | 'learning' | 'reviewing' | 'mastered' => {
    const status = progress.get(senseId)
    if (!status) return 'new'
    if (status === 'solid' || status === 'mastered') return 'mastered'
    if (status === 'hollow' || status === 'learning') return 'learning'
    if (status === 'reviewing') return 'reviewing'
    return 'new'
  }
  
  // Get status emoji and color
  const getStatusDisplay = (status: 'new' | 'learning' | 'reviewing' | 'mastered') => {
    switch (status) {
      case 'new':
        return { emoji: '📦', color: 'text-slate-400', bg: 'bg-slate-700/30' }
      case 'learning':
        return { emoji: '🔥', color: 'text-orange-400', bg: 'bg-orange-500/20' }
      case 'reviewing':
        return { emoji: '✨', color: 'text-blue-400', bg: 'bg-blue-500/20' }
      case 'mastered':
        return { emoji: '💎', color: 'text-yellow-400', bg: 'bg-yellow-500/20' }
    }
  }
  
  // Handle word click - open detail modal or navigate to verification
  const handleWordClick = (senseId: string) => {
    if (onWordClick) {
      onWordClick(senseId)
    } else {
      // Fallback: navigate to verification if no callback provided
      router.push(`/learner/verification?sense_id=${senseId}`)
    }
  }
  
  // Get unique categories
  const categories = Array.from(new Set(allWords.map(w => w.category))).sort()
  
  // Calculate collection stats
  const totalWords = allWords.length
  
  // DEBUG: Log all progress statuses to diagnose the "3 vs 4" issue
  if (process.env.NODE_ENV === 'development') {
    const allStatuses = Array.from(progress.entries())
    const learningStatuses = allStatuses.filter(([_, s]) => s === 'hollow' || s === 'learning' || s === 'pending')
    console.log('🔍 EmojiMineGrid Progress Debug:', {
      totalProgressEntries: progress.size,
      allStatuses: allStatuses.map(([id, s]) => ({ senseId: id, status: s })),
      learningWords: learningStatuses.map(([id, s]) => ({ senseId: id, status: s })),
      learningCount: learningStatuses.length
    })
  }
  
  // FIX: Include 'verified' in mastered count (matches switchLearner)
  const masteredCount = Array.from(progress.values()).filter(s => s === 'solid' || s === 'mastered' || s === 'verified').length
  // FIX: Include 'pending' in learning count (matches switchLearner)
  const learningCount = Array.from(progress.values()).filter(s => s === 'hollow' || s === 'learning' || s === 'pending').length
  const collectionProgress = totalWords > 0 ? ((masteredCount + learningCount) / totalWords) * 100 : 0
  
  if (loading && allWords.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">載入表情詞彙...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-white">收藏進度</h3>
          <span className="text-xs text-slate-400">
            {masteredCount + learningCount} / {totalWords}
          </span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-500"
            style={{ width: `${collectionProgress}%` }}
          />
        </div>
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <span>💎</span>
            <span>已掌握: {masteredCount}</span>
          </div>
          <div className="flex items-center gap-1">
            <span>📚</span>
            <span>學習中: {learningCount}</span>
          </div>
          <div className="flex items-center gap-1">
            <span>📦</span>
            <span>未開始: {totalWords - masteredCount - learningCount}</span>
          </div>
        </div>
      </div>
      
      {/* Category Filters */}
      {categories.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              !selectedCategory
                ? 'bg-cyan-500 text-white'
                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
            }`}
          >
            全部
          </button>
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                selectedCategory === category
                  ? 'bg-cyan-500 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      )}
      
      {/* Word Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {displayedWords.map((word) => {
          const status = getStatus(word.sense_id)
          const statusDisplay = getStatusDisplay(status)
          
          return (
            <button
              key={word.sense_id}
              onClick={() => handleWordClick(word.sense_id)}
              className="group relative bg-slate-800/50 hover:bg-slate-700/50 rounded-xl p-4 transition-all hover:scale-105 border border-slate-700/50 hover:border-cyan-500/50"
            >
              {/* Status Badge */}
              <div className={`absolute top-2 right-2 ${statusDisplay.bg} ${statusDisplay.color} px-2 py-1 rounded-lg text-xs`}>
                {statusDisplay.emoji}
              </div>
              
              {/* Emoji */}
              <div className="text-4xl mb-2 text-center">{word.emoji}</div>
              
              {/* Word */}
              <div className="text-center">
                <div className="text-sm font-semibold text-white mb-1">{word.word}</div>
                <div className="text-xs text-slate-400 line-clamp-2">{word.definition_zh}</div>
              </div>
              
              {/* Hover Effect */}
              <div className="absolute inset-0 bg-gradient-to-t from-cyan-500/0 to-cyan-500/0 group-hover:from-cyan-500/10 group-hover:to-transparent rounded-xl transition-all pointer-events-none" />
            </button>
          )
        })}
      </div>
      
      {/* Load More Trigger */}
      {hasMore && (
        <div ref={loadMoreRef} className="flex items-center justify-center py-8">
          <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      )}
      
      {/* End of List */}
      {!hasMore && displayedWords.length > 0 && (
        <div className="text-center py-8 text-slate-400 text-sm">
          <p>✨ 已顯示所有詞彙</p>
        </div>
      )}
    </div>
  )
}

