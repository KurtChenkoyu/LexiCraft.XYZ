'use client'

import { Link } from '@/i18n/routing'
import { useRolePreference } from '@/hooks/useRolePreference'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export function ProfileQuickActions() {
  const { isParent, canSwitchRoles, currentRole, setRole } = useRolePreference()
  const router = useRouter()
  const { signOut } = useAuth()

  const handleSwitchToParent = () => {
    setRole('parent')
    router.push('/parent/dashboard')
  }

  const handleSwitchToMiner = () => {
    setRole('learner')
    router.push('/learner/mine')
  }

  // Determine if we're currently in miner mode (default) or parent mode
  const isInMinerMode = currentRole === 'learner' || currentRole !== 'parent'

  return (
    <div className="mt-8 space-y-6">
      {/* Quick Actions */}
      <div className="flex flex-wrap justify-center gap-4">
        <Link
          href="/parent/goals"
          className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition-all"
        >
          🎯 設定目標
        </Link>
        <Link
          href="/learner/leaderboards"
          className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl text-white font-semibold hover:shadow-lg hover:shadow-purple-500/30 transition-all"
        >
          🏆 排行榜
        </Link>
        <Link
          href="/learner/verification"
          className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl text-white font-semibold hover:shadow-lg hover:shadow-green-500/30 transition-all"
        >
          📖 開始學習
        </Link>
      </div>

      {/* Role Switcher - Only show if user has parent role */}
      {isParent && (
        <div className="max-w-md mx-auto bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
          <h3 className="text-white/80 text-sm font-medium mb-3 text-center">切換視圖</h3>
          <div className="flex gap-3 justify-center">
            {isInMinerMode ? (
              <button
                onClick={handleSwitchToParent}
                className="flex items-center gap-2 px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 rounded-lg text-amber-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <span>切換到家長控制台</span>
              </button>
            ) : (
              <button
                onClick={handleSwitchToMiner}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-lg text-cyan-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                </svg>
                <span>切換到礦工模式</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Settings & Logout */}
      <div className="flex justify-center gap-4 pt-4 border-t border-white/10">
        <Link
          href="/parent/settings"
          className="px-4 py-2 text-white/60 hover:text-white/80 transition-colors text-sm"
        >
          ⚙️ 設定
        </Link>
        <button
          onClick={signOut}
          className="px-4 py-2 text-white/60 hover:text-red-400 transition-colors text-sm"
        >
          🚪 登出
        </button>
      </div>
    </div>
  )
}

