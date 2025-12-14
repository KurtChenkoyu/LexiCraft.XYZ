'use client'

import { useAppStore, selectUser, selectLearnerProfile, selectProgress } from '@/stores/useAppStore'
import { Link } from '@/i18n/routing'

/**
 * Learner Home Page - The "World Map"
 * 
 * The main landing page for learners - shows the "City" view or Map.
 * This is the base layer that other activities slide over.
 * 
 * ARCHITECTURE: Reads exclusively from Zustand (zero fetchers)
 * Data was pre-loaded by Bootstrap at /start
 * 
 * URL: /learner/home
 * 
 * @see .cursorrules - "Zero-Latency" principle
 */
export default function LearnerHomePage() {
  // ⚡ Instant reads from Zustand (no API calls, no loading states)
  const user = useAppStore(selectUser)
  const learnerProfile = useAppStore(selectLearnerProfile)
  const progress = useAppStore(selectProgress)
  
  // Extract data with fallbacks
  const userName = user?.name || '學習者'
  const level = learnerProfile?.level?.level || 1
  const currentStreak = learnerProfile?.current_streak || 0
  const totalWords = progress.total_discovered || 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 text-white">
      {/* Header */}
      <div className="text-center py-8">
        <h1 className="text-3xl font-black mb-2">
          歡迎回來, {userName}! 👋
        </h1>
        <p className="text-white/70">準備好今天的學習冒險了嗎？</p>
        <div className="mt-2 inline-block bg-white/10 px-4 py-1 rounded-full text-sm">
          等級 {level}
        </div>
      </div>

      {/* Quick Stats - Now with REAL data from Zustand! */}
      <div className="grid grid-cols-2 gap-4 px-4 mb-8">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-4 border border-white/20">
          <div className="text-3xl mb-1">🔥</div>
          <div className="text-2xl font-bold">{currentStreak}</div>
          <div className="text-sm text-white/70">連勝天數</div>
        </div>
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-4 border border-white/20">
          <div className="text-3xl mb-1">📚</div>
          <div className="text-2xl font-bold">{totalWords}</div>
          <div className="text-sm text-white/70">掌握單字</div>
        </div>
      </div>

      {/* Main Actions */}
      <div className="px-4 space-y-4">
        <Link
          href="/learner/mine"
          className="block bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl p-6 shadow-lg shadow-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/40 transition-all"
        >
          <div className="flex items-center gap-4">
            <div className="text-5xl">⛏️</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold mb-1">挖礦區</h2>
              <p className="text-white/80 text-sm">發現新單字，擴展你的詞彙量</p>
            </div>
            <div className="text-2xl">→</div>
          </div>
        </Link>

        <Link
          href="/learner/verification"
          className="block bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl p-6 shadow-lg shadow-purple-500/30 hover:shadow-xl hover:shadow-purple-500/40 transition-all"
        >
          <div className="flex items-center gap-4">
            <div className="text-5xl">✅</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold mb-1">驗證區</h2>
              <p className="text-white/80 text-sm">測試你的記憶，鞏固學習成果</p>
            </div>
            <div className="text-2xl">→</div>
          </div>
        </Link>

        <Link
          href="/learner/build"
          className="block bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl p-6 shadow-lg shadow-amber-500/30 hover:shadow-xl hover:shadow-amber-500/40 transition-all"
        >
          <div className="flex items-center gap-4">
            <div className="text-5xl">🏗️</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold mb-1">建造區</h2>
              <p className="text-white/80 text-sm">使用你的資源建造城市</p>
            </div>
            <div className="text-2xl">→</div>
          </div>
        </Link>

        <Link
          href="/learner/leaderboards"
          className="block bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all"
        >
          <div className="flex items-center gap-4">
            <div className="text-5xl">🏆</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold mb-1">排行榜</h2>
              <p className="text-white/80 text-sm">看看你的排名</p>
            </div>
            <div className="text-2xl">→</div>
          </div>
        </Link>
      </div>

      {/* Bottom spacing for nav */}
      <div className="h-24" />
    </div>
  )
}

