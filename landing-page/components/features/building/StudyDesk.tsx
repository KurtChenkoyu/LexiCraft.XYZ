'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// Desk levels with emoji + CSS styling
const DESK_LEVELS = [
  {
    level: 1,
    emoji: '📦',
    name: 'Cardboard Box',
    nameCn: '紙箱桌',
    description: 'A humble beginning',
    descriptionCn: '謙卑的起點',
    wordsRequired: 0,
    colors: {
      primary: '#8B4513',
      secondary: '#A0522D',
      accent: '#D2691E',
      glow: null,
    },
  },
  {
    level: 2,
    emoji: '🪑',
    name: 'Folding Table',
    nameCn: '折疊桌',
    description: 'Getting organized',
    descriptionCn: '開始整理',
    wordsRequired: 10,
    colors: {
      primary: '#DEB887',
      secondary: '#D2B48C',
      accent: '#F5DEB3',
      glow: null,
    },
  },
  {
    level: 3,
    emoji: '📚',
    name: 'Wooden Desk',
    nameCn: '木製書桌',
    description: 'A proper study space',
    descriptionCn: '正式的學習空間',
    wordsRequired: 25,
    colors: {
      primary: '#8B7355',
      secondary: '#A08060',
      accent: '#C4A77D',
      glow: null,
    },
  },
  {
    level: 4,
    emoji: '💼',
    name: 'Executive Desk',
    nameCn: '行政辦公桌',
    description: 'Serious business',
    descriptionCn: '認真的事業',
    wordsRequired: 50,
    colors: {
      primary: '#4A0E0E',
      secondary: '#6B1A1A',
      accent: '#8B0000',
      glow: 'rgba(139, 0, 0, 0.3)',
    },
  },
  {
    level: 5,
    emoji: '🚀',
    name: 'Hover Desk',
    nameCn: '懸浮書桌',
    description: 'The future of learning',
    descriptionCn: '學習的未來',
    wordsRequired: 100,
    colors: {
      primary: '#1E3A5F',
      secondary: '#2E5A8F',
      accent: '#4169E1',
      glow: 'rgba(65, 105, 225, 0.5)',
    },
  },
]

interface StudyDeskProps {
  wordsLearned: number
  showProgress?: boolean
  size?: 'sm' | 'md' | 'lg'
  onUpgrade?: (newLevel: number) => void
}

