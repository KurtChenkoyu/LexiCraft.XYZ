'use client'

import React, { useState, useEffect, useCallback } from 'react'
import MCQCard from './MCQCard'
import { mcqApi, MCQData, MCQResult } from '@/services/mcqApi'

interface MCQSessionProps {
  senseId: string
  word?: string
  count?: number
  verificationScheduleId?: number
  onComplete?: (results: SessionResult) => void
  onExit?: () => void
  authToken?: string
}

interface SessionResult {
  total: number
  correct: number
  accuracy: number
  abilityChange: number
}

const MCQSession: React.FC<MCQSessionProps> = ({
  senseId,
  word,
  count = 3,
  verificationScheduleId,
  onComplete,
  onExit,
  authToken,
}) => {
  const [status, setStatus] = useState<'loading' | 'active' | 'complete' | 'error'>('loading')
  const [mcqs, setMcqs] = useState<MCQData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [results, setResults] = useState<MCQResult[]>([])
  const [errorMessage, setErrorMessage] = useState<string>('')

  // Set auth token if provided
  useEffect(() => {
    if (authToken) {
      mcqApi.setAuthToken(authToken)
    }
  }, [authToken])

  // Load MCQs on mount
  useEffect(() => {
    const loadMCQs = async () => {
      try {
        setStatus('loading')
        const mcqData = await mcqApi.getMCQSession(senseId, count)
        
        if (mcqData.length === 0) {
          throw new Error('No MCQs available for this word')
        }
        
        setMcqs(mcqData)
        setStatus('active')
      } catch (error) {
        console.error('Failed to load MCQs:', error)
        setErrorMessage(error instanceof Error ? error.message : 'Unknown error')
        setStatus('error')
      }
    }

    loadMCQs()
  }, [senseId, count])

  const handleSubmit = useCallback(async (
    mcqId: string,
    selectedIndex: number,
    responseTimeMs: number
  ): Promise<MCQResult> => {
    const result = await mcqApi.submitAnswer(
      mcqId, 
      selectedIndex, 
      responseTimeMs,
      verificationScheduleId
    )
    setResults(prev => [...prev, result])
    return result
  }, [verificationScheduleId])

  const handleNext = useCallback(() => {
    if (currentIndex + 1 >= mcqs.length) {
      // Session complete
      const totalCorrect = results.filter(r => r.is_correct).length
      const sessionResult: SessionResult = {
        total: results.length,
        correct: totalCorrect,
        accuracy: totalCorrect / results.length,
        abilityChange: results.length > 0 
          ? results[results.length - 1].ability_after - results[0].ability_before
          : 0,
      }
      setStatus('complete')
      onComplete?.(sessionResult)
    } else {
      setCurrentIndex(prev => prev + 1)
    }
  }, [currentIndex, mcqs.length, results, onComplete])

  // Loading state
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-cyan-400 text-xl font-mono animate-pulse mb-4">
            載入題目中...
          </div>
          <div className="text-gray-500 text-sm">
            準備 {word || senseId} 的驗證題目
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <div className="text-red-500 text-2xl mb-4">⚠️</div>
          <h2 className="text-xl text-red-400 font-bold mb-2">載入失敗</h2>
          <p className="text-gray-400 mb-6">{errorMessage}</p>
          <div className="flex gap-3 justify-center">
            {onExit && (
              <button
                onClick={onExit}
                className="px-4 py-2 border border-gray-600 text-gray-400 rounded-lg hover:bg-gray-800"
              >
                返回
              </button>
            )}
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-500"
            >
              重試
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Complete state
  if (status === 'complete') {
    const totalCorrect = results.filter(r => r.is_correct).length
    const accuracy = (totalCorrect / results.length) * 100
    const abilityChange = results.length > 0 
      ? results[results.length - 1].ability_after - results[0].ability_before
      : 0

    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-gray-900/90 border border-gray-700 rounded-2xl p-8 text-center">
          {/* Header */}
          <div className="text-4xl mb-4">
            {accuracy >= 100 ? '🏆' : accuracy >= 70 ? '🎉' : accuracy >= 50 ? '👍' : '💪'}
          </div>
          <h2 className="text-2xl font-bold text-cyan-400 mb-2">測驗完成！</h2>
          <p className="text-gray-400 mb-6">{word || senseId}</p>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-3xl font-bold text-emerald-400">{totalCorrect}</div>
              <div className="text-sm text-gray-500">答對題數</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-3xl font-bold text-cyan-400">{results.length}</div>
              <div className="text-sm text-gray-500">總題數</div>
            </div>
          </div>

          {/* Accuracy Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">正確率</span>
              <span className={accuracy >= 70 ? 'text-emerald-400' : 'text-amber-400'}>
                {accuracy.toFixed(0)}%
              </span>
            </div>
            <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  accuracy >= 70 ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
                style={{ width: `${accuracy}%` }}
              />
            </div>
          </div>

          {/* Ability Change */}
          <div className="mb-6 p-3 bg-gray-800/50 rounded-lg">
            <div className="text-sm text-gray-400 mb-1">能力變化</div>
            <div className={`text-lg font-bold ${
              abilityChange > 0 ? 'text-emerald-400' : 
              abilityChange < 0 ? 'text-red-400' : 'text-gray-400'
            }`}>
              {abilityChange > 0 ? '+' : ''}{(abilityChange * 100).toFixed(1)}%
              {abilityChange > 0 ? ' ↑' : abilityChange < 0 ? ' ↓' : ''}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            {onExit && (
              <button
                onClick={onExit}
                className="flex-1 py-3 border border-gray-600 text-gray-400 rounded-lg hover:bg-gray-800"
              >
                完成
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Active state - show current MCQ
  const currentMCQ = mcqs[currentIndex]

  return (
    <div className="min-h-screen bg-gray-950 py-8 px-4">
      {/* Progress */}
      <div className="max-w-2xl mx-auto mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">
            題目 {currentIndex + 1} / {mcqs.length}
          </span>
          <span className="text-sm text-gray-500">
            {results.filter(r => r.is_correct).length} 正確
          </span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-cyan-500 transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / mcqs.length) * 100}%` }}
          />
        </div>
      </div>

      {/* MCQ Card */}
      <MCQCard
        mcq={currentMCQ}
        onSubmit={handleSubmit}
        onNext={handleNext}
        showDifficulty={false}
      />

      {/* Exit Button */}
      {onExit && (
        <div className="max-w-2xl mx-auto mt-6 text-center">
          <button
            onClick={onExit}
            className="text-sm text-gray-500 hover:text-gray-400"
          >
            暫停測驗
          </button>
        </div>
      )}
    </div>
  )
}

export default MCQSession

