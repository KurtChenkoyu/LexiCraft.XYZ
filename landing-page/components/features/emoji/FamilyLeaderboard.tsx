'use client'

import { useState, useEffect } from 'react'
import { useAppStore, selectLearnersSummaries, selectUser } from '@/stores/useAppStore'
import { downloadService } from '@/services/downloadService'

interface FamilyMember {
  id: string
  name: string
  type: 'parent' | 'child'
  level: number
  total_xp: number
  weekly_xp: number  // XP earned in last 7 days
  monthly_xp: number  // XP earned in last 30 days
  current_streak: number
  vocabulary_size: number
  words_learned_this_week: number
}

/**
 * FamilyLeaderboard - Family score aggregation for emoji pack
 * 
 * Shows:
 * - Aggregate family scores (sum or average)
 * - Per-child breakdown
 * - Sibling competition view
 * - Weekly/monthly stats
 */
export function FamilyLeaderboard() {
  const user = useAppStore(selectUser)
  const learnersSummaries = useAppStore(selectLearnersSummaries)
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly')
  
  // DEBUG: Log store state
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 FamilyLeaderboard: Component mounted/updated', {
        isBootstrapped,
        learnersSummariesLength: learnersSummaries?.length || 0,
        learnersSummaries: learnersSummaries,
        user: user?.id
      })
    }
  }, [isBootstrapped, learnersSummaries, user])
  
  // Load family data
  useEffect(() => {
    const loadFamilyData = async () => {
      // Don't load until bootstrap is complete
      if (!isBootstrapped) {
        if (process.env.NODE_ENV === 'development') {
          console.log('🔍 FamilyLeaderboard: Waiting for bootstrap to complete...')
        }
        return
      }
      
      setLoading(true)
      try {
        // DEBUG: Log what we're receiving
        console.log('🔍 FamilyLeaderboard: loadFamilyData called', {
          learnersSummariesLength: learnersSummaries?.length || 0,
          learnersSummaries: learnersSummaries,
          isBootstrapped
        })
        
        const members: FamilyMember[] = []
        
        // Add all learners from summaries (includes parent + children)
        if (learnersSummaries && learnersSummaries.length > 0) {
          console.log(`✅ FamilyLeaderboard: Processing ${learnersSummaries.length} learners`)
          learnersSummaries.forEach(summary => {
            console.log('🔍 FamilyLeaderboard: Processing summary:', {
              learner_id: summary.learner_id,
              display_name: summary.display_name,
              total_xp: summary.total_xp,
              level: summary.level,
              vocabulary_size: summary.vocabulary_size,
              current_streak: summary.current_streak
            })
            members.push({
              id: summary.learner_id,
              name: summary.display_name,
              type: summary.is_parent_profile ? 'parent' : 'child',
              level: summary.level,
              total_xp: summary.total_xp,  // All-time XP
              weekly_xp: summary.weekly_xp || 0,  // XP earned in last 7 days
              monthly_xp: summary.monthly_xp || 0,  // XP earned in last 30 days
              current_streak: summary.current_streak,
              vocabulary_size: summary.vocabulary_size,
              words_learned_this_week: summary.words_learned_this_week,
            })
          })
        } else {
          console.warn('⚠️ FamilyLeaderboard: learnersSummaries is empty or undefined', {
            learnersSummaries,
            isBootstrapped
          })
          // Try to manually fetch if store is empty
          if (isBootstrapped) {
            console.log('🔄 FamilyLeaderboard: Store is empty, attempting manual fetch...')
            try {
              const { downloadService } = await import('@/services/downloadService')
              const freshSummaries = await downloadService.getLearnersSummaries(true)
              if (freshSummaries && freshSummaries.length > 0) {
                const { useAppStore } = await import('@/stores/useAppStore')
                useAppStore.getState().setLearnersSummaries(freshSummaries)
                console.log(`✅ FamilyLeaderboard: Manually fetched ${freshSummaries.length} learners summaries`)
                // Re-process with fresh data
                freshSummaries.forEach(summary => {
                  members.push({
                    id: summary.learner_id,
                    name: summary.display_name,
                    type: summary.is_parent_profile ? 'parent' : 'child',
                    level: summary.level,
                    total_xp: summary.total_xp,
                    weekly_xp: summary.weekly_xp || 0,
                    monthly_xp: summary.monthly_xp || 0,
                    current_streak: summary.current_streak,
                    vocabulary_size: summary.vocabulary_size,
                    words_learned_this_week: summary.words_learned_this_week,
                  })
                })
              }
            } catch (fetchError) {
              console.error('❌ FamilyLeaderboard: Failed to manually fetch learners summaries:', fetchError)
            }
          }
        }
        
        // Sort by period-based XP (descending)
        members.sort((a, b) => {
          const aXp = period === 'weekly' ? a.weekly_xp : period === 'monthly' ? a.monthly_xp : a.total_xp
          const bXp = period === 'weekly' ? b.weekly_xp : period === 'monthly' ? b.monthly_xp : b.total_xp
          return bXp - aXp
        })
        
        console.log('🔍 FamilyLeaderboard: Final members array:', members)
        const totalXpForPeriod = members.reduce((sum, m) => {
          const xp = period === 'weekly' ? m.weekly_xp : period === 'monthly' ? m.monthly_xp : m.total_xp
          return sum + xp
        }, 0)
        console.log(`🔍 FamilyLeaderboard: Total XP for ${period}:`, totalXpForPeriod)
        
        setFamilyMembers(members)
      } catch (error) {
        console.error('❌ FamilyLeaderboard: Failed to load family data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadFamilyData()
  }, [user, learnersSummaries, isBootstrapped, period])
  
  // Calculate aggregate stats (using period-based XP)
  const totalXP = familyMembers.reduce((sum, m) => {
    const xp = period === 'weekly' ? m.weekly_xp : period === 'monthly' ? m.monthly_xp : m.total_xp
    return sum + xp
  }, 0)
  const totalWords = familyMembers.reduce((sum, m) => sum + m.vocabulary_size, 0)
  const totalStreak = familyMembers.reduce((sum, m) => sum + m.current_streak, 0)
  const avgXP = familyMembers.length > 0 ? Math.round(totalXP / familyMembers.length) : 0
  const avgWords = familyMembers.length > 0 ? Math.round(totalWords / familyMembers.length) : 0
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">載入家庭數據...</p>
        </div>
      </div>
    )
  }
  
  if (familyMembers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <div className="text-6xl mb-4">👨‍👩‍👧‍👦</div>
        <h3 className="text-2xl font-bold text-white mb-2">還沒有家庭成員</h3>
        <p className="text-slate-400 mb-6">添加孩子來開始家庭排行榜！</p>
        <a
          href="/parent/children"
          className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-medium transition-colors"
        >
          添加孩子
        </a>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white flex items-center justify-center gap-3 mb-2">
          👨‍👩‍👧‍👦 家庭排行榜
        </h1>
        <p className="text-slate-400">看看誰是家庭學習冠軍！</p>
      </div>
      
      {/* Aggregate Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">
            {period === 'weekly' ? '本週經驗值' : period === 'monthly' ? '本月經驗值' : '總經驗值'}
          </div>
          <div className="text-3xl font-bold text-cyan-400">{totalXP.toLocaleString()}</div>
          <div className="text-xs text-slate-500 mt-1">平均: {avgXP.toLocaleString()}</div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">總詞彙量</div>
          <div className="text-3xl font-bold text-emerald-400">{totalWords.toLocaleString()}</div>
          <div className="text-xs text-slate-500 mt-1">平均: {avgWords.toLocaleString()}</div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">總連勝</div>
          <div className="text-3xl font-bold text-orange-400">{totalStreak}</div>
          <div className="text-xs text-slate-500 mt-1">天</div>
        </div>
      </div>
      
      {/* Period Toggle */}
      <div className="flex justify-center gap-2">
        <button
          onClick={() => setPeriod('weekly')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            period === 'weekly'
              ? 'bg-cyan-500 text-white'
              : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
          }`}
        >
          本週
        </button>
        <button
          onClick={() => setPeriod('monthly')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            period === 'monthly'
              ? 'bg-cyan-500 text-white'
              : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
          }`}
        >
          本月
        </button>
      </div>
      
      {/* Family Members Ranking */}
      <div className="space-y-3">
        {familyMembers.map((member, index) => {
          const rank = index + 1
          const isTop3 = rank <= 3
          // Get period-based XP
          const memberXP = period === 'weekly' ? member.weekly_xp : period === 'monthly' ? member.monthly_xp : member.total_xp
          
          return (
            <div
              key={member.id}
              className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                isTop3
                  ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-2 border-yellow-500/50'
                  : 'bg-slate-800/50 border border-slate-700 hover:bg-slate-700/50'
              }`}
            >
              {/* Rank */}
              <div
                className={`w-12 h-12 flex items-center justify-center rounded-full font-bold ${
                  isTop3 ? 'text-3xl' : 'bg-slate-700 text-slate-300 text-lg'
                }`}
              >
                {rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank}
              </div>
              
              {/* Member Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`font-semibold ${isTop3 ? 'text-yellow-400' : 'text-white'}`}>
                    {member.name}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    member.type === 'parent'
                      ? 'bg-blue-500/30 text-blue-400'
                      : 'bg-purple-500/30 text-purple-400'
                  }`}>
                    {member.type === 'parent' ? '家長' : '孩子'}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <span>⭐ {memberXP.toLocaleString()} XP</span>
                  <span>📚 {member.vocabulary_size} 字</span>
                  <span>⚡ {member.current_streak} 天</span>
                </div>
              </div>
              
              {/* Level Badge */}
              <div className="text-right">
                <div className="text-xs text-slate-400 mb-1">等級</div>
                <div className="text-2xl font-bold text-cyan-400">{member.level}</div>
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Encouragement */}
      <div className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-xl p-6 border border-cyan-500/30 text-center">
        <p className="text-white font-semibold mb-2">
          💪 繼續努力，一起成為學習冠軍家庭！
        </p>
        <p className="text-slate-300 text-sm">
          家庭總分: {totalXP.toLocaleString()} XP
        </p>
      </div>
    </div>
  )
}