export function StudyDesk({ 
  wordsLearned, 
  showProgress = true, 
  size = 'md',
  onUpgrade 
}: StudyDeskProps) {
  const [displayedLevel, setDisplayedLevel] = useState(1)
  const [changeDirection, setChangeDirection] = useState<'up' | 'down' | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Calculate current level based on words learned
  const currentLevel = DESK_LEVELS.reduce((level, desk) => {
    return wordsLearned >= desk.wordsRequired ? desk.level : level
  }, 1)

  const currentDesk = DESK_LEVELS[currentLevel - 1]
  const nextDesk = DESK_LEVELS[currentLevel] || null

  // Progress to next level
  const progressToNext = nextDesk 
    ? Math.min(100, ((wordsLearned - currentDesk.wordsRequired) / (nextDesk.wordsRequired - currentDesk.wordsRequired)) * 100)
    : 100

  // Detect level changes - simplified to avoid race conditions
  useEffect(() => {
    if (currentLevel !== displayedLevel) {
      // Clear any pending timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      const direction = currentLevel > displayedLevel ? 'up' : 'down'
      setChangeDirection(direction)
      
      if (direction === 'up') {
        onUpgrade?.(currentLevel)
      }
      
      // Update displayed level immediately
      setDisplayedLevel(currentLevel)
      
      // Clear direction indicator after animation
      timeoutRef.current = setTimeout(() => {
        setChangeDirection(null)
      }, 400)
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [currentLevel, displayedLevel, onUpgrade])

  const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-32 h-32',
    lg: 'w-48 h-48',
  }

  const emojiSizes = {
    sm: 'text-4xl',
    md: 'text-6xl',
    lg: 'text-8xl',
  }

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Desk Visual */}
      <motion.div
        className={`relative ${sizeClasses[size]} rounded-xl flex items-center justify-center overflow-hidden`}
        animate={{
          background: `linear-gradient(135deg, ${currentDesk.colors.primary} 0%, ${currentDesk.colors.secondary} 100%)`,
          boxShadow: currentDesk.colors.glow 
            ? `0 0 30px ${currentDesk.colors.glow}, 0 0 60px ${currentDesk.colors.glow}`
            : '0 4px 12px rgba(0,0,0,0.3)',
          scale: changeDirection === 'up' ? [1, 1.1, 1] : changeDirection === 'down' ? [1, 0.95, 1] : 1,
          rotate: changeDirection ? [0, 2, -2, 0] : 0,
        }}
        transition={{ 
          duration: 0.3,
          background: { duration: 0.4 },
          boxShadow: { duration: 0.4 },
        }}
      >
        {/* Glow effect for high levels */}
        <AnimatePresence>
          {currentDesk.colors.glow && (
            <motion.div
              key={`glow-${currentLevel}`}
              className="absolute inset-0 rounded-xl"
              style={{
                background: `radial-gradient(circle, ${currentDesk.colors.glow} 0%, transparent 70%)`,
              }}
              initial={{ opacity: 0 }}
              animate={{
                opacity: [0.5, 0.8, 0.5],
              }}
              exit={{ opacity: 0 }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          )}
        </AnimatePresence>

        {/* Emoji - simple key-based swap without AnimatePresence mode="wait" to avoid race conditions */}
        <motion.span
          key={`emoji-${currentLevel}`}
          className={`${emojiSizes[size]} relative z-10`}
          initial={{ 
            scale: 0.3, 
            opacity: 0,
          }}
          animate={{ 
            scale: 1, 
            opacity: 1,
            y: currentDesk.level === 5 ? [0, -8, 0] : 0,
          }}
          transition={{
            scale: { type: 'spring', stiffness: 400, damping: 15 },
            opacity: { duration: 0.2 },
            y: currentDesk.level === 5 ? {
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            } : { duration: 0.2 },
          }}
        >
          {currentDesk.emoji}
        </motion.span>

        {/* Level badge */}
        <motion.div 
          className="absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg"
          animate={{ 
            backgroundColor: currentDesk.colors.accent,
            scale: changeDirection ? [1, 1.2, 1] : 1,
          }}
          transition={{ duration: 0.3 }}
        >
          {currentLevel}
        </motion.div>

        {/* Level change flash overlay */}
        <AnimatePresence>
          {changeDirection && (
            <motion.div
              key={`overlay-${currentLevel}-${changeDirection}`}
              className={`absolute inset-0 rounded-xl flex items-center justify-center ${
                changeDirection === 'up' ? 'bg-yellow-400/25' : 'bg-red-400/20'
              }`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <motion.span
                className="text-3xl"
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.5, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {changeDirection === 'up' ? '⬆️' : '⬇️'}
              </motion.span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Desk Info */}
      <div className="text-center">
        <h3 className="font-bold text-lg">{currentDesk.nameCn}</h3>
        <p className="text-sm text-gray-500">{currentDesk.name}</p>
      </div>

      {/* Progress Bar (if not max level) */}
      {showProgress && nextDesk && (
        <div className="w-full max-w-xs">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>{wordsLearned} 個單字</span>
            <span>下一級: {nextDesk.wordsRequired}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: currentDesk.colors.accent }}
              initial={{ width: 0 }}
              animate={{ width: `${progressToNext}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <p className="text-xs text-center text-gray-400 mt-1">
            還需 {nextDesk.wordsRequired - wordsLearned} 個單字升級到 {nextDesk.nameCn}
          </p>
        </div>
      )}

      {/* Max level message */}
      {showProgress && !nextDesk && (
        <div className="text-center">
          <span className="text-yellow-500">✨</span>
          <span className="text-sm text-gray-500 ml-1">最高等級！</span>
          <span className="text-yellow-500">✨</span>
        </div>
      )}
    </div>
  )
}

// Demo component to test the desk
export function StudyDeskDemo() {
  const [words, setWords] = useState(0)

  return (
    <div className="p-8 bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl">
      <h2 className="text-white text-xl font-bold mb-6 text-center">
        📚 One Room MVP - Study Desk
      </h2>
      
      <div className="flex flex-col items-center gap-6">
        <StudyDesk 
          wordsLearned={words} 
          size="lg"
          onUpgrade={(level) => console.log(`Upgraded to level ${level}!`)}
        />

        {/* Test controls */}
        <div className="flex gap-2 mt-4 flex-wrap justify-center">
          <button
            onClick={() => setWords(w => Math.max(0, w - 25))}
            className="px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-800 transition"
          >
            -25
          </button>
          <button
            onClick={() => setWords(w => Math.max(0, w - 5))}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
          >
            -5
          </button>
          <button
            onClick={() => setWords(w => w + 5)}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
          >
            +5
          </button>
          <button
            onClick={() => setWords(w => w + 25)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            +25
          </button>
        </div>

        <p className="text-gray-400 text-sm">
          Current: {words} words learned
        </p>
      </div>

      {/* Level Preview */}
      <div className="mt-8 border-t border-gray-700 pt-6">
        <h3 className="text-gray-400 text-sm mb-4 text-center">All Desk Levels</h3>
        <div className="flex justify-center gap-4 flex-wrap">
          {DESK_LEVELS.map((desk) => (
            <div 
              key={desk.level}
              className={`text-center p-3 rounded-lg ${words >= desk.wordsRequired ? 'bg-gray-700' : 'bg-gray-800 opacity-50'}`}
            >
              <span className="text-3xl">{desk.emoji}</span>
              <p className="text-xs text-gray-400 mt-1">Lv.{desk.level}</p>
              <p className="text-xs text-gray-500">{desk.wordsRequired}+</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default StudyDesk

