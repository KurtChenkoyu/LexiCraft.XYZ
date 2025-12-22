'use client'

import React from 'react'

// Types for level unlocks
export interface LevelUnlock {
  code: string
  type: string
  name_en: string
  name_zh?: string
  description_en?: string
  description_zh?: string
  icon?: string
  unlocked_at_level?: number
}

export interface LevelUpInfo {
  old_level: number
  new_level: number
  rewards?: string[]
  new_unlocks?: LevelUnlock[]
}

export interface AchievementInfo {
  id: string
  code: string
  name_en: string
  name_zh?: string
  description_en?: string
  description_zh?: string
  icon?: string
  xp_reward: number
  crystal_reward?: number
  points_bonus?: number
}

// XP Toast Animation Component
export const XPToast: React.FC<{ 
  xp: number
  show: boolean
  multiplier?: number 
}> = ({ xp, show, multiplier }) => {
  if (!show || xp === 0) return null
  
  return (
    <div className="fixed top-20 right-4 z-[60] animate-bounce">
      <div className="bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 rounded-full shadow-lg shadow-orange-500/50 flex items-center gap-2">
        <span className="text-xl">⚡</span>
        <span className="text-white font-bold">+{xp} XP</span>
        {multiplier && multiplier > 1 && (
          <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded text-white">
            {multiplier}×
          </span>
        )}
      </div>
    </div>
  )
}

// Crystal Toast Animation Component
export const CrystalToast: React.FC<{ 
  amount: number
  show: boolean 
}> = ({ amount, show }) => {
  if (!show || amount === 0) return null
  
  return (
    <div className="fixed top-32 right-4 z-[60] animate-bounce">
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 rounded-full shadow-lg shadow-purple-500/50 flex items-center gap-2">
        <span className="text-xl">💎</span>
        <span className="text-white font-bold">+{amount}</span>
      </div>
    </div>
  )
}

// Streak Banner Component
export const StreakBanner: React.FC<{ 
  days: number
  show: boolean 
}> = ({ days, show }) => {
  if (!show || days === 0) return null
  
  return (
    <div className="fixed top-32 left-1/2 -translate-x-1/2 z-[60] animate-bounce">
      <div className="bg-gradient-to-r from-red-500 to-orange-500 px-4 py-2 rounded-full shadow-lg flex items-center gap-2">
        <span className="text-xl">⚡</span>
        <span className="text-white font-bold">連續 {days} 天！</span>
      </div>
    </div>
  )
}

// Enhanced Level Up Celebration with Unlocks
export const LevelUpCelebration: React.FC<{ 
  oldLevel: number
  newLevel: number
  newUnlocks?: LevelUnlock[]
  show: boolean
  onClose: () => void 
}> = ({ oldLevel, newLevel, newUnlocks, show, onClose }) => {
  if (!show) return null
  
  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-gradient-to-br from-yellow-500 to-orange-600 p-8 rounded-3xl shadow-2xl text-center max-w-md mx-4 animate-scale-in">
        {/* Confetti effect */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 rounded-full animate-confetti"
              style={{
                left: `${Math.random() * 100}%`,
                backgroundColor: ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'][i % 5],
                animationDelay: `${Math.random() * 0.5}s`,
              }}
            />
          ))}
        </div>
        
        <div className="text-6xl mb-4">🎉</div>
        <h2 className="text-2xl font-black text-white mb-2">升級了！</h2>
        
        {/* Level transition */}
        <div className="flex items-center justify-center gap-4 mb-4">
          <span className="text-4xl font-black text-white/60">{oldLevel}</span>
          <span className="text-2xl text-white">→</span>
          <span className="text-5xl font-black text-white">{newLevel}</span>
        </div>
        
        {/* New unlocks */}
        {newUnlocks && newUnlocks.length > 0 && (
          <div className="mt-4 mb-4 bg-black/20 rounded-xl p-4">
            <div className="text-sm text-white/80 mb-2">🔓 新解鎖：</div>
            <div className="space-y-2">
              {newUnlocks.map((unlock, index) => (
                <div 
                  key={unlock.code}
                  className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2 animate-slide-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <span className="text-xl">{unlock.icon || '✨'}</span>
                  <div className="text-left">
                    <div className="text-white font-semibold text-sm">
                      {unlock.name_zh || unlock.name_en}
                    </div>
                    <div className="text-white/60 text-xs">
                      {unlock.description_zh || unlock.description_en}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <p className="text-white/80 mb-4">
          {newUnlocks && newUnlocks.length > 0 
            ? '恭喜解鎖新功能！' 
            : '恭喜！你的等級提升了！'}
        </p>
        
        <button 
          onClick={onClose}
          className="px-6 py-2 bg-white text-orange-600 font-bold rounded-full hover:bg-white/90 transition-all"
        >
          太棒了！
        </button>
      </div>
    </div>
  )
}

// Achievement Toast Component
export const AchievementToast: React.FC<{ 
  achievement: AchievementInfo | null
  show: boolean
}> = ({ achievement, show }) => {
  if (!show || !achievement) return null
  
  return (
    <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-[60] animate-slide-up">
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-6 py-3 rounded-xl shadow-lg shadow-purple-500/50 flex items-center gap-3">
        <span className="text-2xl">{achievement.icon || '🏆'}</span>
        <div>
          <div className="text-xs text-white/80">成就解鎖！</div>
          <div className="text-white font-bold">{achievement.name_zh || achievement.name_en}</div>
          {(achievement.xp_reward > 0 || (achievement.crystal_reward && achievement.crystal_reward > 0)) && (
            <div className="flex gap-2 text-xs text-white/80 mt-1">
              {achievement.xp_reward > 0 && <span>+{achievement.xp_reward} XP</span>}
              {achievement.crystal_reward && achievement.crystal_reward > 0 && (
                <span>+{achievement.crystal_reward} 💎</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Feature Unlock Toast (for showing unlocks outside of level-up)
export const UnlockToast: React.FC<{ 
  unlock: LevelUnlock | null
  show: boolean
}> = ({ unlock, show }) => {
  if (!show || !unlock) return null
  
  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[60] animate-slide-down">
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 px-6 py-3 rounded-xl shadow-lg shadow-cyan-500/50 flex items-center gap-3">
        <span className="text-2xl">{unlock.icon || '🔓'}</span>
        <div>
          <div className="text-xs text-white/80">功能解鎖！</div>
          <div className="text-white font-bold">{unlock.name_zh || unlock.name_en}</div>
        </div>
      </div>
    </div>
  )
}

