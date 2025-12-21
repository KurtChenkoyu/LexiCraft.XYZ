'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useAppStore, selectLeaderboardData } from '@/stores/useAppStore'
import { Link } from '@/i18n/routing'
import { leaderboardsApi, LeaderboardEntry, UserRank } from '@/services/gamificationApi'

type Period = 'weekly' | 'monthly' | 'all_time'
type Metric = 'xp' | 'words' | 'streak'
type Tab = 'global' | 'friends'

const periodLabels: Record<Period, string> = {
  weekly: '本週',
  monthly: '本月',
  all_time: '總排行',
}

const metricLabels: Record<Metric, { label: string; icon: string }> = {
  xp: { label: '經驗值', icon: '⭐' },
  words: { label: '單字數', icon: '📚' },
  streak: { label: '連勝', icon: '⚡' },
}

// In-memory cache for leaderboard data (persists during session)
const leaderboardCache = new Map<string, { entries: LeaderboardEntry[], userRank: UserRank | null, timestamp: number }>()
const CACHE_TTL = 60000 // 1 minute cache

export default function LeaderboardsPage() {
  const { user } = useAuth()
  
  // ⚡ ZUSTAND-FIRST: Read from store (pre-loaded by Bootstrap)
  const leaderboardFromStore = useAppStore(selectLeaderboardData)
  const setLeaderboardInStore = useAppStore((state) => state.setLeaderboardData)

  const [tab, setTab] = useState<Tab>('global')
  const [period, setPeriod] = useState<Period>('weekly')
  const [metric, setMetric] = useState<Metric>('xp')
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [userRank, setUserRank] = useState<UserRank | null>(null)
  const [isFetching, setIsFetching] = useState(false)
  
  // Prevent double fetching
  const fetchingRef = useRef(false)
  
  // ⚡ INSTANT: Use Bootstrap data for initial render (weekly/xp)
  const hasUsedBootstrapData = useRef(false)
  useEffect(() => {
    if (hasUsedBootstrapData.current) return
    if (leaderboardFromStore && 
        leaderboardFromStore.period === 'weekly' && 
        leaderboardFromStore.metric === 'xp' &&
        tab === 'global' && period === 'weekly' && metric === 'xp') {
      console.log('⚡ Leaderboard: Using Bootstrap data (instant!)')
      setEntries(leaderboardFromStore.entries)
      setUserRank(leaderboardFromStore.userRank)
      hasUsedBootstrapData.current = true
      
      // Also populate the cache
      leaderboardCache.set('global-weekly-xp', {
        entries: leaderboardFromStore.entries,
        userRank: leaderboardFromStore.userRank,
        timestamp: leaderboardFromStore.timestamp
      })
    }
  }, [leaderboardFromStore, tab, period, metric])

  // Generate cache key
  const getCacheKey = useCallback(() => `${tab}-${period}-${metric}`, [tab, period, metric])

  // ⚡ INSTANT: Check cache first, then fetch in background
  useEffect(() => {
    if (!user) return

    const cacheKey = getCacheKey()
    const cached = leaderboardCache.get(cacheKey)
    const now = Date.now()

    // Use cache if valid (within TTL)
    if (cached && (now - cached.timestamp) < CACHE_TTL) {
      console.log('⚡ Leaderboard: Using cached data')
      setEntries(cached.entries)
      setUserRank(cached.userRank)
      setIsFetching(false)
      return
    }

    // Show cached data immediately if available (even if stale)
    if (cached) {
      console.log('⚡ Leaderboard: Showing stale cache while refreshing')
      setEntries(cached.entries)
      setUserRank(cached.userRank)
    }

    // Prevent double fetch
    if (fetchingRef.current) return
    fetchingRef.current = true
    setIsFetching(true)

    const fetchData = async () => {
      const [leaderboardData, rankData] = await Promise.all([
        tab === 'global'
          ? leaderboardsApi.getGlobal(period, 50, metric)
          : leaderboardsApi.getFriends(period, metric),
        leaderboardsApi.getRank(period, metric),
      ])

      // Update cache
      leaderboardCache.set(cacheKey, {
        entries: leaderboardData,
        userRank: rankData,
        timestamp: Date.now(),
      })

      setEntries(leaderboardData)
      setUserRank(rankData)
      setIsFetching(false)
      fetchingRef.current = false
      console.log('✅ Leaderboard: Fetched and cached')
    }

    fetchData()
    
    return () => {
      fetchingRef.current = false
    }
  }, [user, tab, period, metric, getCacheKey])

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 pt-20 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white flex items-center justify-center gap-3">
            🏆 排行榜
          </h1>
          <p className="text-white/60 mt-2">和其他學習者比較，看看你的排名</p>
        </div>

        {/* User's Rank Banner */}
        {userRank && (
          <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 backdrop-blur-xl rounded-2xl p-6 border border-yellow-500/30 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white/60 text-sm mb-1">你的排名</div>
                <div className="text-4xl font-bold text-yellow-400">#{userRank.rank}</div>
              </div>
              <div className="text-right">
                <div className="text-white/60 text-sm mb-1">{metricLabels[metric].label}</div>
                <div className="text-2xl font-bold text-white flex items-center gap-2">
                  <span>{metricLabels[metric].icon}</span>
                  {userRank.score.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setTab('global')}
            className={`flex-1 py-3 rounded-xl font-semibold transition-all ${
              tab === 'global'
                ? 'bg-white text-purple-900'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            🌍 全球排行
          </button>
          <button
            onClick={() => setTab('friends')}
            className={`flex-1 py-3 rounded-xl font-semibold transition-all ${
              tab === 'friends'
                ? 'bg-white text-purple-900'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            👥 朋友排行
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-8">
          {/* Period Filter */}
          <div className="flex bg-white/10 rounded-xl p-1">
            {(['weekly', 'monthly', 'all_time'] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  period === p ? 'bg-white text-purple-900' : 'text-white/80 hover:bg-white/10'
                }`}
              >
                {periodLabels[p]}
              </button>
            ))}
          </div>

          {/* Metric Filter */}
          <div className="flex bg-white/10 rounded-xl p-1">
            {(['xp', 'words', 'streak'] as Metric[]).map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-1 ${
                  metric === m ? 'bg-white text-purple-900' : 'text-white/80 hover:bg-white/10'
                }`}
              >
                <span>{metricLabels[m].icon}</span>
                {metricLabels[m].label}
              </button>
            ))}
          </div>
        </div>

        {/* Subtle background sync indicator - no spinner blocking the UI! */}
        {isFetching && entries.length > 0 && (
          <div className="mb-4 flex items-center justify-center gap-2 text-white/50 text-sm">
            <span className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
            更新中...
          </div>
        )}

        {/* Leaderboard - always show, empty is valid (no spinner!) */}
        {entries.length === 0 ? (
          <div className="bg-white/5 rounded-xl p-12 text-center border border-white/10">
            <div className="text-6xl mb-4">🏆</div>
            <p className="text-white/60 mb-2">
              {tab === 'friends' ? '還沒有朋友加入排行榜' : '暫無排行資料'}
            </p>
            {tab === 'friends' && (
              <p className="text-white/40 text-sm">邀請朋友一起學習吧！</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry, index) => (
              <LeaderboardRow
                key={entry.user_id}
                entry={entry}
                rank={entry.rank || index + 1}
                metric={metric}
              />
            ))}
          </div>
        )}

        {/* Back Link */}
        <div className="text-center mt-8">
          <Link href="/learner/profile" className="text-white/60 hover:text-white transition-colors">
            ← 返回個人資料
          </Link>
        </div>
      </div>
    </main>
  )
}

