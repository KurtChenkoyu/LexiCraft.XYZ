'use client'

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { packLoader } from '@/lib/pack-loader'
import { EmojiMCQ } from '@/lib/pack-types'
import { useAppStore } from '@/stores/useAppStore'
import { audioService } from '@/lib/audio-service'

interface EmojiMCQSessionProps {
  /** Sense IDs to test (from forged/hollow words) */
  senseIds: string[]
  /** Pack ID (default emoji_core) */
  packId?: string
  /** Pre-generated MCQs (optional - if provided, skips generation for instant start) */
  preGeneratedMcqs?: EmojiMCQ[]
  /** Callback when session completes */
  onComplete?: (result: SessionResult) => void
  /** Callback to exit session */
  onExit?: () => void
}

interface SessionResult {
  total: number
  correct: number
  accuracy: number
  xpEarned: number
  verifiedWords: Array<{ senseId: string, isCorrect: boolean }>
}

interface Answer {
  mcqId: string
  senseId: string
  selectedIndex: number
  isCorrect: boolean
}

// Confetti particle component
function ConfettiParticle({ delay, x }: { delay: number; x: number }) {
  const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6']
  const color = colors[Math.floor(Math.random() * colors.length)]
  
  return (
    <motion.div
      initial={{ y: -20, x, opacity: 1, scale: 1, rotate: 0 }}
      animate={{ 
        y: 400, 
        opacity: 0, 
        scale: 0.5,
        rotate: Math.random() * 360
      }}
      transition={{ 
        duration: 1.5, 
        delay,
        ease: 'easeOut'
      }}
      className="absolute w-3 h-3 rounded-full pointer-events-none"
      style={{ backgroundColor: color, left: `${x}%` }}
    />
  )
}

// Celebration effect component
function CelebrationEffect({ show }: { show: boolean }) {
  if (!show) return null
  
  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {/* Confetti particles */}
      {Array.from({ length: 30 }).map((_, i) => (
        <ConfettiParticle 
          key={i} 
          delay={Math.random() * 0.3} 
          x={Math.random() * 100}
        />
      ))}
      
      {/* Center burst */}
      <motion.div
        initial={{ scale: 0, opacity: 1 }}
        animate={{ scale: 3, opacity: 0 }}
        transition={{ duration: 0.6 }}
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 rounded-full bg-emerald-500/30"
      />
    </div>
  )
}

/**
 * EmojiMCQSession - Session for emoji matching MCQs
 * 
 * Shows word→emoji and emoji→word questions for the given sense IDs.
 * Tracks progress and awards XP on completion.
 */
