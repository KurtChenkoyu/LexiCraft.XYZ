'use client'

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { EmojiMCQ, EmojiMCQOption } from '@/lib/pack-types'
import { audioService } from '@/lib/audio-service'

interface EmojiMCQCardProps {
  mcq: EmojiMCQ
  onAnswer: (isCorrect: boolean, selectedIndex: number) => void
  showFeedback?: boolean
  disabled?: boolean
}

/**
 * Emoji MCQ Card - Displays word↔emoji matching questions
 * 
 * Two modes:
 * - word_to_emoji: Shows word, user picks emoji
 * - emoji_to_word: Shows emoji, user picks word
 * 
 * Designed for young learners with large touch targets
 * and playful animations.
 */
export function EmojiMCQCard({ 
  mcq, 
  onAnswer, 
  showFeedback = true,
  disabled = false 
}: EmojiMCQCardProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [showResult, setShowResult] = useState(false)
  
  const isCorrect = selectedIndex !== null && selectedIndex === mcq.correct_index

  // Play prompt audio when MCQ loads
  useEffect(() => {
    if (mcq && !disabled) {
      // Map MCQ type to prompt ID
      let promptId: string
      if (mcq.type === 'word_to_emoji') {
        // Use specific prompts if word is mentioned, otherwise generic
        const word = mcq.question.text?.toLowerCase()
        if (word === 'apple') {
          promptId = 'click_on_apple'
        } else if (word === 'cat') {
          promptId = 'pick_the_cat'
        } else {
          promptId = 'which_emoji_matches'
        }
      } else {
        // emoji_to_word
        promptId = 'which_word_matches'
      }
      
      // Play prompt audio (English only, offline)
      audioService.playPrompt(promptId, 'questions').catch(err => {
        console.warn('Failed to play prompt audio:', err)
      })
    }
  }, [mcq, disabled])

  const handleSelect = useCallback((index: number) => {
    if (disabled || showResult) return
    
    // Defensive: Only allow selection if user explicitly clicked
    // This prevents any accidental auto-selection
    if (process.env.NODE_ENV === 'development') {
      console.log(`🎯 User selected option ${index}`)
    }
    
    setSelectedIndex(index)
    const correct = index === mcq.correct_index
    
    // Get the word to pronounce (from question.text or correct option's text)
    const wordToPlay = mcq.question.text || mcq.options[mcq.correct_index].text
    
    // 🔊 Play audio feedback (English only, offline)
    if (correct) {
      // Play audio sequence: correct sound → feedback → word pronunciation
      // Chain them sequentially to avoid overlap
      audioService.playCorrect()
        .then(() => {
          // Wait a bit after the short beep, then play feedback
          return new Promise(resolve => setTimeout(resolve, 100))
        })
        .then(() => audioService.playRandomFeedback('correct'))
        .then(() => {
          // After feedback finishes, play word pronunciation
          if (wordToPlay) {
            return audioService.playWord(wordToPlay, 'emoji')
          }
        })
        .catch(err => {
          console.warn('Failed to play audio sequence:', err)
        })
    } else {
      audioService.playWrong()
      // Play random encouraging feedback
      setTimeout(() => {
        audioService.playRandomFeedback('incorrect').catch(err => {
          console.warn('Failed to play feedback audio:', err)
        })
      }, 200)
    }
    
    if (showFeedback) {
      setShowResult(true)
      // Delay before calling onAnswer to show feedback
      setTimeout(() => {
        onAnswer(correct, index)
      }, 1200)
    } else {
      onAnswer(correct, index)
    }
  }, [disabled, showResult, showFeedback, mcq.correct_index, mcq.question.text, mcq.options, onAnswer])

  const getOptionClass = (index: number, option: EmojiMCQOption) => {
    const base = "relative flex items-center justify-center rounded-2xl border-4 transition-all duration-200 cursor-pointer"
    
    if (!showResult) {
      if (selectedIndex === index) {
        return `${base} border-cyan-400 bg-cyan-500/20 scale-95`
      }
      return `${base} border-slate-600 bg-slate-800/50 hover:border-slate-500 hover:bg-slate-700/50 active:scale-95`
    }
    
    // Show result state
    if (option.is_correct) {
      return `${base} border-emerald-400 bg-emerald-500/30`
    }
    if (selectedIndex === index && !option.is_correct) {
      return `${base} border-red-400 bg-red-500/30`
    }
    return `${base} border-slate-700 bg-slate-800/30 opacity-50`
  }

  return (
    <div className="w-full max-w-md mx-auto p-4">
      {/* Question Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 mb-6 border border-slate-700 shadow-xl"
      >
        {/* Category Badge */}
        <div className="text-center mb-2">
          <span className="px-3 py-1 rounded-full bg-slate-700/50 text-slate-400 text-xs uppercase tracking-wide">
            {mcq.category}
          </span>
        </div>

        {/* Question Content */}
        <div className="text-center py-6">
          {mcq.type === 'word_to_emoji' ? (
            // Show word, pick emoji
            <div>
              <p className="text-slate-400 text-sm mb-2">{mcq.question.prompt_zh}</p>
              <div className="flex items-center justify-center gap-3">
                <h2 className="text-4xl font-bold text-white tracking-wide">
                  {mcq.question.text}
                </h2>
                {/* Speaker button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (mcq.question.text) audioService.playWord(mcq.question.text, 'emoji')
                  }}
                  className="p-2 rounded-full bg-slate-700 hover:bg-slate-600 text-cyan-400 transition-colors"
                  aria-label="播放發音"
                >
                  🔊
                </button>
              </div>
            </div>
          ) : (
            // Show emoji, pick word
            <div>
              <p className="text-slate-400 text-sm mb-2">{mcq.question.prompt_zh}</p>
              <div className="text-7xl mb-2">
                {mcq.question.emoji}
              </div>
            </div>
          )}
        </div>

        {/* Difficulty Stars */}
        <div className="flex justify-center gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              className={`text-lg ${
                star <= mcq.difficulty ? 'text-amber-400' : 'text-slate-700'
              }`}
            >
              ★
            </span>
          ))}
        </div>
      </motion.div>

      {/* Options Grid */}
      <div className={`grid gap-4 ${mcq.type === 'word_to_emoji' ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {mcq.options.map((option, index) => (
          <motion.button
            key={index}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => handleSelect(index)}
            disabled={disabled || showResult}
            className={getOptionClass(index, option)}
            style={{
              minHeight: mcq.type === 'word_to_emoji' ? '100px' : '70px'
            }}
          >
            {mcq.type === 'word_to_emoji' ? (
              // Emoji options (larger)
              <span className="text-5xl">{option.emoji}</span>
            ) : (
              // Word options
              <span className="text-2xl font-bold text-white px-6 py-4">
                {option.text}
              </span>
            )}

            {/* Correct/Incorrect indicator */}
            <AnimatePresence>
              {showResult && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className={`absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center text-lg font-bold ${
                    option.is_correct
                      ? 'bg-emerald-500 text-white'
                      : selectedIndex === index
                      ? 'bg-red-500 text-white'
                      : 'hidden'
                  }`}
                >
                  {option.is_correct ? '✓' : '✗'}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.button>
        ))}
      </div>

      {/* Result Feedback */}
      <AnimatePresence>
        {showResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`mt-6 p-4 rounded-2xl text-center ${
              isCorrect
                ? 'bg-emerald-500/20 border border-emerald-500/50'
                : 'bg-red-500/20 border border-red-500/50'
            }`}
          >
            <div className="text-4xl mb-2">
              {isCorrect ? '🎉' : '😅'}
            </div>
            <p className={`font-bold text-lg ${isCorrect ? 'text-emerald-400' : 'text-red-400'}`}>
              {isCorrect ? '太棒了！' : '再試一次！'}
            </p>
            {!isCorrect && (
              <p className="text-slate-400 text-sm mt-1">
                正確答案：{mcq.type === 'word_to_emoji' 
                  ? mcq.options[mcq.correct_index].emoji 
                  : mcq.options[mcq.correct_index].text}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default EmojiMCQCard