// Leaderboard Row Component
function LeaderboardRow({
  entry,
  rank,
  metric,
}: {
  entry: LeaderboardEntry
  rank: number
  metric: Metric
}) {
  const isTop3 = rank <= 3
  const isMe = entry.is_me

  const rankBadge = () => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return rank
  }

  return (
    <div
      className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
        isMe
          ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-2 border-yellow-500/50'
          : isTop3
          ? 'bg-white/15 border border-white/20'
          : 'bg-white/5 border border-white/10 hover:bg-white/10'
      }`}
    >
      {/* Rank */}
      <div
        className={`w-12 h-12 flex items-center justify-center rounded-full font-bold ${
          isTop3 ? 'text-3xl' : 'bg-white/10 text-white/80 text-lg'
        }`}
      >
        {rankBadge()}
      </div>

      {/* User Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`font-semibold truncate ${isMe ? 'text-yellow-400' : 'text-white'}`}>
            {entry.name}
          </span>
          {isMe && (
            <span className="px-2 py-0.5 bg-yellow-500/30 text-yellow-400 text-xs rounded-full">
              你
            </span>
          )}
        </div>
        {entry.current_streak > 0 && (
          <div className="text-white/40 text-sm flex items-center gap-1">
            ⚡ {entry.current_streak} 天連勝
          </div>
        )}
      </div>

      {/* Score */}
      <div className="text-right">
        <div className={`text-xl font-bold ${isMe ? 'text-yellow-400' : 'text-cyan-400'}`}>
          {entry.score.toLocaleString()}
        </div>
        <div className="text-white/40 text-xs">{metricLabels[metric].label}</div>
      </div>
    </div>
  )
}


