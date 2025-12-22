'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import MCQCard from './MCQCard'
import { mcqApi, MCQData, MCQResult } from '@/services/mcqApi'
import { localStore } from '@/lib/local-store'
import { bundleCacheService } from '@/services/bundleCacheService'
import { downloadService } from '@/services/downloadService'
import { useAppStore } from '@/stores/useAppStore'

/**
 * Normalize sense ID by stripping _N suffix
 * e.g., "be.v.01_0" -> "be.v.01"
 */
function normalizeSenseId(senseId: string): string {
  // Pattern: word.pos.NN_NN -> word.pos.NN
  const match = senseId.match(/^(.+\.\w+\.\d+)_\d+$/)
  return match ? match[1] : senseId
}

/**
 * Calculate level from total XP (client-side, matches backend formula)
 * Level 1: 0-99 XP, Level 2: 100-249 XP, Level 3: 250-449 XP, etc.
 * XP needed for level N = 100 + (N-1) * 50
 */
function calculateLevelFromXP(totalXp: number): { level: number; xpInLevel: number; xpToNext: number; progress: number } {
  let level = 1
  let xpNeeded = 100
  let remainingXp = totalXp
  
  while (remainingXp >= xpNeeded) {
    level++
    remainingXp -= xpNeeded
    xpNeeded = 100 + (level - 1) * 50
  }
  
  return {
    level,
    xpInLevel: remainingXp,
    xpToNext: xpNeeded,
    progress: Math.round((remainingXp / xpNeeded) * 100)
  }
}

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
  totalXpEarned: number
  totalPointsEarned: number
}

