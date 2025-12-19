'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAppStore, selectLearners, selectUser, selectActiveLearner, selectBalance, selectLearnerProfile } from '@/stores/useAppStore'
import Link from 'next/link'

/**
 * LearnerSwitcher - Dropdown to select active learner (parent or child)
 * 
 * Shows in top nav when emoji pack is active.
 * Allows switching between family members for per-player progress tracking.
 */
export function LearnerSwitcher() {
  const router = useRouter()
  const learners = useAppStore(selectLearners)
  const user = useAppStore(selectUser)
  const activeLearner = useAppStore(selectActiveLearner)
  const balance = useAppStore(selectBalance)
  const learnerProfile = useAppStore(selectLearnerProfile)
  const switchLearner = useAppStore((state) => state.switchLearner)
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showDropdown])
  
  // Get current player stats
  const currentXP = learnerProfile?.level?.total_xp ?? 0
  const currentStreak = learnerProfile?.current_streak ?? 0
  const currentPoints = balance?.available_points ?? 0
  
  // Handle learner selection - calls switchLearner which reloads all data
  const handleSelectLearner = async (learnerId: string) => {
    await switchLearner(learnerId)
    setShowDropdown(false)
  }
  
  // Handle "Play as Parent"
  const handleSelectParent = async () => {
    const parentLearner = learners.find(l => l.is_parent_profile)
    if (parentLearner) {
      await handleSelectLearner(parentLearner.id)
    } else {
      console.warn('[LearnerSwitcher] Parent learner not found in learners array:', learners)
    }
  }
  
  // Handle "Select Child Learner"
  const handleSelectChildLearner = async (learnerId: string) => {
    await handleSelectLearner(learnerId)
  }
  
  // Display name for current learner
  const displayName = activeLearner?.display_name || '選擇玩家'
  const displayIcon = activeLearner?.is_parent_profile ? '👨' : '👧'
  
  // Get child learners (non-parent profiles)
  const childLearners = learners.filter(l => !l.is_parent_profile)
  const parentLearner = learners.find(l => l.is_parent_profile)
  
  // Debug: Log if learners are missing
  if (process.env.NODE_ENV === 'development' && learners.length === 0) {
    console.warn('[LearnerSwitcher] No learners found in store. Check bootstrap.')
  }
  if (process.env.NODE_ENV === 'development' && !parentLearner && learners.length > 0) {
    console.warn('[LearnerSwitcher] Parent learner not found. Learners:', learners.map(l => ({ id: l.id, name: l.display_name, is_parent: l.is_parent_profile })))
  }
  
  // Show loading state if bootstrap hasn't completed yet
  if (!isBootstrapped && learners.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm bg-slate-700/50 px-3 py-1.5 rounded-lg">
        <span className="text-slate-400 text-xs">載入中...</span>
      </div>
    )
  }
  
  // Don't render if no learners after bootstrap (shouldn't happen, but graceful fallback)
  if (isBootstrapped && learners.length === 0) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('[LearnerSwitcher] Bootstrap completed but no learners found. Check bootstrap step 2c.')
    }
    return null
  }
  
  return (
    <div className="relative" ref={dropdownRef}>
      {/* Player Button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-2 text-sm bg-slate-700/50 hover:bg-slate-600/50 px-3 py-1.5 rounded-lg transition-colors"
        title="切換玩家"
      >
        <span>{displayIcon}</span>
        <span className="text-slate-300 text-xs hidden sm:inline max-w-[80px] truncate">
          {displayName}
        </span>
        <svg 
          className={`w-3 h-3 text-slate-400 transition-transform ${showDropdown ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {/* Dropdown Menu */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-64 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
          {/* Current Player Stats */}
          {activeLearner && (
            <div className="px-4 py-3 bg-slate-700/50 border-b border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{displayIcon}</span>
                <span className="font-semibold text-white">{activeLearner.display_name}</span>
                <span className="text-xs text-slate-400 px-1.5 py-0.5 bg-slate-600 rounded">
                  {activeLearner.is_parent_profile ? '家長' : '孩子'}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-300">
                <div className="flex items-center gap-1">
                  <span>⭐</span>
                  <span>{currentXP.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span>🔥</span>
                  <span>{currentStreak}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span>💰</span>
                  <span>{currentPoints.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Player List */}
          <div className="max-h-64 overflow-y-auto">
            {/* Parent Option */}
            {parentLearner && (
              <button
                onClick={handleSelectParent}
                className={`w-full px-4 py-3 text-left hover:bg-slate-700/50 transition-colors flex items-center gap-3 ${
                  activeLearner?.is_parent_profile ? 'bg-cyan-500/20 border-l-2 border-cyan-500' : ''
                }`}
              >
                <span className="text-xl">👨</span>
                <div className="flex-1">
                  <div className="font-medium text-white">{parentLearner.display_name || 'Parent'}</div>
                  <div className="text-xs text-slate-400">家長</div>
                </div>
                {activeLearner?.is_parent_profile && (
                  <svg className="w-4 h-4 text-cyan-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            )}
            
            {/* Children Options */}
            {childLearners.length > 0 ? (
              childLearners.map((learner) => (
                <button
                  key={learner.id}
                  onClick={() => handleSelectChildLearner(learner.id)}
                  className={`w-full px-4 py-3 text-left hover:bg-slate-700/50 transition-colors flex items-center gap-3 ${
                    activeLearner?.id === learner.id ? 'bg-cyan-500/20 border-l-2 border-cyan-500' : ''
                  }`}
                >
                  <span className="text-xl">👧</span>
                  <div className="flex-1">
                    <div className="font-medium text-white">{learner.display_name || 'Child'}</div>
                    <div className="text-xs text-slate-400">
                      {learner.age_group ? `${learner.age_group} 歲` : '孩子'}
                    </div>
                  </div>
                  {activeLearner?.id === learner.id && (
                    <svg className="w-4 h-4 text-cyan-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))
            ) : (
              <div className="px-4 py-3 text-center text-slate-400 text-sm">
                <p className="mb-2">還沒有添加孩子</p>
                <Link
                  href="/parent/children"
                  onClick={() => setShowDropdown(false)}
                  className="text-cyan-400 hover:text-cyan-300 underline"
                >
                  添加孩子
                </Link>
              </div>
            )}
            
            {/* Add Child Option */}
            {childLearners.length > 0 && (
              <div className="border-t border-slate-700">
                <Link
                  href="/parent/children"
                  onClick={() => setShowDropdown(false)}
                  className="w-full px-4 py-3 text-left hover:bg-slate-700/50 transition-colors flex items-center gap-3 text-slate-300"
                >
                  <span className="text-xl">➕</span>
                  <span className="text-sm">添加孩子</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

