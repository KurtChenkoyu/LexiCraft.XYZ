'use client'

import React, { useState, useCallback, useEffect } from 'react'

interface MCQOption {
  text: string
  source: string
}

interface MCQData {
  mcq_id: string
  sense_id: string
  word: string
  mcq_type: string
  question: string
  context: string | null
  options: MCQOption[]
  user_ability: number
  mcq_difficulty: number | null
  selection_reason: string
}

interface MCQResult {
  is_correct: boolean
  correct_index: number
  explanation: string
  feedback: string
  ability_before: number
  ability_after: number
  mcq_difficulty: number | null
}

interface MCQCardProps {
  mcq: MCQData
  onSubmit: (mcqId: string, selectedIndex: number, responseTimeMs: number) => Promise<MCQResult>
  onNext?: () => void
  showDifficulty?: boolean
}

const MCQCard: React.FC<MCQCardProps> = ({ 
  mcq, 
  onSubmit, 
  onNext,
  showDifficulty = false 
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [result, setResult] = useState<MCQResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [startTime] = useState<number>(Date.now())

  // Reset state when MCQ changes
  useEffect(() => {
    setSelectedIndex(null)
    setResult(null)
    setIsSubmitting(false)
  }, [mcq.mcq_id])

  const handleOptionSelect = useCallback((index: number) => {
    if (result) return // Already submitted
    setSelectedIndex(index)
  }, [result])

  const handleSubmit = useCallback(async () => {
    if (selectedIndex === null || isSubmitting || result) return
    
    setIsSubmitting(true)
    try {
      const responseTimeMs = Date.now() - startTime
      const submitResult = await onSubmit(mcq.mcq_id, selectedIndex, responseTimeMs)
      setResult(submitResult)
    } catch (error) {
      console.error('Failed to submit MCQ answer:', error)
    } finally {
      setIsSubmitting(false)
    }
  }, [selectedIndex, isSubmitting, result, startTime, mcq.mcq_id, onSubmit])

  const getOptionStyle = (index: number) => {
    const baseStyle = 'w-full p-4 text-left border rounded-lg transition-all duration-200 '
    
    if (result) {
      // After submission - show correct/incorrect
      if (index === result.correct_index) {
        return baseStyle + 'border-emerald-500 bg-emerald-500/20 text-emerald-300'
      }
      if (index === selectedIndex && !result.is_correct) {
        return baseStyle + 'border-red-500 bg-red-500/20 text-red-300'
      }
      return baseStyle + 'border-gray-700 bg-gray-900/50 text-gray-500 opacity-60'
    }
    
    // Before submission
    if (index === selectedIndex) {
      return baseStyle + 'border-cyan-400 bg-cyan-500/20 text-cyan-300 ring-2 ring-cyan-400/50'
    }
    
    return baseStyle + 'border-gray-700 bg-gray-900/80 text-gray-300 hover:border-cyan-600 hover:bg-gray-800'
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

  return (
    <div className="w-full max-w-2xl mx-auto bg-gray-900/90 backdrop-blur border border-gray-700 rounded-2xl p-6 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-cyan-400">{mcq.word}</span>
          <span className={`px-2 py-0.5 text-xs border rounded ${getTypeColor(mcq.mcq_type)}`}>
            {getTypeLabel(mcq.mcq_type)}
          </span>
        </div>
        {showDifficulty && mcq.mcq_difficulty !== null && (
          <div className="text-xs text-gray-500">
            難度: {(mcq.mcq_difficulty * 100).toFixed(0)}%
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

      {/* Options */}
      <div className="space-y-3 mb-6">
        {mcq.options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionSelect(index)}
            disabled={!!result || isSubmitting}
            className={getOptionStyle(index)}
          >
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-gray-800 text-sm font-mono">
                {String.fromCharCode(65 + index)}
              </span>
              <span className="flex-1">{option.text}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Submit Button */}
      {!result && (
        <button
          onClick={handleSubmit}
          disabled={selectedIndex === null || isSubmitting}
          className={`w-full py-3 rounded-lg font-medium transition-all duration-200 ${
            selectedIndex === null || isSubmitting
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
              : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-500/25'
          }`}
        >
          {isSubmitting ? (
            <span className="animate-pulse">確認中...</span>
          ) : (
            '確認答案'
          )}
        </button>
      )}

      {/* Result Feedback */}
      {result && (
        <div className="space-y-4">
          {/* Correct/Incorrect Badge */}
          <div className={`p-4 rounded-lg border ${
            result.is_correct 
              ? 'bg-emerald-500/10 border-emerald-500/50' 
              : 'bg-red-500/10 border-red-500/50'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              {result.is_correct ? (
                <span className="text-2xl">✅</span>
              ) : (
                <span className="text-2xl">❌</span>
              )}
              <span className={`text-lg font-bold ${
                result.is_correct ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {result.feedback}
              </span>
            </div>
            
            {/* Explanation */}
            {result.explanation && (
              <div className="text-sm text-gray-300 mt-2">
                {result.explanation}
              </div>
            )}
          </div>

          {/* Ability Change */}
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>能力變化:</span>
            <span className={
              result.ability_after > result.ability_before 
                ? 'text-emerald-400' 
                : result.ability_after < result.ability_before 
                  ? 'text-red-400' 
                  : 'text-gray-400'
            }>
              {(result.ability_before * 100).toFixed(0)}% → {(result.ability_after * 100).toFixed(0)}%
              {result.ability_after > result.ability_before && ' ↑'}
              {result.ability_after < result.ability_before && ' ↓'}
            </span>
          </div>

          {/* Next Button */}
          {onNext && (
            <button
              onClick={onNext}
              className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium transition-all duration-200 shadow-lg shadow-cyan-500/25"
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

