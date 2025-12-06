'use client'

import React, { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { MCQSession } from '@/components/features/mcq'

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
}

export default function VerificationPage() {
  const router = useRouter()
  const pathname = usePathname()
  const { user, session } = useAuth()
  const [dueCards, setDueCards] = useState<DueCard[]>([])
  const [isFetching, setIsFetching] = useState(false)
  const [selectedCard, setSelectedCard] = useState<DueCard | null>(null)
  const [isOffline, setIsOffline] = useState(false)

  const locale = pathname.split('/')[1] || 'zh-TW'

  // Background fetch - UI shows immediately (empty = all caught up!)
  useEffect(() => {
    if (!user || !session?.access_token) return

    const fetchDueCards = async () => {
      setIsFetching(true)
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/v1/verification/due?limit=20`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        })

        if (response.ok) {
          const cards: DueCard[] = await response.json()
          setDueCards(cards)
          setIsOffline(false)
        } else {
          setIsOffline(true)
        }
      } catch {
        setIsOffline(true)
      } finally {
        setIsFetching(false)
      }
    }

    fetchDueCards()
  }, [user, session])

  const handleCardSelect = (card: DueCard) => {
    setSelectedCard(card)
  }

  const handleSessionComplete = async (result: SessionResult) => {
    // Refresh due cards after completion
    if (!session?.access_token) return
    
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    try {
      const response = await fetch(`${apiUrl}/api/v1/verification/due?limit=20`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      })

      if (response.ok) {
        const cards: DueCard[] = await response.json()
        setDueCards(cards)
      }
    } catch (err) {
      console.error('Failed to refresh due cards:', err)
    }

    // Return to card list
    setSelectedCard(null)
  }

  const handleExit = () => {
    router.push(`/${locale}/mine`)
  }

  // If a card is selected, show MCQ session
  if (selectedCard) {
    // Extract sense_id from learning_point_id (format: "word.sense_id" or just "sense_id")
    const senseId = selectedCard.learning_point_id.includes('.')
      ? selectedCard.learning_point_id.split('.').slice(-2).join('.')  // Get last two parts
      : selectedCard.learning_point_id

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

  // ALWAYS show UI - never block on loading
  return (
    <main className="min-h-screen bg-gray-950 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-cyan-400 mb-2">複習驗證</h1>
          <p className="text-gray-400">
            根據間隔重複系統，以下是需要複習的單字
          </p>
        </div>

        {/* Status indicators */}
        {isOffline && (
          <div className="mb-4 flex items-center gap-2 text-amber-400/70 text-sm">
            <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
            離線模式 - 無法載入複習清單
          </div>
        )}
        {isFetching && (
          <div className="mb-4 flex items-center gap-2 text-gray-400 text-sm">
            <div className="w-4 h-4 border-2 border-gray-500 border-t-cyan-400 rounded-full animate-spin" />
            載入中...
          </div>
        )}

        {/* Due cards list - empty means all caught up! */}
        {dueCards.length === 0 ? (
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
        ) : (
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
