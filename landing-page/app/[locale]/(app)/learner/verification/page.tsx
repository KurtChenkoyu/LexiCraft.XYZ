'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import {
  useAppStore,
  selectDueCards,
  selectActivePack,
  selectMineBlocks,
  selectActiveLearner,
  selectEmojiVocabulary,
} from '@/stores/useAppStore'
import { MCQSession } from '@/components/features/mcq'
import { EmojiMCQSession } from '@/components/features/mcq/EmojiMCQSession'
import { bundleCacheService } from '@/services/bundleCacheService'
import type { EmojiMCQ } from '@/lib/pack-types'
import { downloadService } from '@/services/downloadService'

interface DueCard {
  verification_schedule_id: number
  learning_progress_id: number
  learning_point_id: string
  word: string | null
  scheduled_date: string
  days_overdue: number
  mastery_level: string
  retention_predicted: number | null
}

interface SessionResult {
  total: number
  correct: number
  accuracy: number
  abilityChange: number
  totalXpEarned: number
  totalPointsEarned: number
}

export default function VerificationPage() {
  const router = useRouter()
  const pathname = usePathname()
  const { user, session } = useAuth()
  
  // ⚡ ZUSTAND-FIRST: Read from store (pre-loaded by Bootstrap)
  const dueCardsFromStore = useAppStore(selectDueCards)
  const setDueCardsInStore = useAppStore((state) => state.setDueCards)
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  
  // 📦 Check active pack for emoji mode
  const activePack = useAppStore(selectActivePack)
  const activeLearner = useAppStore(selectActiveLearner)
  const mineBlocks = useAppStore(selectMineBlocks)
  const emojiVocabulary = useAppStore(selectEmojiVocabulary)
  const isEmojiPack = activePack?.id === 'emoji_core'
  
  // ⚡ CACHE-FIRST: Initialize with Zustand data immediately (prevents "no words" flash)
  const [dueCards, setDueCards] = useState<DueCard[]>(dueCardsFromStore || [])
  
  // Get emoji words to verify (SRS due cards only, filtered to emoji pack)
  const emojiWordsToVerify = useMemo(() => {
    if (!isEmojiPack) return []

    // Only filter when emojiVocabulary is loaded
    const shouldFilter = emojiVocabulary && emojiVocabulary.length > 0
    const validEmojiIds = shouldFilter
      ? new Set(emojiVocabulary.map((w) => w.sense_id))
      : new Set<string>()

    // 1) Restrict due cards to emoji pack senseIds
    const emojiDueCards = dueCards.filter((card) => {
      if (!card.learning_point_id) return false
      if (!shouldFilter) return true
      return validEmojiIds.has(card.learning_point_id)
    })

    // 2) The verification list is exactly the emoji due-card IDs
    return emojiDueCards.map((card) => card.learning_point_id)
  }, [isEmojiPack, emojiVocabulary, dueCards])
  const [isFetching, setIsFetching] = useState(false)
  const [selectedCard, setSelectedCard] = useState<DueCard | null>(null)
  const [isOffline, setIsOffline] = useState(false)
  const [showEmojiSession, setShowEmojiSession] = useState(false)
  const [preGeneratedMcqs, setPreGeneratedMcqs] = useState<EmojiMCQ[]>([])

  const locale = pathname.split('/')[1] || 'zh-TW'

  // Debug: log key verification state for current learner
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 Verification state', {
        learnerId: activeLearner?.id,
        dueCardsCount: dueCards.length,
        emojiWordsToVerifyCount: emojiWordsToVerify.length,
      })
    }
  }, [
    activeLearner?.id,
    dueCards.length,
    emojiWordsToVerify.length,
  ])

  // ⚡ CACHE-FIRST: Always use Zustand data immediately (even if empty)
  // This prevents the "no words" flash
  // Include activeLearner?.id to ensure sync on learner switches
  useEffect(() => {
    if (dueCardsFromStore !== undefined) {
      setDueCards(dueCardsFromStore)
      if (process.env.NODE_ENV === 'development') {
        console.log(`⚡ Verification: Using Zustand data (${dueCardsFromStore.length} cards) for learner ${activeLearner?.id}`)
      }
    }
  }, [dueCardsFromStore, activeLearner?.id])

  // Background refresh - only if Zustand is empty or learner changed
  // Uses learner-scoped downloadService + guards to avoid stale updates
  // Follows cache priority: Zustand → IndexedDB → API
  useEffect(() => {
    const learnerId = activeLearner?.id
    if (!user || !session?.access_token || !learnerId) return

    // Skip fetch if we already have data for this learner
    const shouldFetch = !dueCardsFromStore || dueCardsFromStore.length === 0
    if (!shouldFetch && dueCards.length > 0) {
      console.log('⚡ Verification: Skipping fetch - using cached Zustand data')
      return
    }

    const learnerIdAtStart = learnerId
    let cancelled = false

    const loadDueCards = async () => {
      setIsFetching(true)
      try {
        // CRITICAL FIX: Use getLearnerDueCards() which follows cache priority (IndexedDB → API)
        // This loads instantly from IndexedDB if available, then syncs from API in background
        // Only use refreshLearnerDueCards() for explicit refreshes (after session complete)
        const freshCards = await downloadService.getLearnerDueCards(learnerIdAtStart)
        if (cancelled) return

        // Guard: only apply if learner is still active
        const current = useAppStore.getState()
        if (current.activeLearner?.id !== learnerIdAtStart) {
          if (process.env.NODE_ENV === 'development') {
            console.log(
              '⏭️ Skipping dueCards update for stale learner',
              learnerIdAtStart,
              '(current =',
              current.activeLearner?.id,
              ')',
            )
          }
          return
        }

        // Update state with cached or fresh data (may be empty array - that's valid!)
        // getLearnerDueCards returns undefined if no cache and API fails, [] if API returns empty
        if (freshCards !== undefined) {
          setDueCards(freshCards)
          setDueCardsInStore(freshCards)
          setIsOffline(false)
        } else {
          // No data from cache or API - mark as offline
          setIsOffline(true)
        }
      } catch (error) {
        console.debug('Failed to load due cards:', error)
        setIsOffline(true)
      } finally {
        if (!cancelled) {
          setIsFetching(false)
        }
      }
    }

    // Only fetch in background (non-blocking)
    loadDueCards()

    return () => {
      cancelled = true
    }
  }, [user, session?.access_token, activeLearner?.id, dueCardsFromStore, dueCards.length, setDueCardsInStore])

  // Pre-cache verification bundles for all due cards (makes MCQ loads instant)
  useEffect(() => {
    if (!session?.access_token || dueCards.length === 0) return
    const senseIds = dueCards.map(c => c.learning_point_id)
    bundleCacheService.preCacheBundles(senseIds, session.access_token)
  }, [dueCards, session?.access_token])

  // Pre-generate questions in background when emojiWordsToVerify changes
  // This makes clicking "Start" instant (no delay)
  useEffect(() => {
    if (!isEmojiPack || emojiWordsToVerify.length === 0) {
      setPreGeneratedMcqs([])
      return
    }
    
    // Generate questions in background (non-blocking)
    const generateQuestions = async () => {
      try {
        const { packLoader } = await import('@/lib/pack-loader')
        const mcqs = await packLoader.generateMCQBatch('emoji_core', emojiWordsToVerify, 1)
        // Shuffle (generateMCQBatch already shuffles, but ensure it's done)
        const shuffled = mcqs.sort(() => Math.random() - 0.5)
        setPreGeneratedMcqs(shuffled)
        console.log(`⚡ Pre-generated ${shuffled.length} MCQs in background`)
      } catch (error) {
        console.warn('Failed to pre-generate MCQs:', error)
        setPreGeneratedMcqs([]) // Fallback to on-demand generation
      }
    }
    
    generateQuestions()
  }, [isEmojiPack, emojiWordsToVerify])

  const handleCardSelect = (card: DueCard) => {
    setSelectedCard(card)
  }

  const handleSessionComplete = (result: SessionResult) => {
    // Refresh due cards in background (don't wait, don't close screen)
    const learnerId = activeLearner?.id
    if (!session?.access_token || !learnerId) return

    const learnerIdAtStart = learnerId

    // Fire and forget - don't await
    downloadService.refreshLearnerDueCards(learnerIdAtStart)
      .then((freshCards) => {
        const current = useAppStore.getState()
        if (current.activeLearner?.id !== learnerIdAtStart) {
          if (process.env.NODE_ENV === 'development') {
            console.log(
              '⏭️ Skipping dueCards refresh after session for stale learner',
              learnerIdAtStart,
              '(current =',
              current.activeLearner?.id,
              ')',
            )
          }
          return
        }

        if (freshCards) {
          const { setDueCards: setStoreDueCards } = current
          setDueCards(freshCards)
          setStoreDueCards(freshCards)
        }
      })
      .catch((err) => {
        console.error('Failed to refresh due cards after session:', err)
      })

    // DON'T auto-close - let user click "完成" button to exit
    // The onExit callback will handle closing
  }

  const handleExit = () => {
    // Close the MCQ session and return to card list
    setSelectedCard(null)
  }

  // 🎯 Emoji Pack: Show emoji MCQ session
  if (isEmojiPack && showEmojiSession && emojiWordsToVerify.length > 0) {
    return (
      <main className="min-h-screen bg-gray-950 pt-top-nav">
        <div className="max-w-md mx-auto">
          <EmojiMCQSession
            senseIds={emojiWordsToVerify}
            packId="emoji_core"
            preGeneratedMcqs={preGeneratedMcqs}
            onComplete={(result) => {
              console.log('Emoji session complete:', result)
              
              // Extract verified words and call completeVerification
              const verifiedWords = result.verifiedWords.map(v => ({
                senseId: v.senseId,
                isCorrect: v.isCorrect
              }))
              
              const { completeVerification } = useAppStore.getState()
              completeVerification(verifiedWords)
              
              setShowEmojiSession(false)
            }}
            onExit={() => setShowEmojiSession(false)}
          />
        </div>
      </main>
    )
  }
  
  // Legacy: If a card is selected, show MCQ session
  if (selectedCard) {
    // The learning_point_id IS the sense_id (e.g., "drop.n.02", "active.a.05")
    // Just use it directly - no transformation needed
    const senseId = selectedCard.learning_point_id

    return (
      <main className="min-h-screen bg-gray-950">
        <MCQSession
          senseId={senseId}
          word={selectedCard.word || undefined}
          count={3}
          verificationScheduleId={selectedCard.verification_schedule_id}
          onComplete={handleSessionComplete}
          onExit={() => setSelectedCard(null)}
          authToken={session?.access_token || undefined}
        />
      </main>
    )
  }

  // Count urgent (overdue) vs scheduled
  const urgentCards = dueCards.filter(c => c.days_overdue > 0)
  const scheduledCards = dueCards.filter(c => c.days_overdue <= 0)

  // Show loading state ONLY if we have no cached data AND are fetching
  // Don't show spinner if we have cached data (even if empty - that means "no cards due")
  // The condition !dueCardsFromStore distinguishes between "empty list" vs "no data yet"
  if (dueCards.length === 0 && isBootstrapped && isFetching && !dueCardsFromStore) {
    return (
      <main className="min-h-screen bg-gray-950 pt-top-nav py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">載入複習清單中...</p>
          </div>
        </div>
      </main>
    )
  }

  // ALWAYS show UI - never block on loading
  return (
    <main className="min-h-screen bg-gray-950 pt-top-nav py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header with stats */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-cyan-400 mb-2">複習驗證</h1>
          {activeLearner && (
            <p className="text-sm text-slate-400 mb-1">
              驗證對象: <span className="font-medium text-slate-300">{activeLearner.display_name}</span>
            </p>
          )}
          <p className="text-gray-400">
            {isEmojiPack 
              ? '驗證你已鍛造的表情符號單字'
              : '根據間隔重複系統，以下是需要複習的單字'
            }
          </p>
          
          {/* Stats row */}
          {isEmojiPack ? (
            <div className="flex gap-4 mt-4">
              <div className="px-3 py-1 bg-cyan-500/20 border border-cyan-500/40 rounded-lg">
                <span className="text-cyan-400 font-medium">📚 {emojiWordsToVerify.length} 待驗證</span>
              </div>
            </div>
          ) : dueCards.length > 0 && (
            <div className="flex gap-4 mt-4">
              {urgentCards.length > 0 && (
                <div className="px-3 py-1 bg-red-500/20 border border-red-500/40 rounded-lg">
                  <span className="text-red-400 font-medium">🔥 {urgentCards.length} 緊急</span>
                </div>
              )}
              <div className="px-3 py-1 bg-cyan-500/20 border border-cyan-500/40 rounded-lg">
                <span className="text-cyan-400 font-medium">📚 {dueCards.length} 待驗證</span>
              </div>
            </div>
          )}
        </div>

        {/* 🎯 Emoji Pack: Start verification button */}
        {isEmojiPack && (
          <div className="mb-6">
            {emojiWordsToVerify.length > 0 ? (
              <button
                onClick={() => setShowEmojiSession(true)}
                className="w-full py-4 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white rounded-xl font-bold text-lg transition-all shadow-lg shadow-cyan-500/20"
              >
                🎯 開始表情配對 ({emojiWordsToVerify.length} 題)
              </button>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📭</div>
                <h2 className="text-2xl font-bold text-gray-300 mb-2">沒有需要驗證的單字</h2>
                <p className="text-gray-500 mb-4">先去礦區鍛造一些單字吧！</p>
                <button
                  onClick={() => router.push(`/${locale}/learner/mine`)}
                  className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors"
                >
                  前往礦區
                </button>
              </div>
            )}
          </div>
        )}

        {/* Legacy: Batch verification buttons */}
        {!isEmojiPack && dueCards.length > 0 && (
          <div className="flex flex-wrap gap-3 mb-6">
            {urgentCards.length > 0 && (
              <button
                onClick={() => setSelectedCard(urgentCards[0])}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium transition-all shadow-lg shadow-red-500/20"
              >
                🔥 先驗證緊急 ({urgentCards.length})
              </button>
            )}
            <button
              onClick={() => setSelectedCard(dueCards[0])}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium transition-all shadow-lg shadow-cyan-500/20"
            >
              📝 開始全部驗證 ({dueCards.length})
            </button>
          </div>
        )}

        {/* Status indicators */}
        {isOffline && (
          <div className="mb-4 flex items-center gap-2 text-amber-400/70 text-sm">
            <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
            離線模式 - 無法載入複習清單
          </div>
        )}
        {/* Only show loading indicator if we have no data yet (not if we're just syncing in background) */}
        {isFetching && dueCards.length === 0 && !dueCardsFromStore && (
          <div className="mb-4 flex items-center gap-2 text-gray-400 text-sm">
            <div className="w-4 h-4 border-2 border-gray-500 border-t-cyan-400 rounded-full animate-spin" />
            載入中...
          </div>
        )}

        {/* Due cards list - empty means all caught up! (Legacy only) */}
        {!isEmojiPack && dueCards.length === 0 && !isFetching ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-300 mb-2">沒有需要複習的單字</h2>
            <p className="text-gray-500">所有單字都在複習間隔內，做得好！</p>
            <button
              onClick={handleExit}
              className="mt-6 px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors"
            >
              前往礦區
            </button>
          </div>
        ) : !isEmojiPack && (
          <div className="space-y-4">
            {dueCards.map((card) => (
              <button
                key={card.learning_progress_id}
                onClick={() => handleCardSelect(card)}
                className="w-full p-6 bg-gray-900/80 border border-gray-700 rounded-lg hover:border-cyan-500 hover:bg-gray-800 transition-all text-left"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-bold text-cyan-400">
                        {card.word || card.learning_point_id}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded ${
                        card.mastery_level === 'mastered' ? 'bg-emerald-500/20 text-emerald-400' :
                        card.mastery_level === 'known' ? 'bg-blue-500/20 text-blue-400' :
                        card.mastery_level === 'familiar' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {card.mastery_level}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      {card.days_overdue > 0 && (
                        <span className="text-red-400">
                          逾期 {card.days_overdue} 天
                        </span>
                      )}
                      {card.retention_predicted !== null && (
                        <span>
                          預測留存率: {(card.retention_predicted * 100).toFixed(0)}%
                        </span>
                      )}
                      <span>
                        排程日期: {new Date(card.scheduled_date).toLocaleDateString('zh-TW')}
                      </span>
                    </div>
                  </div>
                  <div className="text-cyan-400 text-2xl">→</div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Back button */}
        <div className="mt-8 text-center">
          <button
            onClick={handleExit}
            className="px-6 py-2 border border-gray-600 text-gray-400 rounded-lg hover:bg-gray-800 transition-colors"
          >
            前往礦區
          </button>
        </div>
      </div>
    </main>
  )
}
