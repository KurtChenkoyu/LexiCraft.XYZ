'use client'

import React, { useState, useCallback, useEffect, useRef } from 'react'
import { MCQData, MCQResult, GamificationResult, AchievementUnlockedInfo } from '@/services/mcqApi'
import { audioService } from '@/lib/audio-service'
// Gamification overlays removed - rewards shown on completion screen only

// Re-export types for components that import from this file
export type { MCQData, MCQResult }

interface MCQCardProps {
  mcq: MCQData
  onSubmit: (
    mcqId: string,
    selectedIndex: number,
    responseTimeMs: number,
    selectedPoolIndex: number | null,
    servedOptionPoolIndices?: number[]
  ) => Promise<MCQResult>
  onNext?: () => void
  showDifficulty?: boolean
  autoAdvanceDelay?: number // ms to wait before auto-advancing (0 = manual)
}

const MCQCard: React.FC<MCQCardProps> = ({ 
  mcq, 
  onSubmit, 
  onNext,
  showDifficulty = false,
  autoAdvanceDelay = 1500 // Auto-advance after 1.5 seconds
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [selectedPoolIndex, setSelectedPoolIndex] = useState<number | null>(null)
  const [result, setResult] = useState<MCQResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [startTime] = useState<number>(Date.now())
  const autoAdvanceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const resultRef = useRef<HTMLDivElement>(null)
  
  // Gamification UI state
  // Gamification state removed - rewards shown on completion screen only

  // Reset state when MCQ changes
  useEffect(() => {
    setSelectedIndex(null)
    setSelectedPoolIndex(null)
    setResult(null)
    setIsSubmitting(false)
    // State reset removed - no gamification overlays to reset
    
    // Clear auto-advance timer
    if (autoAdvanceTimerRef.current) {
      clearTimeout(autoAdvanceTimerRef.current)
      autoAdvanceTimerRef.current = null
    }
    
    // Play prompt audio when MCQ loads (English only, offline)
    audioService.playPrompt('which_one_is_correct', 'instructions').catch(err => {
      console.warn('Failed to play prompt audio:', err)
    })
  }, [mcq.mcq_id])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (autoAdvanceTimerRef.current) {
        clearTimeout(autoAdvanceTimerRef.current)
      }
    }
  }, [])

  // Scroll to result when it appears
  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [result])

  // Select option (no auto-submit - need confirm button)
  const handleOptionClick = useCallback((index: number, poolIndex?: number | null) => {
    if (result || isSubmitting) return
    setSelectedIndex(index)
    setSelectedPoolIndex(poolIndex ?? null)
  }, [result, isSubmitting])

  // Confirm and submit answer
  // INSTANT FEEDBACK: If we have cached correct_index, show result immediately
  const handleConfirm = useCallback(async () => {
    if (selectedIndex === null || result || isSubmitting) return
    
    console.log('🔥 CONFIRM BUTTON CLICKED - selectedIndex:', selectedIndex)
    console.log('🔥 MCQ has correct_index?', mcq.correct_index !== undefined, 'value:', mcq.correct_index)
    
    setIsSubmitting(true)
    const responseTimeMs = Date.now() - startTime
    
    // Build served option pool indices, filtering out NaN values
    const rawIndices = mcq.options.map((o, idx) => {
      if (o.pool_index !== undefined && o.pool_index !== null) {
        const parsed = parseInt(String(o.pool_index), 10)
        return isNaN(parsed) ? idx : parsed
      }
      return idx
    })
    
    // Only send if we have valid indices (not all fallback)
    const hasValidPoolIndices = mcq.options.some(o => 
      o.pool_index !== undefined && 
      o.pool_index !== null && 
      !isNaN(parseInt(String(o.pool_index), 10))
    )
    
    const servedOptionPoolIndices = hasValidPoolIndices ? rawIndices : undefined
    
    // INSTANT: If we have cached correct_index, show feedback immediately
    const hasCachedAnswer = mcq.correct_index !== undefined && mcq.correct_index !== null
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🎯 Instant feedback check:', {
        has_correct_index: hasCachedAnswer,
        correct_index: mcq.correct_index,
        selected_index: selectedIndex,
        mcq_id: mcq.mcq_id
      })
    }
    
    if (hasCachedAnswer && mcq.correct_index !== undefined) {
      const isCorrect = selectedIndex === mcq.correct_index
      
      if (process.env.NODE_ENV === 'development') {
        console.log('⚡ INSTANT FEEDBACK:', isCorrect ? '✅ Correct!' : '❌ Wrong')
      }
      
      // Play audio feedback (English only, offline)
      if (isCorrect) {
        audioService.playCorrect()
        setTimeout(() => {
          audioService.playRandomFeedback('correct').catch(err => {
            console.warn('Failed to play feedback audio:', err)
          })
        }, 200)
      } else {
        audioService.playWrong()
        setTimeout(() => {
          audioService.playRandomFeedback('incorrect').catch(err => {
            console.warn('Failed to play feedback audio:', err)
          })
        }, 200)
      }
      
      // Show instant result - answer correctness only, rewards pending
      setResult({
        is_correct: isCorrect,
        correct_index: mcq.correct_index,
        feedback: isCorrect ? '答對了！' : '答錯了',
        explanation: '', // Will be updated when API responds
        ability_before: 0.5,
        ability_after: isCorrect ? 0.55 : 0.45,
        mcq_difficulty: null,  // Will be updated when API responds
        gamification: undefined,  // Will show "calculating..." until API responds
      })
      setIsSubmitting(false)  // Allow UI to update immediately (show answer feedback)
    } else {
      if (process.env.NODE_ENV === 'development') {
        console.log('⏳ No cached answer - waiting for API response')
      }
    }
    
    // BACKGROUND: Submit to server for gamification (fire-and-forget for cached)
    try {
      const submitResult = await onSubmit(
        mcq.mcq_id,
        selectedIndex,
        responseTimeMs,
        selectedPoolIndex,
        servedOptionPoolIndices
      )
      
      // Update with server result (or set if not cached)
      if (!hasCachedAnswer) {
        setResult(submitResult)
        setIsSubmitting(false)
      } else if (submitResult.gamification) {
        // Update gamification data from server
        setResult(prev => prev ? { ...prev, gamification: submitResult.gamification } : submitResult)
      }
      
      // Don't show gamification feedback during questions
      // Save it all for the completion screen (the "feel good moment")
      
      // No auto-advance - user clicks "Next" when ready
    } catch (error) {
      console.error('Failed to submit MCQ answer:', error)
      // If we already showed instant result, just log the error
      // If not, we need to show error state
      if (!hasCachedAnswer) {
        setIsSubmitting(false)
      }
    }
  }, [selectedIndex, result, isSubmitting, startTime, mcq.mcq_id, mcq.correct_index, onSubmit, autoAdvanceDelay, onNext])

  // Cancel auto-advance and go to next immediately
  const handleNextClick = useCallback(() => {
    if (autoAdvanceTimerRef.current) {
      clearTimeout(autoAdvanceTimerRef.current)
      autoAdvanceTimerRef.current = null
    }
    onNext?.()
  }, [onNext])

  const getOptionStyle = (index: number) => {
    const baseStyle = 'w-full p-4 text-left border rounded-xl transition-all duration-150 active:scale-[0.98] '
    
    if (result) {
      // After submission - show correct/incorrect
      if (index === result.correct_index) {
        return baseStyle + 'border-emerald-500 bg-emerald-500/20 text-emerald-300 shadow-lg shadow-emerald-500/20'
      }
      if (index === selectedIndex && !result.is_correct) {
        return baseStyle + 'border-red-500 bg-red-500/20 text-red-300 shadow-lg shadow-red-500/20'
      }
      return baseStyle + 'border-gray-700/50 bg-gray-900/30 text-gray-500 opacity-50'
    }
    
    // While submitting - show selection with loading state
    if (isSubmitting && index === selectedIndex) {
      return baseStyle + 'border-cyan-400 bg-cyan-500/30 text-cyan-300 ring-2 ring-cyan-400/50 animate-pulse'
    }
    
    // Before submission - interactive state
    if (index === selectedIndex) {
      return baseStyle + 'border-cyan-400 bg-cyan-500/20 text-cyan-300 ring-2 ring-cyan-400/50'
    }
    
    return baseStyle + 'border-gray-700 bg-gray-900/80 text-gray-300 hover:border-cyan-600 hover:bg-gray-800/80 cursor-pointer'
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'meaning': return '意思'
      case 'usage': return '用法'
      case 'discrimination': return '辨別'
      default: return type
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'meaning': return 'text-purple-400 border-purple-500/50'
      case 'usage': return 'text-amber-400 border-amber-500/50'
      case 'discrimination': return 'text-emerald-400 border-emerald-500/50'
      default: return 'text-gray-400 border-gray-500/50'
    }
  }

  const gamification = result?.gamification

  // Defensive check - accept 4-6 options (minimum 4 for valid MCQ)
  if (mcq.options.length < 4 || mcq.options.length > 6) {
    console.warn(`MCQ ${mcq.mcq_id} has ${mcq.options.length} options (expected 4-6)`)
    // Still render, but log warning for debugging
  }

  if (mcq.correct_index !== undefined && 
      (mcq.correct_index < 0 || mcq.correct_index >= mcq.options.length)) {
    console.error(`MCQ ${mcq.mcq_id} has invalid correct_index: ${mcq.correct_index}`)
    // Disable instant feedback if correct_index is invalid
  }

  return (
    <div className="w-full max-w-2xl mx-auto bg-gray-900/90 backdrop-blur border border-gray-700 rounded-2xl p-6 shadow-2xl">
      {/* Header with XP Badge */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-cyan-400">{mcq.word}</span>
          <span className={`px-2 py-0.5 text-xs border rounded ${getTypeColor(mcq.mcq_type)}`}>
            {getTypeLabel(mcq.mcq_type)}
          </span>
        </div>
        {/* Floating XP indicator */}
        {!result && (
          <div className="px-3 py-1 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500/30 rounded-full text-sm font-medium text-yellow-400 flex items-center gap-1">
            <span>⚡</span>
            <span>+10 XP</span>
          </div>
        )}
      </div>

      {/* Context (if any) */}
      {mcq.context && (
        <div className="mb-4 p-3 bg-gray-800/50 border border-gray-700 rounded-lg">
          <div className="text-xs text-gray-500 mb-1">📖 句子</div>
          <div className="text-gray-200 italic">{mcq.context}</div>
        </div>
      )}

      {/* Question */}
      <div className="mb-6">
        <h3 className="text-lg text-gray-100 font-medium">{mcq.question}</h3>
      </div>

      {/* Options - Tap to select, then confirm */}
      <div className="space-y-2 mb-4">
        {mcq.options.map((option, index) => (
          <button
            key={option.pool_index ?? index}
            onClick={() => handleOptionClick(index, option.pool_index)}
            disabled={!!result || isSubmitting}
            className={getOptionStyle(index)}
          >
            <div className="flex items-start gap-3">
              <span className={`flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full text-sm font-mono transition-colors ${
                result?.correct_index === index 
                  ? 'bg-emerald-500 text-white' 
                  : selectedIndex === index && result && !result.is_correct
                    ? 'bg-red-500 text-white'
                    : selectedIndex === index
                      ? 'bg-cyan-500 text-white'
                      : 'bg-gray-800 text-gray-400'
              }`}>
                {String.fromCharCode(65 + index)}
              </span>
              <span className="flex-1">{option.text}</span>
              {/* Checkmark for correct, X for wrong */}
              {result && index === result.correct_index && (
                <span className="text-emerald-400 text-xl">✓</span>
              )}
              {result && index === selectedIndex && !result.is_correct && (
                <span className="text-red-400 text-xl">✗</span>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Confirm Button - Shows when option selected but not submitted */}
      {!result && (
        <button
          onClick={handleConfirm}
          disabled={selectedIndex === null || isSubmitting}
          className={`w-full py-3 rounded-xl font-bold text-lg transition-all duration-150 mb-4 ${
            selectedIndex === null
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
              : isSubmitting
                ? 'bg-cyan-700 text-cyan-300 animate-pulse'
                : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-500/30 active:scale-[0.98]'
          }`}
        >
          {isSubmitting ? '確認中...' : '確認答案'}
        </button>
      )}

      {/* Result Feedback - Scrolls into view */}
      {result && (
        <div ref={resultRef} className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
          {/* Result Banner */}
          <div className={`p-3 rounded-lg border flex items-center gap-3 ${
            result.is_correct 
              ? 'bg-emerald-500/10 border-emerald-500/50' 
              : 'bg-red-500/10 border-red-500/50'
          }`}>
            <span className="text-2xl">{result.is_correct ? '✅' : '❌'}</span>
            <div className="flex-1">
              <span className={`font-bold ${result.is_correct ? 'text-emerald-400' : 'text-red-400'}`}>
                {result.feedback}
              </span>
              {result.explanation && (
                <p className="text-sm text-gray-400 mt-1">{result.explanation}</p>
              )}
            </div>
          </div>

          {/* Streak Banner */}
          {gamification?.streak_extended && (
            <div className="bg-gradient-to-r from-orange-500/20 to-amber-500/20 border border-orange-500/30 rounded-lg px-3 py-2 flex items-center gap-2 text-sm">
              <span className="text-xl">🔥</span>
              <span className="text-orange-400 font-medium">連勝 +1! 目前 {gamification.streak_days} 天</span>
            </div>
          )}

          {/* NO rewards shown during questions - save for completion screen */}

          {/* NO progress bar during questions */}

          {/* NO ability change during questions */}

          {/* Next Button - Always enabled, don't wait for API */}
          {onNext && (
            <button
              onClick={handleNextClick}
              className="w-full py-3 rounded-xl font-bold text-lg transition-all duration-150 shadow-lg bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-500/25 active:scale-[0.98]"
            >
              下一題 →
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default MCQCard