export function EmojiMCQSession({
  senseIds,
  packId = 'emoji_core',
  preGeneratedMcqs,
  onComplete,
  onExit,
}: EmojiMCQSessionProps) {
  const [mcqs, setMcqs] = useState<EmojiMCQ[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Answer[]>([])
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [status, setStatus] = useState<'loading' | 'active' | 'complete'>('loading')
  const [showCelebration, setShowCelebration] = useState(false)
  
  const applyDelta = useAppStore((state) => state.applyDelta)
  
  // Load MCQs for all sense IDs and preload session audio
  useEffect(() => {
    const preloadSessionAudio = async (mcqs: EmojiMCQ[]) => {
      // Extract unique words from all MCQs
      const uniqueWords = new Set<string>()
      const promptIds = new Set<string>()
      
      mcqs.forEach(mcq => {
        // Extract words from questions and options
        if (mcq.type === 'word_to_emoji') {
          const questionWord = mcq.question.text
          if (questionWord) {
            uniqueWords.add(questionWord)
            
            // Map to prompt ID
            const wordLower = questionWord.toLowerCase()
            if (wordLower === 'apple') {
              promptIds.add('click_on_apple')
            } else if (wordLower === 'cat') {
              promptIds.add('pick_the_cat')
            } else {
              promptIds.add('which_emoji_matches')
            }
          }
        } else {
          // emoji_to_word
          promptIds.add('which_word_matches')
          
          // Extract correct word
          const correctWord = mcq.options[mcq.correct_index]?.text
          if (correctWord) {
            uniqueWords.add(correctWord)
          }
        }
        
        // Extract all option words (for emoji_to_word)
        mcq.options.forEach(option => {
          if (option.text) {
            uniqueWords.add(option.text)
          }
        })
      })
      
      // Preload session-specific audio
      const preloadStartTime = Date.now()
      try {
        await Promise.all([
          audioService.preloadWords(Array.from(uniqueWords), 'emoji'),
          audioService.preloadPrompts(Array.from(promptIds), 'questions'),
          audioService.preloadSfx(['correct', 'wrong'])
        ])
        
        const preloadDuration = Date.now() - preloadStartTime
        if (process.env.NODE_ENV === 'development') {
          console.log(`🎵 Session: Preloaded ${uniqueWords.size} words, ${promptIds.size} prompts, feedback sounds (${preloadDuration}ms)`)
        }
      } catch (err) {
        console.warn('Session audio preload failed (non-critical):', err)
      }
    }
    
    // Fast path: Use pre-generated questions if available (instant start)
    if (preGeneratedMcqs && preGeneratedMcqs.length > 0) {
      setMcqs(preGeneratedMcqs)
      // Preload audio before marking as active
      preloadSessionAudio(preGeneratedMcqs).then(() => {
        setStatus('active')
        console.log(`⚡ Using ${preGeneratedMcqs.length} pre-generated MCQs (instant start)`)
      })
      return
    }
    
    // Fallback: Generate on mount (current behavior)
    const loadMCQs = async () => {
      setStatus('loading')
      try {
        const allMcqs = await packLoader.generateMCQBatch(packId, senseIds, 1) // 1 MCQ per word
        // Shuffle the MCQs
        const shuffled = allMcqs.sort(() => Math.random() - 0.5)
        setMcqs(shuffled)
        
        // Preload audio before marking as active
        await preloadSessionAudio(shuffled)
        setStatus('active')
        console.log(`🎯 Loaded ${shuffled.length} emoji MCQs for ${senseIds.length} words`)
      } catch (error) {
        console.error('Failed to load emoji MCQs:', error)
        setStatus('complete')
      }
    }
    
    if (senseIds.length > 0) {
      loadMCQs()
    } else {
      setStatus('complete')
    }
  }, [senseIds, packId, preGeneratedMcqs])
  
  const currentMCQ = mcqs[currentIndex]
  
  // Play prompt audio when a new question loads, then auto-play word pronunciation
  useEffect(() => {
    if (currentMCQ && status === 'active' && !showResult) {
      // Map MCQ type to prompt ID
      let promptId: string
      if (currentMCQ.type === 'word_to_emoji') {
        const word = currentMCQ.question.text?.toLowerCase()
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
      
      // Play prompt audio, then auto-play the word pronunciation
      audioService.playPrompt(promptId, 'questions')
        .then(() => {
          // After prompt finishes, auto-play the word/question audio
          if (currentMCQ.type === 'word_to_emoji') {
            // For word_to_emoji: play the word from question.text
            const wordToSpeak = currentMCQ.question.text
            if (wordToSpeak) {
              return audioService.playWord(wordToSpeak, 'emoji')
            }
          } else {
            // For emoji_to_word: play the correct word (to show what word matches the emoji)
            const correctWord = currentMCQ.options[currentMCQ.correct_index]?.text
            if (correctWord) {
              return audioService.playWord(correctWord, 'emoji')
            }
          }
        })
        .catch(err => {
          console.warn('Failed to play prompt/word audio:', err)
        })
    }
  }, [currentMCQ, status, showResult])
  
  const handleOptionSelect = (index: number) => {
    if (showResult) return
    
    // Defensive: Only allow selection if user explicitly clicked
    // This prevents any accidental auto-selection
    if (process.env.NODE_ENV === 'development') {
      console.log(`🎯 User selected option ${index} for question ${currentIndex + 1}`)
    }
    
    setSelectedOption(index)
  }
  
  const handleConfirm = useCallback(async () => {
    if (selectedOption === null || !currentMCQ) return
    
    const isCorrect = selectedOption === currentMCQ.correct_index
    
    // Record answer
    const answer: Answer = {
      mcqId: currentMCQ.id,
      senseId: currentMCQ.sense_id,
      selectedIndex: selectedOption,
      isCorrect,
    }
    setAnswers(prev => [...prev, answer])
    setShowResult(true)
    
    // Get the selected option's audio (what user chose)
    const selectedOptionData = currentMCQ.options[selectedOption]
    const selectedWord = selectedOptionData?.text // For emoji_to_word, this is the word they selected
    
    // Get the correct answer's audio
    const correctOptionData = currentMCQ.options[currentMCQ.correct_index]
    const correctWord = correctOptionData?.text // For emoji_to_word, this is the correct word
    
    // Show celebration if correct
    if (isCorrect) {
      setShowCelebration(true)
      setTimeout(() => setShowCelebration(false), 1500)
      
      // Award XP (optimistic)
      applyDelta({
        delta_xp: 5,
        delta_sparks: 2,
      })
    }
    
    // Play audio sequence:
    // 1. Play audio for user's selection (if it's a word, i.e., emoji_to_word)
    // 2. Play feedback (correct/wrong sound + feedback phrase)
    // 3. Play the correct answer's audio (if wrong, or if word_to_emoji and we want to reinforce)
    
    const playSequence = async () => {
      // Step 1: Play selected option's audio (only for emoji_to_word where options are words)
      if (selectedWord && currentMCQ.type === 'emoji_to_word') {
        await audioService.playWord(selectedWord, 'emoji').catch(err => {
          console.warn('Failed to play selected word audio:', err)
        })
      }
      
      // Step 2: Play feedback
      if (isCorrect) {
        // Play correct sound → feedback
        await audioService.playCorrect()
          .then(() => new Promise(resolve => setTimeout(resolve, 100)))
          .then(() => audioService.playRandomFeedback('correct'))
          .catch(err => {
            console.warn('Failed to play correct feedback:', err)
          })
      } else {
        // Play wrong sound → feedback
        await audioService.playWrong()
          .then(() => new Promise(resolve => setTimeout(resolve, 100)))
          .then(() => audioService.playRandomFeedback('incorrect'))
          .catch(err => {
            console.warn('Failed to play incorrect feedback:', err)
          })
      }
      
      // Step 3: Play the correct answer's audio (always play to reinforce the correct answer)
      if (currentMCQ.type === 'emoji_to_word' && correctWord) {
        // For emoji_to_word: always play correct word (reinforcement if correct, correction if wrong)
        if (process.env.NODE_ENV === 'development') {
          console.log(`🔊 Step 3: Playing correct word for emoji_to_word: ${correctWord}`)
        }
        await audioService.playWord(correctWord, 'emoji').catch(err => {
          console.warn('Failed to play correct answer audio:', err)
        })
      } else if (currentMCQ.type === 'word_to_emoji' && currentMCQ.question.text) {
        // For word_to_emoji: always play the question word (the correct answer)
        // This reinforces the word regardless of whether they got it right or wrong
        if (process.env.NODE_ENV === 'development') {
          console.log(`🔊 Step 3: Playing correct word for word_to_emoji: ${currentMCQ.question.text}`)
        }
        await audioService.playWord(currentMCQ.question.text, 'emoji').catch(err => {
          console.warn('Failed to play correct word audio:', err)
        })
      } else {
        if (process.env.NODE_ENV === 'development') {
          console.warn(`⚠️ Step 3: Skipped - type: ${currentMCQ.type}, correctWord: ${correctWord}, question.text: ${currentMCQ.question.text}`)
        }
      }
    }
    
    // Execute sequence (fire and forget - don't block UI)
    playSequence().catch(err => {
      console.warn('Audio sequence error:', err)
    })
  }, [selectedOption, currentMCQ, applyDelta])
  
  const handleNext = useCallback(() => {
    if (currentIndex + 1 >= mcqs.length) {
      // Session complete
      setStatus('complete')
    } else {
      setCurrentIndex(prev => prev + 1)
      setSelectedOption(null)
      setShowResult(false)
    }
  }, [currentIndex, mcqs.length])
  
  const handleComplete = () => {
    const correctCount = answers.filter(a => a.isCorrect).length
    const verifiedWords = answers.map(a => ({
      senseId: a.senseId,
      isCorrect: a.isCorrect
    }))
    const result: SessionResult = {
      total: answers.length,
      correct: correctCount,
      accuracy: answers.length > 0 ? correctCount / answers.length : 0,
      xpEarned: correctCount * 5,
      verifiedWords,
    }
    onComplete?.(result)
  }
  
  // Loading state
  if (status === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-6">
        <div className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mb-4" />
        <p className="text-slate-400">載入題目中...</p>
      </div>
    )
  }
  
  // Complete state
  if (status === 'complete') {
    const correctCount = answers.filter(a => a.isCorrect).length
    const accuracy = answers.length > 0 ? Math.round((correctCount / answers.length) * 100) : 0
    const xpEarned = correctCount * 5
    
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center min-h-[400px] text-center p-6"
      >
        <div className="text-6xl mb-4">
          {accuracy >= 80 ? '🎉' : accuracy >= 50 ? '👍' : '💪'}
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          {accuracy >= 80 ? '太棒了！' : accuracy >= 50 ? '不錯喔！' : '繼續加油！'}
        </h2>
        
        <div className="grid grid-cols-2 gap-4 my-6 w-full max-w-xs">
          <div className="bg-slate-800 rounded-xl p-4">
            <div className="text-3xl font-bold text-cyan-400">{accuracy}%</div>
            <div className="text-sm text-slate-400">正確率</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4">
            <div className="text-3xl font-bold text-amber-400">+{xpEarned}</div>
            <div className="text-sm text-slate-400">XP</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4">
            <div className="text-3xl font-bold text-emerald-400">{correctCount}</div>
            <div className="text-sm text-slate-400">答對</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4">
            <div className="text-3xl font-bold text-slate-400">{answers.length}</div>
            <div className="text-sm text-slate-400">總題數</div>
          </div>
        </div>
        
        <button
          onClick={handleComplete}
          className="w-full max-w-xs py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl transition-colors"
        >
          完成
        </button>
      </motion.div>
    )
  }
  
  // Active state - show MCQ
  if (!currentMCQ) {
    return null
  }
  
  const isWordToEmoji = currentMCQ.type === 'word_to_emoji'
  
  return (
    <div className="flex flex-col min-h-[500px] p-4 relative">
      {/* Celebration effect */}
      <CelebrationEffect show={showCelebration} />
      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-slate-400 mb-1">
          <span>題目 {currentIndex + 1} / {mcqs.length}</span>
          <span>{answers.filter(a => a.isCorrect).length} 答對</span>
        </div>
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-cyan-500"
            initial={{ width: 0 }}
            animate={{ width: `${((currentIndex + 1) / mcqs.length) * 100}%` }}
          />
        </div>
      </div>
      
      {/* Question */}
      <div className="flex-1 flex flex-col items-center justify-center">
        <div className="text-center mb-8">
          <p className="text-slate-400 mb-2">
            {currentMCQ.question.prompt_zh}
          </p>
          {isWordToEmoji ? (
            <div className="flex items-center justify-center gap-3">
              <h2 className="text-4xl font-bold text-white">
                {currentMCQ.question.text}
              </h2>
              {/* Speaker button */}
              <button
                onClick={() => audioService.playWord(currentMCQ.question.text || '', 'emoji')}
                className="p-2 rounded-full bg-slate-700 hover:bg-slate-600 text-cyan-400 transition-colors"
                aria-label="Play pronunciation"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              </button>
            </div>
          ) : (
            <div className="text-8xl">
              {currentMCQ.question.emoji}
            </div>
          )}
        </div>
        
        {/* Options */}
        <div className={`grid gap-3 w-full max-w-md ${isWordToEmoji ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {currentMCQ.options.map((option, index) => {
            const isSelected = selectedOption === index
            const isCorrect = index === currentMCQ.correct_index
            
            let optionStyle = 'bg-slate-800 border-slate-600 hover:border-cyan-500'
            if (showResult) {
              if (isCorrect) {
                optionStyle = 'bg-emerald-500/20 border-emerald-500'
              } else if (isSelected && !isCorrect) {
                optionStyle = 'bg-red-500/20 border-red-500'
              }
            } else if (isSelected) {
              optionStyle = 'bg-cyan-500/20 border-cyan-500'
            }
            
            return (
              <button
                key={index}
                onClick={() => handleOptionSelect(index)}
                disabled={showResult}
                className={`p-4 rounded-xl border-2 transition-all ${optionStyle}`}
              >
                {isWordToEmoji ? (
                  <span className="text-5xl">{option.emoji}</span>
                ) : (
                  <span className="text-xl font-medium text-white">{option.text}</span>
                )}
              </button>
            )
          })}
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="mt-6">
        {!showResult ? (
          <button
            onClick={handleConfirm}
            disabled={selectedOption === null}
            className={`w-full py-3 rounded-xl font-bold transition-all ${
              selectedOption !== null
                ? 'bg-cyan-600 hover:bg-cyan-500 text-white'
                : 'bg-slate-700 text-slate-500 cursor-not-allowed'
            }`}
          >
            確認答案
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl transition-all"
          >
            {currentIndex + 1 >= mcqs.length ? '查看結果' : '下一題'}
          </button>
        )}
      </div>
      
      {/* Exit button */}
      <button
        onClick={onExit}
        className="mt-3 w-full py-2 text-slate-400 hover:text-white transition-colors"
      >
        退出
      </button>
    </div>
  )
}

export default EmojiMCQSession


