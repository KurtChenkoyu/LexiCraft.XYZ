'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface LevelUpModalProps {
  isOpen: boolean
  onClose: () => void
  oldLevel: number
  newLevel: number
  energyEarned: number
}

// Energy rewards by level (matching backend)
const LEVEL_ENERGY_REWARDS: Record<number, number> = {
  2: 30,
  3: 50,
  4: 75,
  5: 100,
}
const DEFAULT_ENERGY = 125 // For levels 6+

export function LevelUpModal({
  isOpen,
  onClose,
  oldLevel,
  newLevel,
  energyEarned,
}: LevelUpModalProps) {
  const [showParticles, setShowParticles] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setShowParticles(true)
      const timer = setTimeout(() => setShowParticles(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

  // Generate confetti particles
  const particles = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    delay: Math.random() * 0.5,
    duration: 1 + Math.random() * 1,
    emoji: ['✨', '⚡', '🎉', '⭐', '💫'][Math.floor(Math.random() * 5)],
  }))

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/70 z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="relative bg-gradient-to-br from-yellow-900/90 via-amber-900/90 to-orange-900/90 rounded-3xl p-8 max-w-sm w-full border-2 border-yellow-500/50 shadow-2xl overflow-hidden"
              initial={{ scale: 0.5, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.5, y: 50 }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Confetti particles */}
              <AnimatePresence>
                {showParticles && particles.map((p) => (
                  <motion.span
                    key={p.id}
                    className="absolute text-2xl pointer-events-none"
                    style={{ left: `${p.x}%` }}
                    initial={{ y: -20, opacity: 1 }}
                    animate={{ 
                      y: 400, 
                      opacity: 0,
                      rotate: 360,
                      x: (Math.random() - 0.5) * 100,
                    }}
                    exit={{ opacity: 0 }}
                    transition={{ 
                      duration: p.duration, 
                      delay: p.delay,
                      ease: 'easeOut',
                    }}
                  >
                    {p.emoji}
                  </motion.span>
                ))}
              </AnimatePresence>

              {/* Glow effect */}
              <div className="absolute inset-0 bg-gradient-radial from-yellow-400/20 to-transparent pointer-events-none" />

              {/* Content */}
              <div className="relative z-10 text-center">
                {/* Crown icon */}
                <motion.div
                  className="text-6xl mb-4"
                  animate={{ 
                    scale: [1, 1.2, 1],
                    rotate: [0, 10, -10, 0],
                  }}
                  transition={{ 
                    duration: 0.5,
                    repeat: 2,
                  }}
                >
                  👑
                </motion.div>

                {/* Level up text */}
                <motion.h2
                  className="text-3xl font-bold text-yellow-300 mb-2"
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 1 }}
                >
                  升級了！
                </motion.h2>
                
                <p className="text-xl text-white mb-6">
                  Level <span className="text-yellow-400 font-bold">{oldLevel}</span>
                  {' → '}
                  <span className="text-green-400 font-bold text-2xl">{newLevel}</span>
                </p>

                {/* Energy reward */}
                <motion.div
                  className="bg-blue-500/20 rounded-2xl p-4 mb-6 border border-blue-400/30"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.3, type: 'spring' }}
                >
                  <p className="text-gray-300 text-sm mb-2">能量獎勵</p>
                  <motion.div
                    className="flex items-center justify-center gap-2"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 0.5 }}
                  >
                    <span className="text-4xl">⚡</span>
                    <span className="text-4xl font-bold text-blue-400">+{energyEarned}</span>
                  </motion.div>
                  <p className="text-gray-400 text-xs mt-2">
                    用能量升級你的家具！
                  </p>
                </motion.div>

                {/* Close button */}
                <motion.button
                  onClick={onClose}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-yellow-500 to-amber-500 text-white font-bold text-lg shadow-lg hover:from-yellow-600 hover:to-amber-600 transition-all"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  太棒了！
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default LevelUpModal

