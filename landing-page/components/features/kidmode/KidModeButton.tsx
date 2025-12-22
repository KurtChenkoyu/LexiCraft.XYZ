'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useUserData } from '@/contexts/UserDataContext'
import { useAppStore } from '@/stores/useAppStore'

/**
 * KidModeButton - Start Kid Mode from parent view
 * 
 * Flow:
 * 1. Parent clicks "開始孩子模式"
 * 2. Modal shows children list
 * 3. Parent selects child
 * 4. Redirects to /learner/mine with kid mode active
 * 
 * Kid Mode features:
 * - Simplified UI (no wallet, no settings)
 * - Child's profile and progress used
 * - Exit requires returning to parent view
 */
export function KidModeButton() {
  const router = useRouter()
  const { children } = useUserData()
  const enterKidMode = useAppStore((state) => state.enterKidMode)
  const [showModal, setShowModal] = useState(false)
  
  const handleSelectChild = (child: { id: string; name: string }) => {
    // Enter kid mode
    enterKidMode(child.id, child.name)
    
    // Close modal
    setShowModal(false)
    
    // Navigate to learner view
    router.push('/learner/mine')
  }
  
  if (children.length === 0) {
    return null // Don't show if no children
  }
  
  return (
    <>
      {/* Kid Mode Button */}
      <button
        onClick={() => setShowModal(true)}
        className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl p-4 shadow-lg transition-all"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">👶</span>
            <div className="text-left">
              <div className="font-bold">孩子模式</div>
              <div className="text-sm text-white/80">讓孩子用您的設備學習</div>
            </div>
          </div>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </button>
      
      {/* Child Selection Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="px-6 py-5 bg-gradient-to-r from-purple-500 to-pink-500">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>👶</span>
                  選擇孩子
                </h2>
                <p className="text-sm text-white/80 mt-1">
                  選擇要進入學習模式的孩子
                </p>
              </div>
              
              {/* Children List */}
              <div className="p-4 space-y-3 max-h-[300px] overflow-y-auto">
                {children.map((child) => (
                  <button
                    key={child.id}
                    onClick={() => handleSelectChild({ ...child, name: child.name || '' })}
                    className="w-full p-4 rounded-xl border-2 border-gray-200 hover:border-purple-400 hover:bg-purple-50 transition-all text-left flex items-center gap-4"
                  >
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white text-xl font-bold">
                      {(child.name || '').charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="font-bold text-gray-800">{child.name}</div>
                      <div className="text-sm text-gray-500">
                        {child.age ? `${child.age} 歲` : '點擊開始'}
                      </div>
                    </div>
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                ))}
              </div>
              
              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                <button
                  onClick={() => setShowModal(false)}
                  className="w-full py-3 text-gray-500 hover:text-gray-700 transition-colors font-medium"
                >
                  取消
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default KidModeButton


