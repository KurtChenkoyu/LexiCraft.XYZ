'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAppStore, selectChildrenSummaries, selectChildren } from '@/stores/useAppStore'
import { useRolePreference } from '@/hooks/useRolePreference'
import { useUserData } from '@/contexts/UserDataContext'

/**
 * Family Progress Page - Parent-Learner Quick View
 * 
 * Allows parent-learners to quickly see their children's progress
 * without fully switching to parent mode.
 * 
 * URL: /learner/family
 * 
 * Architecture:
 * - Reads from Zustand (pre-loaded by Bootstrap)
 * - Clicking a child switches to parent mode and navigates
 * - Shows toast notification during mode switch
 * 
 * @see .cursorrules - "Last War" instant rendering principle
 */
export default function FamilyPage() {
  const router = useRouter()
  const childrenSummaries = useAppStore(selectChildrenSummaries)
  const children = useAppStore(selectChildren) // Check basic children list too
  const { setRole } = useRolePreference()
  const { selectChild } = useUserData()
  const [showTransition, setShowTransition] = useState(false)
  const [transitionChild, setTransitionChild] = useState('')
  
  // Debug logging (client-side only)
  if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
    console.log('👨‍👩‍👧 FamilyPage: childrenSummaries =', childrenSummaries)
    console.log('👨‍👩‍👧 FamilyPage: children =', children)
  }
  
  const handleViewChildAnalytics = (childId: string, childName: string) => {
    // Show transition notification
    setTransitionChild(childName)
    setShowTransition(true)
    
    // Switch role and select child
    setRole('parent')
    selectChild(childId)
    
    // Navigate after brief delay for notification visibility
    setTimeout(() => {
      router.push('/parent/dashboard/analytics')
    }, 1000)
  }
  
  // If no children summaries but we have basic children data, use that as fallback
  const displayChildren = childrenSummaries.length > 0 
    ? childrenSummaries 
    : children.map(child => ({
        id: child.id,
        name: child.name,
        age: child.age,
        email: child.email,
        level: 1,
        total_xp: 0,
        current_streak: 0,
        vocabulary_size: 0,
        words_learned_this_week: 0,
        last_active_date: null
      }))
  
  if (displayChildren.length === 0) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl font-bold text-white mb-8">👨‍👩‍👧 Family Progress</h1>
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-12 text-center border border-white/20">
            <div className="text-6xl mb-4">👨‍👩‍👧</div>
            <p className="text-white/80 text-lg">No children added yet</p>
            <p className="text-white/60 text-sm mt-2">
              Switch to Parent View to add children
            </p>
          </div>
        </div>
      </main>
    )
  }
  
  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
      {/* Mode Switch Notification */}
      {showTransition && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[60] animate-slide-down">
          <div className="bg-gradient-to-r from-cyan-600 to-blue-600 px-6 py-3 rounded-xl shadow-lg shadow-cyan-500/50 flex items-center gap-3">
            <span className="text-2xl">👨‍👩‍👧</span>
            <div>
              <div className="text-white font-bold">Switching to Parent View...</div>
              <div className="text-white/80 text-sm">Viewing {transitionChild}&apos;s progress</div>
            </div>
          </div>
        </div>
      )}
      
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-white mb-2">👨‍👩‍👧 Family Progress</h1>
        <p className="text-white/60 mb-8">Quick overview of your children&apos;s learning</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {displayChildren.map((child) => (
            <button
              key={child.id}
              onClick={() => handleViewChildAnalytics(child.id, child.name || 'Child')}
              className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 hover:bg-white/15 hover:border-white/30 transition-all text-left active:scale-98"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white">{child.name || 'Child'}</h3>
                  <p className="text-white/60 text-sm">{child.age ? `${child.age} years old` : ''}</p>
                </div>
                <div className="text-white/40 text-2xl">→</div>
              </div>
              
              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-white/60 text-sm">Level</div>
                  <div className="text-2xl font-bold text-white">Lv {child.level}</div>
                </div>
                <div>
                  <div className="text-white/60 text-sm">Streak</div>
                  <div className="text-2xl font-bold text-white">🔥 {child.current_streak}</div>
                </div>
              </div>
              
              {/* This Week's Progress */}
              <div className="bg-white/5 rounded-lg p-3 mb-3">
                <div className="text-white/60 text-sm mb-1">This Week</div>
                <div className="text-white font-semibold">
                  +{child.words_learned_this_week} words
                </div>
              </div>
              
              {/* Total Vocab */}
              <div className="text-white/40 text-sm">
                Total: {child.vocabulary_size} words learned
              </div>
              
              {/* Last Active */}
              {child.last_active_date && (
                <div className="text-white/40 text-xs mt-2">
                  Last active: {new Date(child.last_active_date).toLocaleDateString()}
                </div>
              )}
            </button>
          ))}
        </div>
        
        {/* Info Box */}
        <div className="mt-8 bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-4 text-cyan-100">
          <div className="flex items-start gap-3">
            <div className="text-2xl">ℹ️</div>
            <div className="flex-1">
              <p className="text-sm">
                Tap on any child to view detailed analytics in Parent View
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}

