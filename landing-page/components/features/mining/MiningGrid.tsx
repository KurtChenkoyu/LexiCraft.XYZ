'use client'

import { useState, useRef } from 'react'
import { MiningSquare } from './MiningSquare'
import { MiningFeedback } from './MiningFeedback'
import { useAppStore } from '@/stores/useAppStore'

interface MiningGridProps {
  senseIds: string[]  // Current layer senses
  layer: number       // 0, 1, or 2
  onDrillDown: (senseId: string) => void
  onBack?: () => void
}

interface FeedbackPosition {
  x: number
  y: number
}

export function MiningGrid({ senseIds, layer, onDrillDown, onBack }: MiningGridProps) {
  const [selectedSenses, setSelectedSenses] = useState<Set<string>>(new Set())
  const [feedbackPositions, setFeedbackPositions] = useState<FeedbackPosition[]>([])
  
  const minedSenses = useAppStore((state) => state.minedSenses)
  const mineSenses = useAppStore((state) => state.mineSenses)
  const isSenseMined = useAppStore((state) => state.isSenseMined)
  
  const gridRef = useRef<HTMLDivElement>(null)
  
  // Debug: Log what we receive
  console.log('🔲 MiningGrid render:', { 
    senseIdsCount: senseIds.length, 
    minedCount: minedSenses.size,
    layer 
  })
  
  // Filter out already mined
  const availableSenses = senseIds.filter(id => !isSenseMined(id))
  
  console.log('🔲 Available senses:', availableSenses.length)
  
  const handleSelectAll = () => {
    setSelectedSenses(new Set(availableSenses))
  }
  
  const handleMineSelected = () => {
    const toMine = Array.from(selectedSenses)
    if (toMine.length === 0) return
    
    // Trigger feedback animations (center of viewport)
    const centerX = window.innerWidth / 2
    const centerY = window.innerHeight / 2
    const newPositions = toMine.map((_, i) => ({
      x: centerX + (Math.random() - 0.5) * 100,
      y: centerY + (Math.random() - 0.5) * 100,
    }))
    setFeedbackPositions(newPositions)
    
    // Clear feedback after animation
    setTimeout(() => setFeedbackPositions([]), 1000)
    
    // Mine in Zustand (instant update)
    mineSenses(toMine)
    
    // Clear selection
    setSelectedSenses(new Set())
  }
  
  const handleToggleSelect = (senseId: string) => {
    const newSet = new Set(selectedSenses)
    if (newSet.has(senseId)) {
      newSet.delete(senseId)
    } else {
      newSet.add(senseId)
    }
    setSelectedSenses(newSet)
  }
  
  return (
    <div className="relative">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {onBack && (
            <button 
              onClick={onBack}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors text-sm"
            >
              ← Layer {layer - 1}
            </button>
          )}
          <span className="text-slate-400 text-sm">
            Layer {layer} • {availableSenses.length} words
          </span>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={handleSelectAll}
            disabled={availableSenses.length === 0}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Select All ({availableSenses.length})
          </button>
          <button 
            onClick={handleMineSelected}
            disabled={selectedSenses.size === 0}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-bold transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ⛏️ Mine Selected ({selectedSenses.size})
          </button>
        </div>
      </div>
      
      {/* Grid - Responsive: 3 cols mobile, 4 cols tablet, 5 cols desktop */}
      <div 
        ref={gridRef}
        className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 mb-4"
      >
        {availableSenses.map((senseId) => (
          <MiningSquare
            key={senseId}
            senseId={senseId}
            isSelected={selectedSenses.has(senseId)}
            onToggleSelect={() => handleToggleSelect(senseId)}
          />
        ))}
      </div>
      
      {/* Empty state */}
      {availableSenses.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <div className="text-4xl mb-2">✅</div>
          <p className="text-lg">All words in this layer have been mined!</p>
          {onBack && (
            <button
              onClick={onBack}
              className="mt-4 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
            >
              ← Back to Layer {layer - 1}
            </button>
          )}
        </div>
      )}
      
      {/* Feedback Particles */}
      <MiningFeedback positions={feedbackPositions} />
    </div>
  )
}

