'use client'

import React, { useEffect, useState, memo, useCallback, useMemo } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { vocabulary, VocabularySense } from '@/lib/vocabulary'
import { useAppStore } from '@/stores/useAppStore'
import { Block } from '@/types/mine'
import { packLoader } from '@/lib/pack-loader'

interface WordCardProps {
  senseId: string
  onClick?: (id: string) => void
}

interface EmojiWordCardProps {
  block: Block
  onClick?: (id: string) => void
}

// CEFR level colors for background
const cefrBgColors: Record<string, string> = {
  'A1': 'bg-emerald-100 hover:bg-emerald-200',
  'A2': 'bg-green-100 hover:bg-green-200',
  'B1': 'bg-amber-100 hover:bg-amber-200',
  'B2': 'bg-orange-100 hover:bg-orange-200',
  'C1': 'bg-rose-100 hover:bg-rose-200',
  'C2': 'bg-purple-100 hover:bg-purple-200',
}

// Memoized WordCard to prevent unnecessary re-renders
export const WordCard = memo(function WordCard({ senseId, onClick }: WordCardProps) {
  const [sense, setSense] = useState<VocabularySense | null>(null)
  const params = useParams()
  const locale = (params.locale as string) || 'en'
  
  // Optimized queue check - only re-renders when THIS card's queue status changes
  const isInQueue = useAppStore(
    useCallback((state) => state.miningQueue.some(q => q.senseId === senseId), [senseId])
  )
  const addToQueue = useAppStore((state) => state.addToQueue)
  const removeFromQueue = useAppStore((state) => state.removeFromQueue)

  useEffect(() => {
    let mounted = true
    vocabulary.getSense(senseId).then(data => {
      if (mounted) setSense(data)
    })
    return () => { mounted = false }
  }, [senseId])

  if (!sense) {
    return (
      <div className="aspect-square rounded-xl bg-slate-200 animate-pulse shadow-sm" />
    )
  }

  const bgColor = cefrBgColors[sense.cefr || 'B1'] || 'bg-slate-100 hover:bg-slate-200'
  const xpValue = sense.total_value || sense.base_xp || 100

  const handleQueueToggle = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (isInQueue) {
      removeFromQueue(senseId)
    } else {
      addToQueue(senseId, sense.word)
    }
  }

  return (
    <Link
      href={`/${locale}/learner/word/${encodeURIComponent(senseId)}`}
      className={`group relative aspect-square w-full rounded-xl p-3 text-center shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg active:translate-y-0 ${bgColor}`}
    >
      {/* Queue Toggle Button */}
      <button
        onClick={handleQueueToggle}
        className={`absolute right-2 top-2 w-7 h-7 rounded-full flex items-center justify-center transition-all text-sm ${
          isInQueue
            ? 'bg-cyan-500 text-white shadow-md'
            : 'bg-white/80 text-slate-400 hover:bg-white hover:text-slate-600 shadow-sm'
        }`}
        title={isInQueue ? '從佇列移除' : '加入挖礦佇列'}
      >
        {isInQueue ? '✓' : '⛏'}
      </button>

      {/* Word Content */}
      <div className="flex h-full flex-col justify-center items-center">
        <span className="font-bold text-slate-800 text-lg leading-tight break-all">
          {sense.word}
        </span>
        
        {/* XP Badge */}
        <span className="mt-2 px-2 py-0.5 text-xs font-bold rounded-full bg-white/60 text-amber-700">
          💎 {xpValue}
        </span>
      </div>
    </Link>
  )
})

// Display name for debugging
WordCard.displayName = 'WordCard'

// Difficulty colors for emoji pack
const difficultyColors: Record<number, string> = {
  1: 'bg-emerald-100 hover:bg-emerald-200',
  2: 'bg-green-100 hover:bg-green-200',
  3: 'bg-amber-100 hover:bg-amber-200',
  4: 'bg-orange-100 hover:bg-orange-200',
  5: 'bg-rose-100 hover:bg-rose-200',
}

/**
 * EmojiWordCard - Card for emoji pack vocabulary
 * Shows emoji prominently with word below
 * Fetches emoji from pack if not present on block
 */
export const EmojiWordCard = memo(function EmojiWordCard({ block, onClick }: EmojiWordCardProps) {
  const params = useParams()
  const locale = (params.locale as string) || 'en'
  const [emoji, setEmoji] = useState<string>(block.emoji || '')
  const [translation, setTranslation] = useState<string>(block.definition_preview || '')
  
  // Fetch emoji from pack if not on block
  useEffect(() => {
    if (!block.emoji) {
      packLoader.getItem('emoji_core', block.sense_id).then(item => {
        if (item) {
          setEmoji(item.emoji)
          if (!block.definition_preview) {
            setTranslation(item.definition_zh)
          }
        }
      }).catch(() => {
        // Fallback emoji
        setEmoji('📝')
      })
    }
  }, [block.sense_id, block.emoji, block.definition_preview])
  
  // Optimized queue check
  const isInQueue = useAppStore(
    useCallback((state) => state.miningQueue.some(q => q.senseId === block.sense_id), [block.sense_id])
  )
  const addToQueue = useAppStore((state) => state.addToQueue)
  const removeFromQueue = useAppStore((state) => state.removeFromQueue)

  const bgColor = difficultyColors[block.tier] || 'bg-slate-100 hover:bg-slate-200'
  const xpValue = block.total_value || 100

  const handleQueueToggle = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (isInQueue) {
      removeFromQueue(block.sense_id)
    } else {
      addToQueue(block.sense_id, block.word)
    }
  }

  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault()
      onClick(block.sense_id)
    }
  }

  return (
    <div
      onClick={handleClick}
      className={`group relative aspect-square w-full rounded-xl p-2 text-center shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg active:translate-y-0 cursor-pointer ${bgColor}`}
    >
      {/* Queue Toggle Button */}
      <button
        onClick={handleQueueToggle}
        className={`absolute right-1 top-1 w-6 h-6 rounded-full flex items-center justify-center transition-all text-xs ${
          isInQueue
            ? 'bg-cyan-500 text-white shadow-md'
            : 'bg-white/80 text-slate-400 hover:bg-white hover:text-slate-600 shadow-sm'
        }`}
        title={isInQueue ? '從佇列移除' : '加入挖礦佇列'}
      >
        {isInQueue ? '✓' : '⛏'}
      </button>

      {/* Emoji + Word Content */}
      <div className="flex h-full flex-col justify-center items-center">
        {/* Big Emoji */}
        <span className="text-4xl mb-1">{emoji || '📝'}</span>
        
        {/* Word */}
        <span className="font-bold text-slate-800 text-sm leading-tight">
          {block.word}
        </span>
        
        {/* Chinese translation */}
        {translation && (
          <span className="text-xs text-slate-500 mt-0.5 truncate max-w-full">
            {translation}
          </span>
        )}
        
        {/* XP Badge */}
        <span className="mt-1 px-2 py-0.5 text-[10px] font-bold rounded-full bg-white/60 text-amber-700">
          💎 {xpValue}
        </span>
      </div>
    </div>
  )
})

EmojiWordCard.displayName = 'EmojiWordCard'


