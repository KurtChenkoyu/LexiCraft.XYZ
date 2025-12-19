'use client'

import { useAppStore, selectChildren, selectUser, selectActivePack, selectLearners } from '@/stores/useAppStore'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'

interface EmojiLearnerSelectionModalProps {
  isOpen: boolean
  onClose: () => void
}

/**
 * EmojiLearnerSelectionModal - Modal to select active learner for emoji pack
 * 
 * Shows when:
 * - Emoji pack is active
 * - User enters learner routes and has multiple learner profiles
 *
 * IDENTITY RULES:
 * - All backend-facing identity MUST flow through `activeLearner` / `switchLearner`.
 * - This modal only calls `switchLearner(learnerId)` and never manages its own player identity state.
 */
export function EmojiLearnerSelectionModal({ isOpen, onClose }: EmojiLearnerSelectionModalProps) {
  const children = useAppStore(selectChildren)
  const user = useAppStore(selectUser)
  const activePack = useAppStore(selectActivePack)
  const learners = useAppStore(selectLearners)
  const switchLearner = useAppStore((state) => state.switchLearner)
  
  // Only show if emoji pack is active
  if (activePack?.id !== 'emoji_core') {
    return null
  }
  
  /**
   * Resolve a learner profile for a given child selection.
   *
   * Preferred mapping:
   * - Match on learner.user_id === child.id (canonical DB link)
   * Fallback:
   * - Match on learner.display_name === child.name (best-effort)
   */
  const findLearnerForChild = (childId: string, childName: string | null) => {
    // 1) Preferred: explicit user_id ↔ child.id mapping
    let learner = learners.find(
      (l) => !l.is_parent_profile && l.user_id === childId,
    )

    // 2) Fallback: match on display_name if no direct mapping
    if (!learner && childName) {
      learner = learners.find(
        (l) => !l.is_parent_profile && l.display_name === childName,
      )
    }

    if (!learner) {
      console.warn('[EmojiLearnerSelectionModal] No learner profile found for child selection', {
        childId,
        childName,
      })
    }

    return learner
  }
  
  const handleSelectParent = async () => {
    if (!user) return

    // Data: switch canonical activeLearner via multi-profile system
    const parentLearner = learners.find((l) => l.is_parent_profile)
    if (!parentLearner) {
      console.warn('[EmojiLearnerSelectionModal] Parent learner profile not found for current user', {
        userId: user.id,
      })
      onClose()
      return
    }

    try {
      await switchLearner(parentLearner.id)
    } catch (error) {
      console.warn('[EmojiLearnerSelectionModal] Failed to switch learner for parent selection', error)
    } finally {
      onClose()
    }
  }
  
  const handleSelectChild = async (childId: string, childName: string | null) => {
    // Data: resolve learner and switch canonical activeLearner
    const learner = findLearnerForChild(childId, childName)

    if (learner) {
      try {
        await switchLearner(learner.id)
      } catch (error) {
        console.warn('[EmojiLearnerSelectionModal] Failed to switch learner for child selection', error)
      }
    }

    onClose()
  }
  
  if (!isOpen) return null
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-slate-900/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl max-w-md w-full p-6"
        >
          <h2 className="text-2xl font-bold text-white mb-2 text-center">
            🎯 選擇玩家
          </h2>
          <p className="text-slate-400 text-sm text-center mb-6">
            選擇要追蹤進度的玩家
          </p>
          
          {/* Parent Option */}
          {user && (
            <button
              onClick={handleSelectParent}
              className="w-full mb-3 px-4 py-4 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl transition-colors text-left flex items-center gap-3"
            >
              <span className="text-3xl">👨</span>
              <div className="flex-1">
                <div className="font-semibold text-white">{user.name || 'Parent'}</div>
                <div className="text-xs text-slate-400">家長</div>
              </div>
              <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
          
          {/* Children Options */}
          {children.length > 0 ? (
            <>
              {children.map((child) => (
                <button
                  key={child.id}
                  onClick={() => handleSelectChild(child.id, child.name)}
                  className="w-full mb-3 px-4 py-4 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl transition-colors text-left flex items-center gap-3"
                >
                  <span className="text-3xl">👧</span>
                  <div className="flex-1">
                    <div className="font-semibold text-white">{child.name || 'Child'}</div>
                    <div className="text-xs text-slate-400">
                      {child.age ? `${child.age} 歲` : '孩子'}
                    </div>
                  </div>
                  <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              ))}
              
              {/* Add Child Link */}
              <div className="border-t border-slate-700 pt-3 mt-3">
                <Link
                  href="/parent/children"
                  onClick={onClose}
                  className="w-full px-4 py-3 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded-xl transition-colors text-center flex items-center justify-center gap-2"
                >
                  <span>➕</span>
                  <span className="font-medium">添加孩子</span>
                </Link>
              </div>
            </>
          ) : (
            <div className="text-center py-6">
              <p className="text-slate-400 mb-4">還沒有添加孩子</p>
              <Link
                href="/parent/children"
                onClick={onClose}
                className="inline-block px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-medium transition-colors"
              >
                添加孩子
              </Link>
            </div>
          )}
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="w-full mt-4 px-4 py-2 text-slate-400 hover:text-slate-300 text-sm transition-colors"
          >
            稍後選擇
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

