'use client'

import { useState, useCallback } from 'react'
import { Block, BlockDetail as BlockDetailType } from '@/types/mine'
import { BlockCard } from './BlockCard'
import { BlockDetailModal } from './BlockDetailModal'
import { vocabulary } from '@/lib/vocabulary'
import { progressApi } from '@/services/progressApi'

interface BlockListProps {
  blocks: Block[]
}

export function BlockList({ blocks }: BlockListProps) {
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
  const [blockDetail, setBlockDetail] = useState<BlockDetailType | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [navigationHistory, setNavigationHistory] = useState<string[]>([])

  /**
   * Load block detail from local vocabulary store
   */
  const loadBlockDetail = useCallback((senseId: string) => {
    // Get block detail from LOCAL vocabulary store (INSTANT)
    const localDetail = vocabulary.getBlockDetail(senseId)
    
    if (localDetail) {
      // Set detail immediately from local data
      setBlockDetail(localDetail)
      setIsLoadingDetail(false)
      
      // Optionally fetch user progress in background
      progressApi.getBlockProgress(senseId).then(progress => {
        if (progress) {
          setBlockDetail(prev => prev ? {
            ...prev,
            user_progress: {
              status: progress.status,
              tier: progress.tier,
              started_at: progress.started_at,
              mastery_level: progress.mastery_level,
    }
          } : prev)
        }
      }).catch(() => {
        // Ignore progress fetch errors - we still have the vocabulary data
      })
    } else {
      console.warn('Vocabulary not loaded, block detail unavailable:', senseId)
    }
  }, [])

  const handleBlockClick = useCallback((senseId: string) => {
    setSelectedBlockId(senseId)
    setNavigationHistory([])  // Clear history when opening new block
    loadBlockDetail(senseId)
  }, [loadBlockDetail])

  /**
   * Navigate to another sense (from connections or other senses)
   * This allows in-modal navigation without closing
   */
  const handleNavigateToSense = useCallback((senseId: string) => {
    // Save current to history for back navigation
    if (selectedBlockId) {
      setNavigationHistory(prev => [...prev, selectedBlockId])
    }
    setSelectedBlockId(senseId)
    loadBlockDetail(senseId)
  }, [selectedBlockId, loadBlockDetail])

  const handleCloseDetail = useCallback(() => {
    setSelectedBlockId(null)
    setBlockDetail(null)
    setNavigationHistory([])
  }, [])

  if (blocks.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 text-lg">目前沒有可探索的字塊</p>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {blocks.map((block) => (
          <BlockCard
            key={block.sense_id}
            block={block}
            onClick={() => handleBlockClick(block.sense_id)}
          />
        ))}
      </div>

      {selectedBlockId && (
        <BlockDetailModal
          blockDetail={blockDetail}
          isLoading={isLoadingDetail}
          onClose={handleCloseDetail}
          onNavigateToSense={handleNavigateToSense}
        />
      )}
    </>
  )
}
