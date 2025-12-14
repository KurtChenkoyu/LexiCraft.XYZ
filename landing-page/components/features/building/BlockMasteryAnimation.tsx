'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface BlockMasteryAnimationProps {
  isVisible: boolean
  onComplete: () => void
  wordText?: string
}

/**
 * The "Diamond Moment" - A huge celebration when user masters a word
 * and earns a Block.
 * 
 * This needs to be HUGE because it's the payoff for 7-10 days of SRS work.
 */
export function BlockMasteryAnimation({
  isVisible,
  onComplete,
  wordText = '',
}: BlockMasteryAnimationProps) {
  const [phase, setPhase] = useState<'cube' | 'fly' | 'banner'>('cube')

  useEffect(() => {
    if (isVisible) {
      setPhase('cube')
      
      // Phase transitions
      const flyTimer = setTimeout(() => setPhase('fly'), 1500)
      const bannerTimer = setTimeout(() => setPhase('banner'), 2500)
      const completeTimer = setTimeout(() => {
        onComplete()
        setPhase('cube')
      }, 4000)
      
      return () => {
        clearTimeout(flyTimer)
        clearTimeout(bannerTimer)
        clearTimeout(completeTimer)
      }
    }
  }, [isVisible, onComplete])

  // Particle burst
  const particles = Array.from({ length: 40 }, (_, i) => ({
    id: i,
    angle: (i / 40) * 360,
    distance: 100 + Math.random() * 150,
    delay: Math.random() * 0.3,
    size: 8 + Math.random() * 16,
    emoji: ['🧱', '✨', '💎', '⭐', '🔥'][Math.floor(Math.random() * 5)],
  }))

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Dark overlay */}
          <motion.div
            className="absolute inset-0 bg-black/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Screen shake container */}
          <motion.div
            className="relative"
            animate={phase === 'cube' ? {
              x: [0, -5, 5, -3, 3, 0],
              y: [0, 3, -3, 5, -5, 0],
            } : {}}
            transition={{ duration: 0.5, repeat: 2 }}
          >
            {/* Particle burst */}
            <AnimatePresence>
              {phase === 'cube' && particles.map((p) => (
                <motion.span
                  key={p.id}
                  className="absolute text-2xl"
                  style={{ 
                    left: '50%', 
                    top: '50%',
                    fontSize: `${p.size}px`,
                  }}
                  initial={{ 
                    x: 0, 
                    y: 0, 
                    scale: 0, 
                    opacity: 1,
                  }}
                  animate={{ 
                    x: Math.cos(p.angle * Math.PI / 180) * p.distance,
                    y: Math.sin(p.angle * Math.PI / 180) * p.distance,
                    scale: 1,
                    opacity: 0,
                    rotate: 360,
                  }}
                  transition={{ 
                    duration: 1.2, 
                    delay: p.delay,
                    ease: 'easeOut',
                  }}
                >
                  {p.emoji}
                </motion.span>
              ))}
            </AnimatePresence>

            {/* Main 3D Cube */}
            <AnimatePresence>
              {(phase === 'cube' || phase === 'fly') && (
                <motion.div
                  className="relative"
                  initial={{ scale: 0, rotate: 0 }}
                  animate={phase === 'cube' ? {
                    scale: [0, 1.5, 1.2],
                    rotate: [0, 180, 360],
                  } : {
                    scale: [1.2, 0.3],
                    y: [0, -300],
                    opacity: [1, 0],
                  }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ 
                    duration: phase === 'cube' ? 1 : 0.8,
                    ease: phase === 'cube' ? 'backOut' : 'easeIn',
                  }}
                >
                  {/* Glow behind cube */}
                  <motion.div
                    className="absolute inset-0 bg-orange-500/40 rounded-3xl blur-3xl"
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.5, 0.8, 0.5],
                    }}
                    transition={{ duration: 1, repeat: Infinity }}
                  />
                  
                  {/* Cube */}
                  <motion.div
                    className="relative w-32 h-32 rounded-2xl bg-gradient-to-br from-orange-400 via-amber-500 to-orange-600 shadow-2xl flex items-center justify-center border-4 border-orange-300"
                    animate={{
                      rotateY: [0, 360],
                      rotateX: [0, 15, 0, -15, 0],
                    }}
                    transition={{ 
                      duration: 3, 
                      repeat: Infinity,
                      ease: 'linear',
                    }}
                    style={{
                      transformStyle: 'preserve-3d',
                      boxShadow: '0 0 60px rgba(251, 146, 60, 0.5), inset 0 0 30px rgba(255, 255, 255, 0.2)',
                    }}
                  >
                    <span className="text-6xl">🧱</span>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Banner */}
            <AnimatePresence>
              {phase === 'banner' && (
                <motion.div
                  className="absolute inset-0 flex flex-col items-center justify-center"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                >
                  {/* Main banner */}
                  <motion.div
                    className="bg-gradient-to-r from-orange-600 via-amber-500 to-orange-600 px-8 py-4 rounded-2xl shadow-2xl border-2 border-orange-300"
                    animate={{
                      scale: [1, 1.05, 1],
                    }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-4xl">🧱</span>
                      <div className="text-center">
                        <motion.h3
                          className="text-2xl font-bold text-white"
                          animate={{ scale: [1, 1.1, 1] }}
                          transition={{ duration: 0.3, repeat: 3 }}
                        >
                          +1 BLOCK!
                        </motion.h3>
                        {wordText && (
                          <p className="text-orange-100 text-sm">
                            掌握了 "{wordText}"
                          </p>
                        )}
                      </div>
                      <span className="text-4xl">🧱</span>
                    </div>
                  </motion.div>

                  {/* Subtitle */}
                  <motion.p
                    className="mt-4 text-orange-200 text-sm"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    可以用來升級家具了！
                  </motion.p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default BlockMasteryAnimation

