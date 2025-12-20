'use client'

import React, { useEffect, useMemo, memo } from 'react'
import { WordCard, EmojiWordCard } from './WordCard'
import { Block } from '@/types/mine'

interface WordGridProps {
  senseIds: string[]
  onWordClick?: (id: string) => void
  // For emoji pack - pass blocks directly with emoji data
  blocks?: Block[]
  isEmojiMode?: boolean
}

// Memoized WordGrid to prevent unnecessary re-renders
export const WordGrid = memo(function WordGrid({ 
  senseIds, 
  onWordClick, 
  blocks,
  isEmojiMode = false 
}: WordGridProps) {
  // Deduplicate sense IDs to avoid React key warnings
  const uniqueSenseIds = useMemo(() => {
    return Array.from(new Set(senseIds || []))
  }, [senseIds])

  // Debug: log whenever senseIds changes
  useEffect(() => {
    const dupeCount = (senseIds?.length || 0) - uniqueSenseIds.length
    if (dupeCount > 0) {
      console.warn(`⚠️ WordGrid: Removed ${dupeCount} duplicate sense IDs`)
    }
    console.log('🟢 WordGrid mounted/updated:', { 
      count: uniqueSenseIds.length,
      first5: uniqueSenseIds.slice(0, 5),
      isEmojiMode,
      blocksCount: blocks?.length || 0
    })
  }, [senseIds, uniqueSenseIds, isEmojiMode, blocks])

  // For emoji mode with blocks, use blocks directly
  if (isEmojiMode && blocks && blocks.length > 0) {
    return (
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
        {blocks.map((block) => (
          <EmojiWordCard 
            key={block.sense_id}
            block={block}
            onClick={onWordClick}
          />
        ))}
      </div>
    )
  }

  if (!uniqueSenseIds || uniqueSenseIds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 border-2 border-dashed border-slate-300 rounded-2xl bg-white/50">
        <span className="text-5xl mb-3">📭</span>
        <p className="text-lg font-medium">No words in this layer</p>
        <p className="text-sm mt-1">Try refreshing or searching for words</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
      {uniqueSenseIds.map((id) => (
        <WordCard 
          key={id} 
          senseId={id} 
          onClick={onWordClick} 
        />
      ))}
    </div>
  )
})

// Memoization display name for debugging
WordGrid.displayName = 'WordGrid'

