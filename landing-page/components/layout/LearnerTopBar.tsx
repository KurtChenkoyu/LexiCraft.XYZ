'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAppStore, selectBalance, selectLearnerProfile, selectActivePack, selectIsKidModeActive, selectKidModeChildName } from '@/stores/useAppStore'
import Link from 'next/link'
import { PackSelectorDropdown } from '@/components/features/packs/PackSelectorDropdown'
import { LearnerSwitcher } from './PlayerSwitcher'

/**
 * Learner Top Bar (HUD Layer)
 * 
 * The persistent top bar for learner routes.
 * Shows: Logo, Pack, Streak, Wallet, Settings
 * 
 * In Kid Mode:
 * - Shows child's name
 * - Hides wallet and settings
 * - Shows "Exit" button to return to parent view
 * 
 * Z-Index: 40 (HUD layer, above content)
 * Persistence: Never unmounts during learner navigation
 * 
 * @see .cursorrules - "The Game Viewport Law"
 */
export function LearnerTopBar() {
  const router = useRouter()
  const balance = useAppStore(selectBalance)
  const learnerProfile = useAppStore(selectLearnerProfile)
  const activePack = useAppStore(selectActivePack)
  const isKidMode = useAppStore(selectIsKidModeActive)
  const kidModeChildName = useAppStore(selectKidModeChildName)
  const exitKidMode = useAppStore((state) => state.exitKidMode)
  
  const [showPackDropdown, setShowPackDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const currentStreak = learnerProfile?.current_streak ?? 0
  const availablePoints = balance?.available_points ?? 0
  
  // Pack indicator emoji and name
  const packEmoji = activePack?.id === 'emoji_core' ? '🎯' : '📚'
  const packName = activePack?.id === 'emoji_core' ? '表情' : '詞彙'
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowPackDropdown(false)
      }
    }
    if (showPackDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showPackDropdown])
  
  // Handle exit kid mode
  const handleExitKidMode = () => {
    exitKidMode()
    router.push('/parent/dashboard')
  }

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border-b border-white/10 px-4 py-3">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        {/* Left: App Title/Logo */}
        <Link href="/learner/home" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-sm font-bold text-white">塊</span>
          </div>
          <span className="font-semibold text-white hidden sm:block">LexiCraft</span>
        </Link>

        {/* Center: Pack Indicator (Dropdown) + Player Switcher (if emoji) + Streak */}
        <div className="flex items-center gap-2">
          {/* Pack Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowPackDropdown(!showPackDropdown)}
              className="flex items-center gap-1.5 text-sm bg-slate-700/50 hover:bg-slate-600/50 px-2.5 py-1.5 rounded-lg transition-colors"
              title="切換詞彙包"
            >
              <span>{packEmoji}</span>
              <span className="text-slate-300 text-xs hidden sm:inline">{packName}</span>
              <svg className={`w-3 h-3 text-slate-400 transition-transform ${showPackDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {/* Dropdown Menu */}
            {showPackDropdown && (
              <PackSelectorDropdown onClose={() => setShowPackDropdown(false)} />
            )}
          </div>
          
          {/* Learner Switcher (only for emoji pack) */}
          {activePack?.id === 'emoji_core' && (
            <LearnerSwitcher />
          )}
          {process.env.NODE_ENV === 'development' && activePack?.id !== 'emoji_core' && (
            <div className="text-xs text-red-400">Pack: {activePack?.id || 'none'}</div>
          )}
          
          {/* Streak */}
          <div className="flex items-center gap-2 text-sm bg-orange-500/20 px-3 py-1.5 rounded-lg">
            <span className="text-orange-400">⚡</span>
            <span className="text-white font-semibold">{currentStreak}</span>
          </div>
        </div>

        {/* Right side - varies based on Kid Mode */}
        {isKidMode ? (
          // Kid Mode: Show child name + exit button
          <div className="flex items-center gap-3">
            {/* Child Name Badge */}
            <div className="flex items-center gap-1.5 bg-purple-500/20 text-purple-400 px-3 py-1.5 rounded-lg text-sm font-semibold">
              <span>👶</span>
              <span className="hidden sm:inline">{kidModeChildName}</span>
            </div>
            
            {/* Exit Kid Mode Button */}
            <button
              onClick={handleExitKidMode}
              className="flex items-center gap-1 bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">結束</span>
            </button>
          </div>
        ) : (
          // Normal Mode: Wallet + Settings
          <div className="flex items-center gap-3">
            {/* Wallet Badge */}
            <button className="flex items-center gap-1.5 bg-amber-500/20 text-amber-400 px-3 py-1.5 rounded-lg text-sm font-semibold hover:bg-amber-500/30 transition-colors">
              <span>💰</span>
              <span>{availablePoints.toLocaleString()}</span>
            </button>
            
            {/* Settings Button */}
            <Link 
              href="/learner/settings"
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