const MCQSession: React.FC<MCQSessionProps> = ({
  senseId: rawSenseId,
  word,
  count = 3,
  verificationScheduleId,
  onComplete,
  onExit,
  authToken,
}) => {
  // Normalize sense ID (strip _N suffix) for MCQ lookup
  const senseId = useMemo(() => normalizeSenseId(rawSenseId), [rawSenseId])
  
  // Start as 'pending' - only show loading UI after 150ms (avoid flicker for cached data)
  const [status, setStatus] = useState<'pending' | 'loading' | 'active' | 'complete' | 'error'>('pending')
  const [mcqs, setMcqs] = useState<MCQData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [results, setResults] = useState<MCQResult[]>([])
  const [errorMessage, setErrorMessage] = useState<string>('')
  // Collect answers for batch submission
  const [pendingAnswers, setPendingAnswers] = useState<Array<{
    mcqId: string
    selectedIndex: number
    responseTimeMs: number
    selectedPoolIndex: number | null
    servedOptionPoolIndices?: number[]
    // Store instant result for immediate feedback
    instantResult?: MCQResult
    // FAST PATH: Include data so backend skips DB fetch
    isCorrect?: boolean
    senseId?: string
    correctIndex?: number
  }>>([])
  const [isSubmittingBatch, setIsSubmittingBatch] = useState(false)
  // Cached user XP for delta calculations
  const [cachedUserXp, setCachedUserXp] = useState<number>(0)
  
  // Load cached user XP on mount
  useEffect(() => {
    const loadCachedXp = async () => {
      try {
        const profile = await downloadService.getLearnerProfile()
        if (profile?.level?.total_xp) {
          setCachedUserXp(profile.level.total_xp)
          console.log('📊 Cached user XP:', profile.level.total_xp)
        }
      } catch (e) {
        console.warn('Could not load cached XP:', e)
      }
    }
    loadCachedXp()
  }, [])

  // Set auth token and load MCQs
  // CACHE-FIRST: Try IndexedDB first (~10ms), fallback to API
  useEffect(() => {
    // Set auth token first
    if (authToken) {
      mcqApi.setAuthToken(authToken)
    }

    const loadMCQs = async () => {
      try {
        // Deferred loading: Only show loading UI after 150ms (avoids flicker for cached data)
        const loadingTimeout = setTimeout(() => setStatus('loading'), 150)
        
        console.log(`🔍 Loading MCQs for ${senseId} (raw: ${rawSenseId})`)
        
        // 1. Try IndexedDB cache first (INSTANT, ~10ms)
        // This is wrapped in try-catch because IndexedDB might not be upgraded yet
        let bundle = null
        try {
          bundle = await localStore.getVerificationBundle(senseId)
        } catch (cacheError) {
          console.warn('Cache lookup failed (non-critical):', cacheError)
        }
        
        if (bundle?.mcqs && bundle.mcqs.length >= count) {
          // Validate cached MCQs (defensive check)
          const validMcqs = bundle.mcqs.slice(0, count).filter(m => {
            // Accept 4-6 options (minimum 4 for valid MCQ)
            if (m.options.length < 4 || m.options.length > 6) {
              console.warn(`MCQ ${m.mcq_id} has ${m.options.length} options (expected 4-6), version=${bundle.version || 'unknown'}`)
              return false
            }
            if (m.correct_index < 0 || m.correct_index >= m.options.length) {
              console.warn(`MCQ ${m.mcq_id} has invalid correct_index: ${m.correct_index}, version=${bundle.version || 'unknown'}`)
              return false
            }
            return true
          })
          
          if (validMcqs.length >= count) {
            // Map to MCQData format
            const cachedMcqs: MCQData[] = validMcqs.slice(0, count).map(m => ({
            mcq_id: m.mcq_id,
            sense_id: senseId,
            word: bundle.word,
            mcq_type: m.mcq_type,
            question: m.question,
            context: m.context,
            options: m.options,
              correct_index: m.correct_index,
            user_ability: 0.5,
            mcq_difficulty: null,
            selection_reason: 'cached',
          }))
          console.log(`⚡ Loaded ${cachedMcqs.length} MCQs from cache`)
            clearTimeout(loadingTimeout)
          setMcqs(cachedMcqs)
          setStatus('active')
          return
          } else {
            console.warn(`Only ${validMcqs.length}/${count} valid MCQs in cache, falling back to API`)
          }
        }
        
        // 2. If cache miss, try to pre-cache this sense on the fly
        if (authToken) {
          try {
            await bundleCacheService.preCacheBundles([senseId], authToken)
            const cachedAfterPrefetch = await localStore.getVerificationBundle(senseId)
            if (cachedAfterPrefetch?.mcqs && cachedAfterPrefetch.mcqs.length >= count) {
              // Validate cached MCQs (defensive check)
              const validMcqs = cachedAfterPrefetch.mcqs.slice(0, count).filter(m => {
                // Accept 4-6 options (minimum 4 for valid MCQ)
                if (m.options.length < 4 || m.options.length > 6) {
                  console.warn(`MCQ ${m.mcq_id} has ${m.options.length} options (expected 4-6), version=${cachedAfterPrefetch.version || 'unknown'}`)
                  return false
                }
                if (m.correct_index < 0 || m.correct_index >= m.options.length) {
                  console.warn(`MCQ ${m.mcq_id} has invalid correct_index: ${m.correct_index}, version=${cachedAfterPrefetch.version || 'unknown'}`)
                  return false
                }
                return true
              })
              
              if (validMcqs.length >= count) {
                const cachedMcqs: MCQData[] = validMcqs.slice(0, count).map(m => ({
                mcq_id: m.mcq_id,
                sense_id: senseId,
                word: cachedAfterPrefetch.word,
                mcq_type: m.mcq_type,
                question: m.question,
                context: m.context,
                options: m.options,
                correct_index: m.correct_index,
                user_ability: 0.5,
                mcq_difficulty: null,
                selection_reason: 'cached',
              }))
              console.log(`⚡ Loaded ${cachedMcqs.length} MCQs from cache after prefetch`)
                clearTimeout(loadingTimeout)
              setMcqs(cachedMcqs)
              setStatus('active')
              return
              } else {
                console.warn(`Only ${validMcqs.length}/${count} valid MCQs in cache after prefetch, falling back to API`)
              }
            }
          } catch (prefetchError) {
            console.warn('On-demand pre-cache failed (non-critical):', prefetchError)
          }
        }
        
        // 3. Fallback to API (if cache miss or cache unavailable)
        if (!authToken) {
          console.warn('No auth token and no cached MCQs')
          clearTimeout(loadingTimeout)
          setErrorMessage('請先登入 / Authentication required')
          setStatus('error')
          return
        }

        console.log(`📡 Fetching MCQs from API for ${senseId} (cache miss)`)
        const mcqData = await mcqApi.getMCQSession(senseId, count)
        
        if (mcqData.length === 0) {
          throw new Error(`No MCQs available for sense ${senseId}`)
        }
        
        clearTimeout(loadingTimeout)
        setMcqs(mcqData)
        setStatus('active')
      } catch (error) {
        console.error('Failed to load MCQs:', error)
        setErrorMessage(error instanceof Error ? error.message : 'Unknown error')
        setStatus('error')
      }
    }

    loadMCQs()
  }, [senseId, rawSenseId, count, authToken])

  const handleSubmit = useCallback(async (
    mcqId: string,
    selectedIndex: number,
    responseTimeMs: number,
    selectedPoolIndex: number | null,
    servedOptionPoolIndices?: number[]
  ): Promise<MCQResult> => {
    // Get current MCQ for instant feedback
    const currentMcq = mcqs[currentIndex]
    const hasCachedAnswer = currentMcq?.correct_index !== undefined && currentMcq?.correct_index !== null
    
    // Create instant result from cache (for immediate UI feedback)
    let instantResult: MCQResult | undefined
    if (hasCachedAnswer && currentMcq) {
      const isCorrect = selectedIndex === currentMcq.correct_index
      instantResult = {
        is_correct: isCorrect,
        correct_index: currentMcq.correct_index ?? 0,
        explanation: '',
        feedback: isCorrect ? '答對了！' : '答錯了',
        ability_before: 0.5,
        ability_after: isCorrect ? 0.55 : 0.45,
        mcq_difficulty: null,
        gamification: undefined, // Will be updated from batch response
      }
      // Add instant result to results for immediate UI update
      setResults(prev => [...prev, instantResult!])
    }
    
    // Collect answer for batch submission (don't submit yet)
    // Include FAST PATH data so backend skips DB fetch (~50ms vs ~1500ms)
    setPendingAnswers(prev => [...prev, {
      mcqId, 
      selectedIndex, 
      responseTimeMs,
      selectedPoolIndex,
      servedOptionPoolIndices,
      instantResult,
      // FAST PATH data - backend skips DB fetch when these are provided
      isCorrect: instantResult?.is_correct,
      senseId: currentMcq?.sense_id,
      correctIndex: currentMcq?.correct_index,
    }])
    
    // Return instant result if available, otherwise return a placeholder
    return instantResult || {
      is_correct: false,
      correct_index: -1,
      explanation: '',
      feedback: '處理中...',
      ability_before: 0.5,
      ability_after: 0.5,
      mcq_difficulty: null,
    }
  }, [verificationScheduleId, mcqs, currentIndex])

  const handleNext = useCallback(async () => {
    if (currentIndex + 1 >= mcqs.length) {
      // Last question - submit batch and show completion screen
      
      // IMMEDIATELY show completion screen with instant stats
      const localCorrect = results.filter(r => r.is_correct).length
      const sessionResult: SessionResult = {
        total: mcqs.length,
        correct: localCorrect,
        accuracy: mcqs.length > 0 ? (localCorrect / mcqs.length) * 100 : 0,
        abilityChange: results.length > 0 
          ? results[results.length - 1].ability_after - results[0].ability_before
          : 0,
        totalXpEarned: 0, // Will update from batch response
        totalPointsEarned: 0, // Will update from batch response
      }
      
      setStatus('complete')
      onComplete?.(sessionResult)
      
      // Submit all answers in batch (non-blocking)
      // Wait a tiny bit to ensure last answer is collected
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // Check if we have answers to submit
      // Wait a bit more and check again - the last answer might still be collecting
      let attempts = 0
      while (pendingAnswers.length < results.length && attempts < 5) {
        await new Promise(resolve => setTimeout(resolve, 200))
        attempts++
      }
      
      if (pendingAnswers.length === 0) {
        console.warn('No pending answers to submit - answers may not have been collected')
        console.warn('Results count:', results.length, 'Pending answers:', pendingAnswers.length)
        // If we have results but no pending answers, something went wrong
        // But we can still show the completion screen with instant results
        setIsSubmittingBatch(false)
        return
      }
      
      if (pendingAnswers.length !== results.length) {
        console.warn(`Mismatch: ${results.length} results but ${pendingAnswers.length} pending answers`)
        // Continue anyway - submit what we have
      }
      
      setIsSubmittingBatch(true)
      
      // Add timeout to prevent hanging
      const timeoutId = setTimeout(() => {
        console.warn('Batch submission timeout - clearing submission state')
        setIsSubmittingBatch(false)
      }, 60000) // 60 second timeout (batch is now fast, this is just safety)
      
      try {
        console.log(`📦 Submitting batch of ${pendingAnswers.length} answers`)
        const batchResults = await mcqApi.submitBatchAnswers(
          pendingAnswers.map(answer => ({
            mcqId: answer.mcqId,
            selectedIndex: answer.selectedIndex,
            responseTimeMs: answer.responseTimeMs,
            verificationScheduleId: verificationScheduleId,
            selectedPoolIndex: answer.selectedPoolIndex ?? undefined,
            servedOptionPoolIndices: answer.servedOptionPoolIndices,
            // FAST PATH: Include data so backend skips DB fetch (~50ms vs ~1500ms)
            isCorrect: answer.isCorrect,
            senseId: answer.senseId,
            correctIndex: answer.correctIndex,
          }))
        )
        
        clearTimeout(timeoutId)
        console.log(`✅ Batch submission complete: ${batchResults.length} results`)
        
        // Update results with server responses (merge with instant results)
        setResults(prev => {
          const updated = [...prev]
          batchResults.forEach((batchResult, index) => {
            if (updated[index]) {
              // Merge server gamification data with instant result
              updated[index] = {
                ...updated[index],
                ...batchResult,
                // Keep instant feedback but update with server data
                gamification: batchResult.gamification,
              }
            } else {
              updated[index] = batchResult
            }
          })
          return updated
        })
        
        // Update session result with final totals
        const finalXp = batchResults.reduce((sum, r) => sum + (r.gamification?.xp_gained || 0), 0)
        const finalPoints = batchResults.reduce((sum, r) => sum + (r.gamification?.points_earned || 0), 0)
        const finalCorrect = batchResults.filter(r => r.is_correct).length
        
        // Apply deltas to global store (Delta Strategy - instant UI update)
        const sparksGained = batchResults.reduce((sum, r) => sum + (r.gamification?.sparks_gained || 0), 0)
        const essenceGained = batchResults.reduce((sum, r) => sum + (r.gamification?.essence_gained || 0), 0)
        useAppStore.getState().applyDelta({
          delta_xp: finalXp,
          delta_points: finalPoints,
          delta_sparks: sparksGained,
          delta_essence: essenceGained,
        })
        
        const finalSessionResult: SessionResult = {
          total: mcqs.length,
          correct: finalCorrect,
          accuracy: mcqs.length > 0 ? (finalCorrect / mcqs.length) * 100 : 0,
          abilityChange: batchResults.length > 0 
            ? batchResults[batchResults.length - 1].ability_after - batchResults[0].ability_before
            : 0,
          totalXpEarned: finalXp,
          totalPointsEarned: finalPoints,
        }
        
        // Call onComplete again with final data
        onComplete?.(finalSessionResult)
      } catch (error) {
        clearTimeout(timeoutId)
        console.error('❌ Failed to submit batch answers:', error)
        // Keep instant results even if batch fails
        // Show error but don't block UI
      } finally {
        setIsSubmittingBatch(false)
      }
    } else {
      setCurrentIndex(prev => prev + 1)
    }
  }, [currentIndex, mcqs.length, results, onComplete, pendingAnswers, verificationScheduleId])

  // Loading state - 'pending' shows minimal skeleton (waiting for cache check)
  // 'loading' shows full loading UI (only after 150ms delay for API fetch)
  if (status === 'pending') {
    // Show subtle skeleton for first 150ms (avoids flicker for cached data)
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    )
  }
  
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

  // Complete state - ALWAYS show, update progressively
  if (status === 'complete') {
    const allResultsLoaded = results.length === mcqs.length
    const allGamificationLoaded = results.every(r => r.gamification !== undefined)
    const pendingCount = mcqs.length - results.length
    
    // Calculate from what we have (instant feedback from MCQCard)
    const totalCorrect = results.filter(r => r.is_correct).length
    const accuracy = mcqs.length > 0 ? (totalCorrect / mcqs.length) * 100 : 0
    
    // Progressive XP/Points (update as API responds)
    const totalXpEarned = results.reduce(
      (sum, r) => sum + (r.gamification?.xp_gained || 0), 
      0
    )
    const totalPointsEarned = results.reduce(
      (sum, r) => sum + (r.gamification?.points_earned || 0), 
      0
    )
    
    const latestGamification = results[results.length - 1]?.gamification
    
    // Determine what backend is doing
    const getBackendStatus = () => {
      // Show batch submission status
      if (isSubmittingBatch) {
        return {
          message: `批次提交 ${pendingAnswers.length} 題答案...`,
          details: [
            '處理所有答案',
            '計算間隔重複排程',
            '更新學習進度',
            '計算 XP 與點數'
          ]
        }
      }
      
      if (pendingCount > 0) {
        return {
          message: `處理中 ${mcqs.length - pendingCount}/${mcqs.length} 題目...`,
          details: [
            '計算間隔重複排程',
            '更新學習進度',
            '計算 XP 與點數',
            '檢查成就解鎖'
          ]
        }
      }
      
      // Check if achievements are still processing in background
      const achievementsProcessing = results.some(r => r.gamification?.sync_status === 'processing')
      
      // Only show status if we have some gamification data or are still processing
      // Don't hang if we have no data at all
      if (allGamificationLoaded && !achievementsProcessing) {
        return null // All done, hide status
      }
      
      if (!allGamificationLoaded || achievementsProcessing) {
        return {
          message: '計算最終獎勵...',
          details: [
            allGamificationLoaded ? '✓ 間隔重複排程完成' : '間隔重複排程',
            allGamificationLoaded ? '✓ 學習進度已更新' : '更新學習進度',
            allGamificationLoaded ? '✓ XP 與點數已計算' : '計算 XP 與點數',
            achievementsProcessing ? '檢查成就解鎖中...' : (allGamificationLoaded ? '✓ 完成' : '處理中...')
          ]
        }
      }
      return null
    }
    
    const backendStatus = getBackendStatus()

    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-gray-900/90 border border-gray-700 rounded-2xl p-8 text-center">
          {/* Header */}
          <div className="text-4xl mb-4">
            {accuracy >= 100 ? '🏆' : accuracy >= 70 ? '🎉' : accuracy >= 50 ? '👍' : '💪'}
          </div>
          <h2 className="text-2xl font-bold text-cyan-400 mb-2">測驗完成！</h2>
          <p className="text-gray-400 mb-6">{word || senseId}</p>

          {/* Stats - INSTANT (from local state) */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-3xl font-bold text-emerald-400">{totalCorrect}</div>
              <div className="text-sm text-gray-500">答對題數</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-3xl font-bold text-cyan-400">{mcqs.length}</div>
              <div className="text-sm text-gray-500">總題數</div>
            </div>
          </div>
          
          {/* Accuracy Bar - INSTANT */}
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
          
          {/* Backend Status Indicator */}
          {backendStatus && (
            <div className="mb-6 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
              <div className="flex items-center justify-center gap-2 mb-2">
                <div className="w-3 h-3 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm font-medium text-cyan-400">{backendStatus.message}</span>
              </div>
              <div className="text-left space-y-1 mt-3">
                {backendStatus.details.map((detail, idx) => (
                  <div key={idx} className="text-xs text-gray-400 flex items-center gap-2">
                    <span className={detail.startsWith('✓') ? 'text-emerald-400' : 'text-cyan-400'}>
                      {detail.startsWith('✓') ? '✓' : '○'}
                    </span>
                    <span>{detail.replace('✓ ', '')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Gamification Summary - PROGRESSIVE */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border border-yellow-500/30 rounded-lg p-4">
              {totalXpEarned > 0 ? (
                <>
                  <div className="text-3xl font-bold text-yellow-400">
                    +{totalXpEarned}
                  </div>
                  <div className="text-sm text-gray-400">XP 獲得</div>
                </>
              ) : (
                <>
                  <div className="text-sm text-yellow-400/60 flex items-center justify-center gap-2">
                    <div className="w-3 h-3 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin"></div>
                    計算中
                  </div>
                  <div className="text-xs text-gray-500 mt-1">XP</div>
                </>
              )}
            </div>
            <div className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 rounded-lg p-4">
              {totalPointsEarned > 0 ? (
                <>
                  <div className="text-3xl font-bold text-emerald-400">
                    +${totalPointsEarned}
                  </div>
                  <div className="text-sm text-gray-400">點數獲得</div>
                </>
              ) : (
                <>
                  <div className="text-sm text-emerald-400/60 flex items-center justify-center gap-2">
                    <div className="w-3 h-3 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                    計算中
                  </div>
                  <div className="text-xs text-gray-500 mt-1">點數</div>
                </>
              )}
            </div>
          </div>
          
          {/* Level Progress - DELTA STRATEGY (cached XP + earned XP) */}
          {(() => {
            // Calculate level from cached XP + XP earned this session
            const newTotalXp = cachedUserXp + totalXpEarned
            const levelInfo = calculateLevelFromXP(newTotalXp)
            return (
            <div className="mb-6 p-3 bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-lg">
              <div className="flex justify-between text-sm mb-2">
                  <span className="text-purple-400 font-bold">Level {levelInfo.level}</span>
                <span className="text-gray-400">
                    {levelInfo.xpInLevel} / {levelInfo.xpToNext} XP
                </span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                    style={{ width: `${levelInfo.progress}%` }}
                />
              </div>
            </div>
            )
          })()}

          {/* Ability Change - Hidden (confusing to users) */}
          {false && (() => {
            const abilityChange = 0 // Hidden feature - not displayed
            return (
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
            )
          })()}

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

      {/* MCQ Card - Manual advance (user controls pace) */}
      <MCQCard
        key={currentMCQ.mcq_id} // Force remount for clean state
        mcq={currentMCQ}
        onSubmit={handleSubmit}
        onNext={handleNext}
        showDifficulty={false}
        autoAdvanceDelay={0} // No auto-advance - user clicks "Next" button
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

