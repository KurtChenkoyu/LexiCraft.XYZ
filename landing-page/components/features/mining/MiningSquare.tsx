'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { vocabulary, type VocabularySense } from '@/lib/vocabulary'
import { useAppStore } from '@/stores/useAppStore'
import { getXpValue } from '@/components/features/vocabulary'

interface MiningSquareProps {
  senseId: string
  isSelected: boolean
  onToggleSelect: () => void
}

/**
 * Get background color based on CEFR level
 * Visual encoding: Green = Easy, Amber = Medium, Red/Purple = Hard
 */
function getCefrBackgroundColor(cefr?: string): string {
  switch (cefr) {
    case 'A1':
      return 'bg-emerald-600 hover:bg-emerald-500'
    case 'A2':
      return 'bg-green-600 hover:bg-green-500'
    case 'B1':
      return 'bg-amber-600 hover:bg-amber-500'
    case 'B2':
      return 'bg-orange-600 hover:bg-orange-500'
    case 'C1':
      return 'bg-red-600 hover:bg-red-500'
    case 'C2':
      return 'bg-purple-600 hover:bg-purple-500'
    default:
      return 'bg-slate-600 hover:bg-slate-500'
  }
}

export function MiningSquare({ senseId, isSelected, onToggleSelect }: MiningSquareProps) {
  const progress = useAppStore((state) => state.progress)
  const [sense, setSense] = useState<VocabularySense | null>(null)
  const [isNavigating, setIsNavigating] = useState(false)

  useEffect(() => {
    let mounted = true
    
    async function loadSense() {
      const data = await vocabulary.getSense(senseId)
      if (mounted) {
        setSense(data)
      }
    }
    
    loadSense()
    
    return () => { mounted = false }
  }, [senseId])
  
  if (!sense) return null
  
  // Get value metrics
  const xp = getXpValue(sense)
  const cefr = sense.cefr || 'B1'
  
  // CEFR-based background color (visual difficulty indicator)
  const bgColor = getCefrBackgroundColor(cefr)
  
  return (
    <motion.div
      className="relative aspect-square"
      whileTap={{ scale: 0.95 }}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.15 }}
    >
      {/* Square - Using Link for instant prefetched navigation */}
      <Link
        href={`/learner/word/${encodeURIComponent(senseId)}`}
        prefetch={true}
        onClick={() => setIsNavigating(true)}
        className={`block w-full h-full rounded-xl ${bgColor} transition-all shadow-lg ${
          isSelected ? 'ring-3 ring-cyan-400 ring-offset-2 ring-offset-slate-900' : ''
        } flex flex-col items-center justify-center p-3 active:scale-95`}
      >
        {/* Word - bigger and bolder */}
        <div className="text-white font-bold text-base sm:text-xl mb-1 text-center leading-tight">
          {sense.word}
        </div>
        
        {/* XP Value only (CEFR shown via background color) */}
        <div className="text-white/90 text-sm font-semibold">
          💎 {xp}
        </div>
        
        {/* Checkmark if selected */}
        {isSelected && (
          <div className="absolute inset-0 flex items-center justify-center bg-cyan-400/30 text-white text-2xl rounded-xl">
            ✓
          </div>
        )}
        
        {/* Loading overlay - shows immediately on click */}
        {isNavigating && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/70 rounded-xl">
            <div className="animate-spin h-8 w-8 border-3 border-cyan-400 border-t-transparent rounded-full" />
          </div>
        )}
      </Link>
      
      {/* Checkbox (top-right corner) - bigger for touch */}
      <button
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onToggleSelect()
        }}
        className="absolute -top-1.5 -right-1.5 w-6 h-6 bg-white rounded-full border-2 border-slate-700 flex items-center justify-center shadow-lg z-10 active:scale-90"
      >
        {isSelected && <span className="text-sm text-slate-900 font-bold">✓</span>}
      </button>
    </motion.div>
  )
}

