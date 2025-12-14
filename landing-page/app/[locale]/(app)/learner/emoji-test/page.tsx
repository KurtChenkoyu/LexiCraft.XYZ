'use client'

import { useState, useEffect } from 'react'
import { packLoader } from '@/lib/pack-loader'
import { EmojiMCQ, PackVocabularyItem } from '@/lib/pack-types'
import { EmojiMCQCard } from '@/components/features/mcq/EmojiMCQCard'
import { useAppStore, selectActivePack } from '@/stores/useAppStore'

/**
 * Emoji MCQ Test Page
 * 
 * Temporary page to test the emoji matching game.
 * Will be integrated into the main verification flow.
 */
export default function EmojiTestPage() {
  const activePack = useAppStore(selectActivePack)
  const [loading, setLoading] = useState(true)
  const [vocabulary, setVocabulary] = useState<PackVocabularyItem[]>([])
  const [currentMcq, setCurrentMcq] = useState<EmojiMCQ | null>(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [showingResult, setShowingResult] = useState(false)

  // Load pack on mount
  useEffect(() => {
    const loadPack = async () => {
      setLoading(true)
      const vocab = await packLoader.getVocabulary(activePack?.id || 'emoji_core')
      setVocabulary(vocab)
      setLoading(false)
    }
    loadPack()
  }, [activePack?.id])

  // Generate next MCQ
  const generateNextMcq = async () => {
    if (vocabulary.length === 0) return
    
    // Pick random word
    const randomItem = vocabulary[Math.floor(Math.random() * vocabulary.length)]
    
    // Generate MCQs
    const mcqs = await packLoader.generateMCQs(
      activePack?.id || 'emoji_core',
      randomItem.sense_id
    )
    
    if (mcqs.length > 0) {
      // Randomly pick word_to_emoji or emoji_to_word
      const randomMcq = mcqs[Math.floor(Math.random() * mcqs.length)]
      setCurrentMcq(randomMcq)
      setShowingResult(false)
    }
  }

  // Generate first MCQ when vocabulary loads
  useEffect(() => {
    if (vocabulary.length > 0 && !currentMcq) {
      generateNextMcq()
    }
  }, [vocabulary])

  // Handle answer
  const handleAnswer = (isCorrect: boolean) => {
    setScore(prev => ({
      correct: prev.correct + (isCorrect ? 1 : 0),
      total: prev.total + 1
    }))
    setShowingResult(true)
    
    // Auto-advance after delay
    setTimeout(() => {
      generateNextMcq()
    }, 1500)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">🎯</div>
          <p className="text-slate-400">載入表情符號包...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">
          {activePack?.emoji || '🎯'} {activePack?.name || 'Emoji Match'}
        </h1>
        <p className="text-slate-400">
          {vocabulary.length} 個單字
        </p>
      </div>

      {/* Score */}
      <div className="flex justify-center gap-4 mb-8">
        <div className="bg-emerald-500/20 border border-emerald-500/50 rounded-xl px-4 py-2">
          <span className="text-emerald-400 font-bold">{score.correct}</span>
          <span className="text-slate-400 text-sm ml-1">正確</span>
        </div>
        <div className="bg-slate-700/50 border border-slate-600 rounded-xl px-4 py-2">
          <span className="text-white font-bold">{score.total}</span>
          <span className="text-slate-400 text-sm ml-1">題目</span>
        </div>
        {score.total > 0 && (
          <div className="bg-amber-500/20 border border-amber-500/50 rounded-xl px-4 py-2">
            <span className="text-amber-400 font-bold">
              {Math.round((score.correct / score.total) * 100)}%
            </span>
            <span className="text-slate-400 text-sm ml-1">正確率</span>
          </div>
        )}
      </div>

      {/* MCQ Card */}
      {currentMcq ? (
        <EmojiMCQCard
          mcq={currentMcq}
          onAnswer={handleAnswer}
          showFeedback={true}
        />
      ) : (
        <div className="text-center text-slate-400">
          正在載入題目...
        </div>
      )}

      {/* Manual Next Button (for testing) */}
      <div className="text-center mt-8">
        <button
          onClick={generateNextMcq}
          className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-bold transition-colors"
        >
          下一題 →
        </button>
      </div>

      {/* Debug Info */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-8 p-4 bg-slate-800/50 rounded-xl text-xs text-slate-500">
          <p>Pack: {activePack?.id}</p>
          <p>Vocab count: {vocabulary.length}</p>
          <p>Current MCQ: {currentMcq?.id}</p>
        </div>
      )}
    </div>
  )
}


