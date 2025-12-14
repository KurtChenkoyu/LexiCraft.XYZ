'use client'

import { motion, AnimatePresence } from 'framer-motion'

interface FeedbackPosition {
  x: number
  y: number
}

interface MiningFeedbackProps {
  positions: FeedbackPosition[]
}

export function MiningFeedback({ positions }: MiningFeedbackProps) {
  return (
    <AnimatePresence>
      {positions.map((pos, i) => (
        <motion.div
          key={`${pos.x}-${pos.y}-${i}-${Date.now()}`}
          className="fixed pointer-events-none z-50"
          style={{ left: pos.x, top: pos.y }}
          initial={{ opacity: 1, scale: 1, y: 0 }}
          animate={{ 
            opacity: 0, 
            scale: 1.5, 
            y: -50 
          }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          <div className="flex flex-col items-center">
            <div className="text-2xl mb-1">⛏️</div>
            <div className="text-sm font-bold text-amber-400 bg-slate-900/80 px-2 py-1 rounded-lg">
              +10 XP
            </div>
          </div>
        </motion.div>
      ))}
    </AnimatePresence>
  )
}

