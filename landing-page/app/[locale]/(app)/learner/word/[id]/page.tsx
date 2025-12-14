'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams, useParams } from 'next/navigation'
import { MiningDetailPanel } from '@/components/features/mining/MiningDetailPanel'
import { vocabulary } from '@/lib/vocabulary'
import { useAppStore } from '@/stores/useAppStore'

interface WordPageProps {
  params: { id: string; locale: string }
}

/**
 * Dedicated Word Detail Page
 * 
 * This solves the "Stacking Context Trap" by using standard page navigation
 * instead of overlays/modals inside a game-style layout.
 * 
 * Benefits:
 * - Zero CSS bugs (fresh page, no z-index wars)
 * - Deep linking (shareable URLs like /learner/word/brave.a.01)
 * - Mobile friendly (full screen focus)
 * - Works perfectly with game-style layouts
 * 
 * Navigation tracking:
 * - Uses ?from= param to track where user came from
 * - Shows "← {word}" when drilling down from another word
 * - Shows "← Mining" when coming from the mining grid
 */
export default function WordPage({ params }: WordPageProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const routeParams = useParams()
  const locale = (routeParams.locale as string) || 'en'
  const senseId = decodeURIComponent(params.id)
  
  // Mining queue state from store
  const miningQueue = useAppStore((state) => state.miningQueue)
  const addToQueue = useAppStore((state) => state.addToQueue)
  const removeFromQueue = useAppStore((state) => state.removeFromQueue)
  const hydrateMiningQueue = useAppStore((state) => state.hydrateMiningQueue)
  const isInQueue = miningQueue.some(q => q.senseId === senseId)
  const miningQueueCount = miningQueue.length
  
  // Current word's display name for queue
  const [currentWord, setCurrentWord] = useState<string>('')
  
  // Track where we came from for smart back button
  const fromSenseId = searchParams.get('from')
  const [fromWord, setFromWord] = useState<string | null>(null)
  
  // Hydrate mining queue from IndexedDB on mount
  useEffect(() => {
    hydrateMiningQueue()
  }, [hydrateMiningQueue])
  
  // Load the current word's display name and "from" word
  useEffect(() => {
    vocabulary.getSense(senseId).then(sense => {
      if (sense?.word) {
        setCurrentWord(sense.word)
      }
    })
    
    if (fromSenseId) {
      vocabulary.getSense(fromSenseId).then(sense => {
        if (sense?.word) {
          // Capitalize first letter
          setFromWord(sense.word.charAt(0).toUpperCase() + sense.word.slice(1))
        }
      })
    }
  }, [senseId, fromSenseId])
  
  /**
   * Navigate back - uses explicit navigation instead of router.back()
   * This is more reliable when browser history might be empty/broken
   */
  const handleGoBack = () => {
    if (fromSenseId) {
      // Go back to the word we came from
      router.push(`/${locale}/learner/word/${encodeURIComponent(fromSenseId)}`)
    } else {
      // Go back to mining page
      router.push(`/${locale}/learner/mine`)
    }
  }
  
  /**
   * Toggle word in mining queue
   */
  const handleToggleQueue = () => {
    if (isInQueue) {
      removeFromQueue(senseId)
    } else {
      addToQueue(senseId, currentWord)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header with smart back button and queue toggle */}
      <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <button 
            onClick={handleGoBack} 
            className="flex items-center gap-2 text-slate-400 hover:text-cyan-400 transition-colors font-medium"
          >
            <span className="text-xl">←</span>
            <span>{fromWord ? fromWord : 'Mining'}</span>
          </button>
          
          {/* Add to Queue toggle - always visible */}
          <button
            onClick={handleToggleQueue}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all text-sm ${
              isInQueue
                ? 'bg-cyan-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <span>{isInQueue ? '✓' : '⛏️'}</span>
            <span>{isInQueue ? '已加入' : '加入挖礦'}</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto p-4 pb-24">
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
          <MiningDetailPanel 
            senseId={senseId}
            isSelected={isInQueue}
            onClose={handleGoBack}
            onToggleSelect={handleToggleQueue}
            onDrillDown={() => {
              // Could navigate to connections view
            }}
            onNavigateToSense={(newSenseId) => {
              // Navigate to the new word's page, passing current word as "from"
              router.push(`/${locale}/learner/word/${encodeURIComponent(newSenseId)}?from=${encodeURIComponent(senseId)}`)
            }}
          />
        </div>
      </div>
    </div>
  )
}

