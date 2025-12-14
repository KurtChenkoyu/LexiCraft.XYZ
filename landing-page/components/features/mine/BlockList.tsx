'use client'

import { useState, useCallback } from 'react'
import { AnimatePresence } from 'framer-motion'
import { Block } from '@/types/mine'
import { BlockCard } from './BlockCard'
import { MiningDetailPanel } from '@/components/features/mining'

interface BlockListProps {
  blocks: Block[]
}

export function BlockList({ blocks }: BlockListProps) {
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)

  const handleBlockClick = useCallback((senseId: string) => {
    setSelectedBlockId(senseId)
  }, [])

  const handleCloseDetail = useCallback(() => {
    setSelectedBlockId(null)
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

      <AnimatePresence mode="wait">
        {selectedBlockId && (
          <MiningDetailPanel
            key={selectedBlockId}
            senseId={selectedBlockId}
            isSelected={false}
            onClose={handleCloseDetail}
            onToggleSelect={() => {}}
            onDrillDown={() => {}}
            onNavigateToSense={(newSenseId) => setSelectedBlockId(newSenseId)}
          />
        )}
      </AnimatePresence>
    </>
  )
}
