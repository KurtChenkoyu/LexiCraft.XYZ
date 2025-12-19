'use client'

import { useState, useEffect } from 'react'
import { useAppStore, selectChildren, selectChildrenSummaries, selectUser } from '@/stores/useAppStore'
import { downloadService } from '@/services/downloadService'

interface FamilyMember {
  id: string
  name: string
  type: 'parent' | 'child'
  level: number
  total_xp: number
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
  const children = useAppStore(selectChildren)
  const childrenSummaries = useAppStore(selectChildrenSummaries)
  
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly')
  
  // Load family data
  useEffect(() => {
    const loadFamilyData = async () => {
      setLoading(true)
      try {
        const members: FamilyMember[] = []
        
        // Add parent
        if (user) {
          // Load parent's learner profile
          const parentProfile = await downloadService.getProfile()
          // For now, use placeholder data - we'll need to load actual learner profile
          members.push({
            id: user.id,
            name: user.name || 'Parent',
            type: 'parent',
            level: 1,
            total_xp: 0,
            current_streak: 0,
            vocabulary_size: 0,
            words_learned_this_week: 0,
          })
        }
        
        // Add children from summaries
        childrenSummaries.forEach(summary => {
          members.push({
            id: summary.id,
            name: summary.name || 'Child',
            type: 'child',
            level: summary.level,
            total_xp: summary.total_xp,
            current_streak: summary.current_streak,
            vocabulary_size: summary.vocabulary_size,
            words_learned_this_week: summary.words_learned_this_week,
          })
        })
        
        // Sort by total XP (descending)
        members.sort((a, b) => b.total_xp - a.total_xp)
        
        setFamilyMembers(members)
      } catch (error) {
        console.error('Failed to load family data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadFamilyData()
  }, [user, children, childrenSummaries])
  
  // Calculate aggregate stats
  const totalXP = familyMembers.reduce((sum, m) => sum + m.total_xp, 0)
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
          <div className="text-slate-400 text-sm mb-2">總經驗值</div>
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
                  <span>⭐ {member.total_xp.toLocaleString()} XP</span>
                  <span>📚 {member.vocabulary_size} 字</span>
                  <span>🔥 {member.current_streak} 天</span>
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

