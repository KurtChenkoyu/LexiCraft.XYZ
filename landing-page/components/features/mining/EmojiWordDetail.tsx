'use client'

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Block } from '@/types/mine'
import { audioService, VOICES, Voice, DEFAULT_VOICE, AUDIO_PATHS } from '@/lib/audio-service'
import { useAppStore, selectEmojiVocabulary, selectEmojiProgress } from '@/stores/useAppStore'

interface EmojiWordDetailProps {
  block: Block | null
  isOpen: boolean
  onClose: () => void
  onAddToSmelting?: (senseId: string, word: string) => void  // For raw words
  onStartQuiz?: (senseId: string) => void  // For hollow words (in queue/SRS)
}

/**
 * EmojiWordDetail - Full-screen detail view for a word
 * Shows emoji, word, translation, and audio playback
 */
export function EmojiWordDetail({ block, isOpen, onClose, onAddToSmelting, onStartQuiz }: EmojiWordDetailProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedVoice, setSelectedVoice] = useState<Voice>(DEFAULT_VOICE)
  const [isPlayingAll, setIsPlayingAll] = useState(false) // Track if "play all" is active
  const [isPreloading, setIsPreloading] = useState(false)
  const [preloadComplete, setPreloadComplete] = useState(false)
  const [showTranslation, setShowTranslation] = useState(false)
  const [showHelpTooltip, setShowHelpTooltip] = useState(false)
  const [hasAutoPlayed, setHasAutoPlayed] = useState(false)
  const hoverTimerRef = React.useRef<NodeJS.Timeout | null>(null)
  
  // Get vocabulary and progress from store for category stats
  const emojiVocabulary = useAppStore(selectEmojiVocabulary)
  const emojiProgress = useAppStore(selectEmojiProgress)
  
  // Calculate category stats (learned/total)
  const categoryStats = useMemo(() => {
    if (!block?.category || !emojiVocabulary || !emojiProgress) return null
    
    // Count total words in this category
    const totalInCategory = emojiVocabulary.filter(v => v.category === block.category).length
    
    // Count learned words in this category (hollow or solid status)
    const learnedInCategory = emojiVocabulary.filter(v => {
      if (v.category !== block.category) return false
      const status = emojiProgress.get(v.sense_id)
      return status === 'hollow' || status === 'solid' || status === 'mastered'
    }).length
    
    return { learned: learnedInCategory, total: totalInCategory }
  }, [block?.category, emojiVocabulary, emojiProgress])
  
  // Fisher-Yates shuffle algorithm for random voice order
  const shuffleVoices = (voices: Voice[]): Voice[] => {
    const shuffled = [...voices]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    return shuffled
  }

  const handlePlayWord = useCallback(async () => {
    if (!block || !preloadComplete) return
    setIsPlaying(true)
    
    // If "Play All" is active, play all voices; otherwise play selected voice
    if (isPlayingAll) {
      const shuffledVoices = shuffleVoices([...VOICES])
      for (let i = 0; i < shuffledVoices.length; i++) {
        await audioService.playWord(block.word, 'emoji', shuffledVoices[i])
        if (i < shuffledVoices.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }
    } else {
      await audioService.playWord(block.word, 'emoji', selectedVoice)
    }
    
    setTimeout(() => setIsPlaying(false), 500)
  }, [block, preloadComplete, selectedVoice, isPlayingAll])
  
  // Preload all 9 voice variants and wait for readiness
  useEffect(() => {
    if (isOpen && block) {
      setIsPreloading(true)
      setPreloadComplete(false)
      setHasAutoPlayed(false) // Reset auto-play flag when modal opens
      
      const word = block.word.toLowerCase().replace(/\s+/g, '_')
      const audioCache = audioService.getAudioCache()
      const preloadPromises: Promise<void>[] = []
      
      // Preload all 9 voice variants and wait for canplaythrough
      VOICES.forEach(voice => {
        const path = `${AUDIO_PATHS.emoji}/${word}_${voice}.mp3`
        
        // Skip if already cached and ready
        const existing = audioCache.get(path)
        if (existing && existing.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
          return
        }
        
        const audio = new Audio()
        audio.preload = 'auto'
        audio.src = path
        
        // Wait for audio to be ready
        const preloadPromise = new Promise<void>((resolve) => {
          audio.addEventListener('canplaythrough', () => {
            audioCache.set(path, audio)
            resolve()
          }, { once: true })
          
          audio.addEventListener('error', () => {
            // Silently fail for missing files (expected in MVP)
            resolve()
          }, { once: true })
          
          // Timeout after 3 seconds to prevent hanging
          setTimeout(() => resolve(), 3000)
        })
        
        preloadPromises.push(preloadPromise)
      })
      
      // Wait for all variants to be ready
      Promise.all(preloadPromises).then(() => {
        setIsPreloading(false)
        setPreloadComplete(true)
        
        // Auto-play default voice once ready (only on initial load, not when voice changes)
        if (!hasAutoPlayed) {
          setTimeout(() => {
            if (block) {
              setHasAutoPlayed(true)
              setIsPlaying(true)
              audioService.playWord(block.word, 'emoji', selectedVoice).then(() => {
                setTimeout(() => setIsPlaying(false), 500)
              })
            }
          }, 100)
        }
      })
    } else {
      setIsPreloading(false)
      setPreloadComplete(false)
      setShowTranslation(false) // Reset translation visibility when modal closes
      setShowHelpTooltip(false) // Reset help tooltip when modal closes
      setHasAutoPlayed(false) // Reset auto-play flag when modal closes
      if (hoverTimerRef.current) {
        clearTimeout(hoverTimerRef.current)
        hoverTimerRef.current = null
      }
    }
    // Note: selectedVoice is intentionally NOT in dependencies to prevent re-triggering when user changes voice
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, block])

  const handleForgeMouseEnter = () => {
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current)
    }
    hoverTimerRef.current = setTimeout(() => {
      setShowHelpTooltip(true)
    }, 2000)
  }

  const handleForgeMouseLeave = () => {
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current)
      hoverTimerRef.current = null
    }
    setShowHelpTooltip(false)
  }
  
  const handlePlayWithVoice = async (voice: Voice) => {
    if (!block || !preloadComplete || isPlaying) return
    setSelectedVoice(voice)
    setIsPlayingAll(false) // Clear play-all state when individual voice is selected
    setIsPlaying(true)
    await audioService.playWord(block.word, 'emoji', voice)
    setTimeout(() => setIsPlaying(false), 500)
  }

  const handlePlayAllVoices = async () => {
    if (!block || !preloadComplete || isPlaying) return
    
    setIsPlayingAll(true) // Set play-all as active (stays highlighted)
    setSelectedVoice(DEFAULT_VOICE) // Clear individual voice selection
    setIsPlaying(true)
    const shuffledVoices = shuffleVoices([...VOICES])
    
    // Cascade playback: play each voice with 500ms delay
    for (let i = 0; i < shuffledVoices.length; i++) {
      await audioService.playWord(block.word, 'emoji', shuffledVoices[i])
      if (i < shuffledVoices.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }
    
    setTimeout(() => setIsPlaying(false), 500)
    // Note: isPlayingAll stays true to keep the highlight active
  }

  // Voice badge mapping (Periodic Table style)
  const voiceBadgeMap: Record<Voice, string> = {
    alloy: 'Al',
    ash: 'As',
    coral: 'Co',
    echo: 'Ec',
    fable: 'Fa',
    nova: 'No',
    onyx: 'On',
    sage: 'Sa',
    shimmer: 'Sh',
  }

  // Voice color mapping (vibrant, distinct colors - not gray shades)
  const voiceColorMap: Record<Voice, string> = {
    alloy: 'bg-blue-400',      // Blue
    ash: 'bg-purple-500',      // Purple
    coral: 'bg-pink-400',      // Pink
    echo: 'bg-indigo-400',     // Indigo
    fable: 'bg-violet-400',    // Violet
    nova: 'bg-rose-400',       // Rose
    onyx: 'bg-slate-600',      // Dark slate (kept for contrast)
    sage: 'bg-emerald-500',    // Green
    shimmer: 'bg-amber-400',   // Gold/Amber
  }
  
  // Echo cursor (sound waves + ECHO text) for when audio is playing
  const echoCursor = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'56\' height=\'36\' viewBox=\'0 0 56 36\'%3E%3Crect width=\'56\' height=\'36\' fill=\'%231e293b\' fill-opacity=\'0.9\' rx=\'4\'/%3E%3Cg%3E%3Cg transform=\'translate(28, 0)\'%3E%3Cpath fill=\'%2306b6d4\' d=\'M-16 10v6h2v-6h-2zm3 1v4h2v-4h-2zm3-1v6h2v-6h-2zm3-1v6h2v-6h-2zm3 1v4h2v-4h-2zm3-2v8h2v-8h-2z\'/%3E%3C/g%3E%3Ctext x=\'28\' y=\'30\' font-size=\'10\' fill=\'%2306b6d4\' font-weight=\'bold\' text-anchor=\'middle\' font-family=\'Arial, sans-serif\'%3EECHO%3C/text%3E%3C/g%3E%3C/svg%3E") 28 18, auto'
  
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
      case 'solid': return '💎 Mastered'
      case 'hollow': return '🔥 Learning'
      default: return '🪨 RAW'
    }
  }

  const getStatusTooltip = () => {
    switch (block.status) {
      case 'solid': return 'Mastered'
      case 'hollow': return 'Learning'
      default: return 'NEW WORDS'
    }
  }
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-700 flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* SECTION 1: Unified Top Bar */}
            <div className="flex items-center justify-between mb-4">
              {/* Left: Status + Translation Toggle */}
              <div className="flex items-center gap-2">
                <span 
                  className={`px-4 py-1.5 rounded-lg text-sm font-bold bg-gradient-to-r ${getStatusColor()} text-white`}
                  title={getStatusTooltip()}
                >
                  {getStatusLabel()}
                </span>
                {/* Translation Toggle Badge */}
                {block.translation && (
                  <button
                    onClick={() => setShowTranslation(!showTranslation)}
                    className={`px-2 py-1 rounded-md text-xs font-medium transition-all ${
                      showTranslation
                        ? 'bg-slate-700 text-slate-300'
                        : 'bg-slate-800/50 text-slate-600 hover:bg-slate-800/70'
                    }`}
                    title={showTranslation ? 'Hide translation' : 'Show translation'}
                  >
                    {showTranslation ? block.translation : '塊'}
                  </button>
                )}
              </div>
              
              {/* Right: Category + Stars + Close */}
              <div className="flex items-center gap-3">
                <div className="text-sm text-slate-300">
                  {block.category || '基礎'}
                  {categoryStats && (
                    <span className="ml-2 text-slate-500">
                      {categoryStats.learned}/{categoryStats.total}
                    </span>
                  )}
                </div>
                <div className="text-slate-300">
                  {block.difficulty === 1 ? '⭐' : block.difficulty === 2 ? '⭐⭐' : '⭐⭐⭐'}
                </div>
                <button
                  onClick={onClose}
                  className="text-slate-400 hover:text-white transition-colors p-2"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* SECTION 2: Unified Center - Immersive Core */}
            <div className="flex flex-col items-center justify-center mb-6 overflow-hidden">
              {/* Hero Emoji - Wall-to-Wall */}
              <div className="-mx-6 mb-4 w-full text-center overflow-hidden py-2">
                <motion.span 
                  className="block drop-shadow-2xl leading-none"
                  style={{ fontSize: 'min(40vw, 12rem)' }}
                  animate={isPlaying ? { 
                    scale: [1, 1.1, 1],
                    filter: ['brightness(1)', 'brightness(1.3)', 'brightness(1)']
                  } : {}}
                  transition={{ duration: 0.3 }}
                >
                  {block.emoji || '📝'}
                </motion.span>
              </div>
              
              {/* Word Row: English + Play Icon (clickable) */}
              <button
                onClick={handlePlayWord}
                disabled={!preloadComplete || isPlaying}
                className="flex items-center gap-3 mb-4 group"
                style={isPlaying ? { cursor: echoCursor } : undefined}
              >
                <h2 className="text-4xl font-black text-white group-hover:text-cyan-400 transition-colors">
                  {block.word}
                </h2>
                <div className={`transition-all ${isPlaying ? 'animate-pulse' : ''}`}>
                  <svg 
                    className={`w-8 h-8 ${preloadComplete ? 'text-cyan-400' : 'text-slate-500'}`}
                    fill="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </button>
              
              {/* FORGE Button - Just below word text */}
              {block?.status === 'raw' && onAddToSmelting && (
                <div className="relative w-full mb-6">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => onAddToSmelting(block.sense_id, block.word)}
                    onMouseEnter={handleForgeMouseEnter}
                    onMouseLeave={handleForgeMouseLeave}
                    className="w-full h-12 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-lg flex items-center justify-center"
                  >
                    <span className="text-lg">🔥 FORGE</span>
                  </motion.button>
                  {/* Hover tooltip - appears after 2 seconds */}
                  {showHelpTooltip && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800/95 backdrop-blur-sm rounded-lg border border-slate-700 shadow-xl z-50 whitespace-nowrap"
                    >
                      <div className="text-xs text-white font-medium">Add to smelting</div>
                      <div className="text-xs text-slate-400 mt-0.5">加入列表</div>
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
                        <div className="w-2 h-2 bg-slate-800 border-r border-b border-slate-700 transform rotate-45"></div>
                      </div>
                    </motion.div>
                  )}
                </div>
              )}
            </div>
            
            {/* SECTION 3: Unified Bottom - Actions */}
            <div className="space-y-2">
              {/* Voice Grid - Ghost Style */}
              <div className="w-full">
                <div className="grid grid-rows-2 grid-cols-5 gap-3 w-full" style={{ height: 'calc(3rem * 1.6)' }}>
                {/* 9 Voice badges */}
                {VOICES.map((voice) => (
                  <button
                    key={voice}
                    onClick={() => handlePlayWithVoice(voice)}
                    disabled={!preloadComplete || isPlaying}
                    className={`w-full h-full rounded-lg flex items-center justify-center text-xs font-bold transition-all border relative ${
                      !preloadComplete
                        ? 'bg-transparent border-slate-700 text-slate-600 opacity-50 cursor-not-allowed'
                        : isPlaying
                        ? 'bg-transparent border-slate-600 text-slate-400 opacity-70'
                        : selectedVoice === voice
                        ? `${voiceColorMap[voice]} border-transparent text-white ring-2 ring-cyan-400 ring-offset-2 ring-offset-slate-800`
                        : 'bg-transparent border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white'
                    }`}
                    style={isPlaying ? { cursor: echoCursor } : undefined}
                    title={voice}
                  >
                    {voiceBadgeMap[voice]}
                  </button>
                ))}
                {/* Play All button (10th) */}
                <button
                  onClick={handlePlayAllVoices}
                  disabled={!preloadComplete || isPlaying}
                  className={`w-full h-full rounded-lg flex items-center justify-center transition-all border ${
                    !preloadComplete
                      ? 'bg-transparent border-slate-700 text-slate-600 opacity-50 cursor-not-allowed'
                      : isPlaying
                      ? 'bg-transparent border-slate-600 text-slate-400 opacity-70'
                      : isPlayingAll
                      ? 'bg-cyan-500 border-transparent text-white ring-2 ring-cyan-400 ring-offset-2 ring-offset-slate-800'
                      : 'bg-transparent border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white'
                  }`}
                  style={isPlaying ? { cursor: echoCursor } : undefined}
                  title="Play all voices (random order)"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
                </div>
              </div>

              {/* VERIFY Button (for hollow status) */}
              {block?.status === 'hollow' && onStartQuiz && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onStartQuiz(block.sense_id)}
                  className="w-full h-12 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl flex items-center justify-center relative"
                >
                  <span className="text-xs opacity-40 absolute left-4">開始驗證</span>
                  <span className="text-lg">⚒️ VERIFY</span>
                </motion.button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default EmojiWordDetail

