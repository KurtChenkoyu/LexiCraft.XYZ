'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Block } from '@/types/mine'
import { audioService, VOICES, Voice, DEFAULT_VOICE } from '@/lib/audio-service'

interface EmojiWordDetailProps {
  block: Block | null
  isOpen: boolean
  onClose: () => void
  onStartQuiz?: (senseId: string) => void
}

/**
 * EmojiWordDetail - Full-screen detail view for a word
 * Shows emoji, word, translation, and audio playback
 */
export function EmojiWordDetail({ block, isOpen, onClose, onStartQuiz }: EmojiWordDetailProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedVoice, setSelectedVoice] = useState<Voice>(DEFAULT_VOICE)
  
  // Auto-play word on open
  useEffect(() => {
    if (isOpen && block) {
      // Small delay so user sees the modal first
      const timer = setTimeout(() => {
        handlePlayWord()
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [isOpen, block])
  
  const handlePlayWord = async () => {
    if (!block) return
    setIsPlaying(true)
    await audioService.playWord(block.word, 'emoji', selectedVoice)
    setTimeout(() => setIsPlaying(false), 500)
  }
  
  const handlePlayWithVoice = async (voice: Voice) => {
    if (!block) return
    setSelectedVoice(voice)
    setIsPlaying(true)
    await audioService.playWord(block.word, 'emoji', voice)
    setTimeout(() => setIsPlaying(false), 500)
  }
  
  if (!block) return null
  
  // Get status color
  const getStatusColor = () => {
    switch (block.status) {
      case 'solid': return 'from-purple-500 to-pink-500'
      case 'hollow': return 'from-cyan-500 to-blue-500'
      default: return 'from-slate-500 to-slate-600'
    }
  }
  
  const getStatusLabel = () => {
    switch (block.status) {
      case 'solid': return '💎 已掌握'
      case 'hollow': return '✨ 學習中'
      default: return '📦 新單字'
    }
  }
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-700"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors p-2"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {/* Status badge */}
            <div className="flex justify-center mb-4">
              <span className={`px-4 py-1 rounded-full text-sm font-medium bg-gradient-to-r ${getStatusColor()} text-white`}>
                {getStatusLabel()}
              </span>
            </div>
            
            {/* Emoji */}
            <div className="text-center mb-4">
              <motion.span 
                className="text-8xl block"
                animate={isPlaying ? { scale: [1, 1.1, 1] } : {}}
                transition={{ duration: 0.3 }}
              >
                {block.emoji || '📝'}
              </motion.span>
            </div>
            
            {/* Word */}
            <div className="text-center mb-2">
              <h2 className="text-4xl font-black text-white">{block.word}</h2>
            </div>
            
            {/* Translation */}
            {block.translation && (
              <p className="text-center text-xl text-slate-300 mb-6">
                {block.translation}
              </p>
            )}
            
            {/* Main play button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handlePlayWord}
              disabled={isPlaying}
              className={`w-full py-4 rounded-xl font-bold text-xl flex items-center justify-center gap-3 transition-all ${
                isPlaying
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white hover:from-cyan-400 hover:to-blue-400'
              }`}
            >
              {isPlaying ? (
                <>
                  <span className="animate-pulse">🔊</span>
                  播放中...
                </>
              ) : (
                <>
                  <span>🔊</span>
                  聽發音
                </>
              )}
            </motion.button>
            
            {/* Voice selector */}
            <div className="mt-4">
              <p className="text-sm text-slate-400 text-center mb-2">選擇聲音風格：</p>
              <div className="flex flex-wrap justify-center gap-2">
                {VOICES.slice(0, 5).map((voice) => (
                  <button
                    key={voice}
                    onClick={() => handlePlayWithVoice(voice)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                      selectedVoice === voice
                        ? 'bg-cyan-500 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {voice}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Start quiz button */}
            {onStartQuiz && block.status !== 'solid' && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onStartQuiz(block.sense_id)}
                className="w-full mt-4 py-3 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold rounded-xl"
              >
                🎯 開始測驗
              </motion.button>
            )}
            
            {/* Word info */}
            <div className="mt-6 pt-4 border-t border-slate-700">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center">
                  <span className="text-slate-400 block">分類</span>
                  <span className="text-white font-medium">{block.category || '基礎'}</span>
                </div>
                <div className="text-center">
                  <span className="text-slate-400 block">難度</span>
                  <span className="text-white font-medium">
                    {block.difficulty === 1 ? '⭐' : block.difficulty === 2 ? '⭐⭐' : '⭐⭐⭐'}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default EmojiWordDetail

