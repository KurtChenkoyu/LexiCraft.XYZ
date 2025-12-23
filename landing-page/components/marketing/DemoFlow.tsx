'use client'

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { Block } from '@/types/mine'
import { audioService, VOICES, Voice, DEFAULT_VOICE, AUDIO_PATHS } from '@/lib/audio-service'
import { CampaignConfig, trackCampaignEvent } from '@/lib/campaign-config'
import { useAuth } from '@/contexts/AuthContext'

// Demo words array - 12 diverse words (all from emoji pack with audio)
const DEMO_WORDS: Block[] = [
  { sense_id: 'avocado.emoji.01', word: 'avocado', emoji: '🥑', translation: '酪梨', category: 'food', difficulty: 3, status: 'raw', definition_preview: 'A green fruit with a large seed', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'broccoli.emoji.01', word: 'broccoli', emoji: '🥦', translation: '花椰菜', category: 'food', difficulty: 3, status: 'raw', definition_preview: 'A green vegetable with a tree-like shape', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'crocodile.emoji.01', word: 'crocodile', emoji: '🐊', translation: '鱷魚', category: 'animals', difficulty: 3, status: 'raw', definition_preview: 'A large reptile with sharp teeth', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'kangaroo.emoji.01', word: 'kangaroo', emoji: '🦘', translation: '袋鼠', category: 'animals', difficulty: 3, status: 'raw', definition_preview: 'An Australian animal that hops', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'helicopter.emoji.01', word: 'helicopter', emoji: '🚁', translation: '直升機', category: 'objects', difficulty: 3, status: 'raw', definition_preview: 'A flying vehicle with rotating blades', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'octopus.emoji.01', word: 'octopus', emoji: '🐙', translation: '章魚', category: 'animals', difficulty: 2, status: 'raw', definition_preview: 'A sea animal with eight arms', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'dolphin.emoji.01', word: 'dolphin', emoji: '🐬', translation: '海豚', category: 'animals', difficulty: 2, status: 'raw', definition_preview: 'A smart sea mammal', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'giraffe.emoji.01', word: 'giraffe', emoji: '🦒', translation: '長頸鹿', category: 'animals', difficulty: 2, status: 'raw', definition_preview: 'A tall African animal with a long neck', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'pineapple.emoji.01', word: 'pineapple', emoji: '🍍', translation: '鳳梨', category: 'food', difficulty: 2, status: 'raw', definition_preview: 'A tropical fruit with a spiky top', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'robot.emoji.01', word: 'robot', emoji: '🤖', translation: '機器人', category: 'objects', difficulty: 2, status: 'raw', definition_preview: 'A machine that can do tasks', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'ghost.emoji.01', word: 'ghost', emoji: '👻', translation: '鬼', category: 'objects', difficulty: 2, status: 'raw', definition_preview: 'A spirit of a dead person', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'rocket.emoji.01', word: 'rocket', emoji: '🚀', translation: '火箭', category: 'objects', difficulty: 2, status: 'raw', definition_preview: 'A vehicle that travels through space', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
]

type Stage = 'grid' | 'mining' | 'verifying' | 'result'

interface DemoFlowProps {
  campaign: CampaignConfig
}

// Helper to capitalize word for display
const capitalizeWord = (word: string): string => {
  return word.charAt(0).toUpperCase() + word.slice(1)
}

/**
 * Preload single voice for a word (Ghost Audio Strategy)
 * Fixed: Properly loads audio and verifies readiness
 */
async function preloadWordVoice(word: string, voice: Voice): Promise<void> {
  if (typeof window === 'undefined') return
  
  const cleanWord = word.toLowerCase().replace(/\s+/g, '_')
  const path = `${AUDIO_PATHS.emoji}/${cleanWord}_${voice}.mp3`
  const audioCache = audioService.getAudioCache()
  
  // Skip if already cached and ready
  const existing = audioCache.get(path)
  if (existing && existing.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
    return
  }
  
  const audio = new Audio()
  audio.preload = 'auto'
  audio.src = path
  // CRITICAL: Explicitly trigger loading
  audio.load()
  
  return new Promise<void>((resolve, reject) => {
    let resolved = false
    
    const cleanup = () => {
      if (resolved) return
      resolved = true
      audio.removeEventListener('canplaythrough', onReady)
      audio.removeEventListener('error', onError)
      audio.removeEventListener('loadstart', onLoadStart)
    }
    
    const onReady = () => {
      cleanup()
      // Verify audio is actually ready before caching
      if (audio.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
        audioCache.set(path, audio)
        resolve()
      } else {
        // Audio loaded but not ready - wait a bit more
        setTimeout(() => {
          if (audio.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
            audioCache.set(path, audio)
            resolve()
          } else {
            reject(new Error(`Audio not ready: ${path}`))
          }
        }, 500)
      }
    }
    
    const onError = (e: Event) => {
      cleanup()
      
      // Check if this is a 404 (missing file) - expected in MVP, handle silently
      // MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED (code 4) typically means 404
      const is404 = audio.error?.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED ||
                    audio.error?.code === 4 ||
                    audio.networkState === HTMLMediaElement.NETWORK_NO_SOURCE
      
      if (!is404) {
        // Real error (network issue, etc.) - log for debugging
        console.warn(`Failed to preload audio (non-404): ${path}`, {
          error: audio.error,
          networkState: audio.networkState,
          event: e
        })
      }
      
      // Resolve silently for all errors (don't reject) - missing files are expected in MVP
      // Don't cache failed audio elements
      resolve()
    }
    
    const onLoadStart = () => {
      // Audio started loading - good sign
      audio.removeEventListener('loadstart', onLoadStart)
    }
    
    audio.addEventListener('canplaythrough', onReady, { once: true })
    audio.addEventListener('error', onError, { once: true })
    audio.addEventListener('loadstart', onLoadStart, { once: true })
    
    // Timeout after 5 seconds (increased from 3)
    setTimeout(() => {
      cleanup()
      if (audio.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
        audioCache.set(path, audio)
        resolve()
      } else {
        // Check if it's a 404 - if so, resolve silently
        const is404 = audio.error?.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED ||
                      audio.error?.code === 4 ||
                      audio.networkState === HTMLMediaElement.NETWORK_NO_SOURCE
        
        if (!is404 && audio.error) {
          // Real timeout with error - log for debugging
          console.warn(`Audio preload timeout (non-404): ${path}`, {
            error: audio.error,
            networkState: audio.networkState,
            readyState: audio.readyState
          })
        }
        
        // Resolve silently for all timeouts (missing files are expected in MVP)
        resolve()
      }
    }, 5000)
  })
}

/**
 * Preload all voices for a word (called on selection)
 */
async function preloadAllVoicesForWord(word: string): Promise<void> {
  const promises = VOICES.map(voice => 
    preloadWordVoice(word, voice).catch(err => {
      console.warn(`Failed to preload ${word} with voice ${voice}:`, err)
      // Continue with other voices even if one fails
    })
  )
  await Promise.allSettled(promises)
}

export function DemoFlow({ campaign }: DemoFlowProps) {
  const { user } = useAuth()
  const [stage, setStage] = useState<Stage>('grid')
  const [selectedWord, setSelectedWord] = useState<Block | null>(null)
  const [showChinese, setShowChinese] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isPreloadingVoices, setIsPreloadingVoices] = useState(false)
  const [showSparkAnimation, setShowSparkAnimation] = useState(false)
  const [mcqOptions, setMcqOptions] = useState<Block[]>([])
  const sparkAnimationRef = useRef<NodeJS.Timeout | null>(null)

  // Ghost Audio Strategy: Preload default voice (alloy) for all 12 words on mount
  useEffect(() => {
    const preloadDefaultVoices = async () => {
      try {
        const words = DEMO_WORDS.map(w => w.word)
        console.log('🎵 [DemoFlow] Preloading default voices for', words.length, 'words...')
        
        // Preload words in parallel (browser handles concurrency)
        // Note: preloadWordVoice now resolves (not rejects) for errors, so catch won't fire
        // This is intentional - missing files are expected in MVP
        const preloadPromises = words.map(word => preloadWordVoice(word, 'alloy'))
        
        await Promise.allSettled(preloadPromises)
        
        // Preload success/error sounds
        await audioService.preloadSfx(['correct', 'wrong'])
        
        console.log('✅ [DemoFlow] Audio preload complete')
      } catch (err) {
        console.warn('⚠️ [DemoFlow] Audio preload had errors (non-critical):', err)
      }
    }
    preloadDefaultVoices()
  }, [])

  // When word is selected, preload all voices in background
  useEffect(() => {
    if (selectedWord && stage === 'mining') {
      setIsPreloadingVoices(true)
      preloadAllVoicesForWord(selectedWord.word)
        .then(() => setIsPreloadingVoices(false))
        .catch(() => setIsPreloadingVoices(false))
    }
  }, [selectedWord, stage])

  // Generate MCQ options when entering verification stage
  useEffect(() => {
    if (stage === 'verifying' && selectedWord) {
      // Create options: correct answer + 2 random distractors
      const distractors = DEMO_WORDS
        .filter(w => w.sense_id !== selectedWord.sense_id)
        .sort(() => Math.random() - 0.5)
        .slice(0, 2)
      
      const options = [selectedWord, ...distractors].sort(() => Math.random() - 0.5)
      setMcqOptions(options)
      
      // Auto-play selected word audio (random voice) after ensuring it's ready
      const playAudioWhenReady = async () => {
        // Wait a bit for any pending preloads
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // Try to ensure the audio is preloaded
        const randomVoice = VOICES[Math.floor(Math.random() * VOICES.length)]
        const cleanWord = selectedWord.word.toLowerCase().replace(/\s+/g, '_')
        const path = `${AUDIO_PATHS.emoji}/${cleanWord}_${randomVoice}.mp3`
        const audioCache = audioService.getAudioCache()
        
        // Check if audio is cached and ready
        const cached = audioCache.get(path)
        if (!cached || cached.readyState < HTMLMediaElement.HAVE_ENOUGH_DATA) {
          // Preload it now if not ready
          try {
            await preloadWordVoice(selectedWord.word, randomVoice)
          } catch (err) {
            console.warn('Failed to preload audio for verification:', err)
          }
        }
        
        // Now play it
        audioService.playWord(selectedWord.word, 'emoji', randomVoice).catch(err => {
          console.warn('Failed to play audio in verification:', err)
        })
      }
      
      playAudioWhenReady()
    }
  }, [stage, selectedWord])

  const handleWordSelect = (word: Block) => {
    setSelectedWord(word)
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'word_selected',
      word: word.word,
      emoji: word.emoji,
    })
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'demo_stage_mining',
    })
    setStage('mining')
  }

  const handleForge = useCallback(() => {
    if (!selectedWord) return
    
    setShowSparkAnimation(true)
    audioService.playSfx('correct').catch(() => {})
    
    if (sparkAnimationRef.current) {
      clearTimeout(sparkAnimationRef.current)
    }
    sparkAnimationRef.current = setTimeout(() => {
      setShowSparkAnimation(false)
    }, 500)
    
    // Transition to verification stage
    setTimeout(() => {
      trackCampaignEvent(campaign, 'ctaClick', {
        action: 'demo_stage_verifying',
      })
      setStage('verifying')
    }, 600)
  }, [selectedWord])

  const handleMcqAnswer = async (option: Block) => {
    if (!selectedWord || isPlaying) return
    
    setSelectedAnswer(option.sense_id)
    setIsPlaying(true)
    
    const isCorrect = option.sense_id === selectedWord.sense_id
    
    if (isCorrect) {
      await audioService.playSfx('correct')
      trackCampaignEvent(campaign, 'ctaClick', {
        action: 'mcq_answered',
        correct: true,
        word: selectedWord.word,
      })
      
      // Transition to result stage after 1 second
      setTimeout(() => {
        trackCampaignEvent(campaign, 'ctaClick', {
          action: 'demo_stage_result',
        })
        trackCampaignEvent(campaign, 'ctaClick', {
          action: 'demo_completed',
          word: selectedWord.word,
        })
        setStage('result')
      }, 1000)
    } else {
      await audioService.playSfx('wrong')
      trackCampaignEvent(campaign, 'ctaClick', {
        action: 'mcq_answered',
        correct: false,
        word: selectedWord.word,
      })
      
      // Allow retry after error sound
      setTimeout(() => {
        setSelectedAnswer(null)
        setIsPlaying(false)
      }, 1000)
    }
  }

  const handleSaveProgress = () => {
    trackCampaignEvent(campaign, 'signupStart', {
      source: 'demo_funnel',
      action: 'cta_clicked',
      word: selectedWord?.word,
    })
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

  // Echo cursor for disabled buttons
  const echoCursor = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'56\' height=\'36\' viewBox=\'0 0 56 36\'%3E%3Crect width=\'56\' height=\'36\' fill=\'%231e293b\' fill-opacity=\'0.9\' rx=\'4\'/%3E%3Cg transform=\'translate(0, -2)\'%3E%3Cpath fill=\'%2306b6d4\' d=\'M10 10v6h2v-6H10zm5 1v4h2v-4h-2zm5-1v6h2v-6h-2zm5-1v6h2v-6h-2zm5 1v4h2v-4h-2zm5-2v8h2v-8h-2z\' transform=\'translate(-4, 0)\'/%3E%3Ctext x=\'28\' y=\'30\' font-size=\'10\' fill=\'%2306b6d4\' font-weight=\'bold\' text-anchor=\'middle\' font-family=\'Arial, sans-serif\'%3EECHO%3C/text%3E%3C/g%3E%3C/svg%3E") 28 18, auto'

  return (
    <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-700 flex flex-col min-h-[500px]">
      {/* Language Toggle Button */}
      <button
        onClick={() => setShowChinese(!showChinese)}
        className="absolute top-4 right-4 text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded"
        title={showChinese ? 'Turn on English' : 'Turn on Chinese'}
      >
        {showChinese ? 'Turn on English' : '開啟中文'}
      </button>

      <AnimatePresence mode="wait">
        {/* STAGE 0: Mini Mining Grid */}
        {stage === 'grid' && (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full"
          >
            <div className="text-center mb-4">
              <h3 className="text-xl font-bold text-white mb-2">
                {showChinese ? '選擇一個單字開始' : 'Pick a word to start'}
              </h3>
              <p className="text-sm text-slate-400">
                {showChinese ? '點擊任意字塊開始學習' : 'Click any word to begin'}
              </p>
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              {DEMO_WORDS.map((word) => (
                <motion.button
                  key={word.sense_id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleWordSelect(word)}
                  className="bg-slate-700/50 hover:bg-slate-700 rounded-lg p-4 flex flex-col items-center justify-center border border-slate-600 transition-all"
                >
                  <span className="text-3xl mb-2">{word.emoji}</span>
                  <span className="text-sm font-bold text-white">{capitalizeWord(word.word)}</span>
                  <span className="text-xs text-slate-400 mt-1">🪨 RAW</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        {/* STAGE 1: Mining (Word Detail) */}
        {stage === 'mining' && selectedWord && (
          <motion.div
            key="mining"
            initial={{ opacity: 0, rotateY: -90 }}
            animate={{ opacity: 1, rotateY: 0 }}
            exit={{ opacity: 0, rotateY: 90 }}
            transition={{ duration: 0.6, ease: 'easeInOut' }}
            className="w-full"
          >
            {/* Forge Spark Animation */}
            <AnimatePresence>
              {showSparkAnimation && (
                <>
                  {/* Particle burst */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 pointer-events-none z-40"
                  >
                    {[...Array(8)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="absolute w-2 h-2 bg-amber-400 rounded-full"
                        style={{ left: '50%', top: '50%' }}
                        animate={{
                          x: [0, Math.cos((i * 45 * Math.PI) / 180) * 40],
                          y: [0, Math.sin((i * 45 * Math.PI) / 180) * 40],
                          scale: [1, 0],
                        }}
                        transition={{ duration: 0.5, delay: 0 }}
                      />
                    ))}
                  </motion.div>
                  
                  {/* White flash overlay */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0, 0.5, 0] }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.05 }}
                    className="absolute inset-0 bg-white pointer-events-none z-30 rounded-3xl"
                  />
                </>
              )}
            </AnimatePresence>

            {/* Top Bar */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setSelectedWord(null)
                    setStage('grid')
                  }}
                  className="text-slate-400 hover:text-white transition-colors p-2 -ml-2"
                  title={showChinese ? '返回' : 'Back'}
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <span className="px-4 py-1.5 rounded-lg text-sm font-bold bg-gradient-to-r from-slate-500 to-slate-600 text-white">
                  🪨 RAW
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-sm text-slate-300">
                  {selectedWord.category || '基礎'}
                </div>
                <div className="text-slate-300">
                  {selectedWord.difficulty === 1 ? '⭐' : selectedWord.difficulty === 2 ? '⭐⭐' : '⭐⭐⭐'}
                </div>
              </div>
            </div>

            {/* Hero Emoji */}
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
                {selectedWord.emoji || '📝'}
              </motion.span>
            </div>
            
            {/* Word + Play Button */}
            <button
              onClick={() => {
                setIsPlaying(true)
                audioService.playWord(selectedWord.word, 'emoji', DEFAULT_VOICE)
                  .then(() => setTimeout(() => setIsPlaying(false), 500))
                  .catch(() => setIsPlaying(false))
              }}
              disabled={isPlaying}
              className="flex items-center gap-3 mb-4 group w-full justify-center"
              style={isPlaying ? { cursor: echoCursor } : undefined}
            >
              <h2 className="text-4xl font-black text-white group-hover:text-cyan-400 transition-colors">
                {capitalizeWord(selectedWord.word)}
              </h2>
              <div className={`transition-all ${isPlaying ? 'animate-pulse' : ''}`}>
                <svg 
                  className={`w-8 h-8 ${isPlaying ? 'text-cyan-400' : 'text-slate-500'}`}
                  fill="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
            </button>

            {/* FORGE Button */}
            <div className="relative w-full mb-6">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleForge}
                className="w-full h-12 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-lg flex items-center justify-center"
              >
                <span className="text-lg">🔥 FORGE</span>
              </motion.button>
            </div>
            
            {/* Voice Grid */}
            <div className="w-full">
              {isPreloadingVoices ? (
                <div className="text-center text-slate-400 text-sm py-4">
                  {showChinese ? '載入語音中...' : 'Loading voices...'}
                </div>
              ) : (
                <div className="grid grid-rows-2 grid-cols-5 gap-3 w-full" style={{ height: 'calc(3rem * 1.6)' }}>
                  {VOICES.map((voice) => (
                    <button
                      key={voice}
                      onClick={() => {
                        setIsPlaying(true)
                        audioService.playWord(selectedWord.word, 'emoji', voice)
                          .then(() => setTimeout(() => setIsPlaying(false), 500))
                          .catch(() => setIsPlaying(false))
                      }}
                      disabled={isPlaying}
                      className={`w-full h-full rounded-lg flex items-center justify-center text-xs font-bold transition-all border ${
                        isPlaying
                          ? 'bg-transparent border-slate-600 text-slate-400 opacity-70'
                          : 'bg-transparent border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white'
                      }`}
                      style={isPlaying ? { cursor: echoCursor } : undefined}
                      title={voice}
                    >
                      {voiceBadgeMap[voice]}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* STAGE 2: Verification (MCQ Quiz) */}
        {stage === 'verifying' && selectedWord && mcqOptions.length > 0 && (
          <motion.div
            key="verifying"
            initial={{ opacity: 0, rotateY: -90 }}
            animate={{ opacity: 1, rotateY: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.6, ease: 'easeInOut' }}
            className="w-full"
          >
            {/* Question Card - Match actual app design exactly */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 mb-6 border border-slate-700 shadow-xl"
            >
              {/* Category Badge */}
              <div className="text-center mb-2">
                <span className="px-3 py-1 rounded-full bg-slate-700/50 text-slate-400 text-xs uppercase tracking-wide">
                  {selectedWord.category || '基礎'}
                </span>
              </div>

              {/* Question Content - Match actual app */}
              <div className="text-center py-6">
                <p className="text-slate-400 text-sm mb-2">
                  {showChinese ? '哪個表情符號符合聲音？' : 'Which emoji matches the sound?'}
                </p>
                <div className="flex items-center justify-center gap-3">
                  <h2 className="text-4xl font-bold text-white tracking-wide">
                    {capitalizeWord(selectedWord.word)}
                  </h2>
                  {/* Speaker button - Play again (matches actual app) */}
                  <button
                    onClick={() => {
                      const randomVoice = VOICES[Math.floor(Math.random() * VOICES.length)]
                      audioService.playWord(selectedWord.word, 'emoji', randomVoice).catch(() => {})
                    }}
                    className="p-2 rounded-full bg-slate-700 hover:bg-slate-600 text-cyan-400 transition-colors"
                    aria-label={showChinese ? '播放發音' : 'Play pronunciation'}
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Difficulty Stars - Match actual app */}
              <div className="flex justify-center gap-1">
                {[1, 2, 3].map((star) => (
                  <span
                    key={star}
                    className={`text-lg ${
                      star <= (selectedWord.difficulty || 1) ? 'text-amber-400' : 'text-slate-700'
                    }`}
                  >
                    ★
                  </span>
                ))}
              </div>
            </motion.div>
            
            {/* Options Grid - Match actual app (2 columns for emoji) */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              {mcqOptions.map((option) => {
                const isCorrect = option.sense_id === selectedWord.sense_id
                const isSelected = selectedAnswer === option.sense_id
                const hasFeedback = selectedAnswer !== null
                
                return (
                  <motion.button
                    key={option.sense_id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: mcqOptions.indexOf(option) * 0.1 }}
                    whileHover={!hasFeedback ? { scale: 1.05 } : {}}
                    whileTap={!hasFeedback ? { scale: 0.95 } : {}}
                    onClick={() => handleMcqAnswer(option)}
                    disabled={isPlaying || hasFeedback}
                    className={`relative flex items-center justify-center rounded-2xl border-4 transition-all duration-200 min-h-[100px] ${
                      hasFeedback
                        ? isCorrect
                          ? 'bg-emerald-500/30 border-emerald-400'
                          : isSelected
                          ? 'bg-red-500/30 border-red-400'
                          : 'bg-slate-800/30 border-slate-700 opacity-50'
                        : isSelected
                        ? 'bg-cyan-500/20 border-cyan-400 scale-95'
                        : 'bg-slate-800/50 border-slate-600 hover:border-slate-500 hover:bg-slate-700/50'
                    }`}
                  >
                    <span className="text-5xl">{option.emoji}</span>
                    
                    {/* Correct/Incorrect indicator - Match actual app */}
                    <AnimatePresence>
                      {hasFeedback && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                          className={`absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center text-lg font-bold ${
                            isCorrect
                              ? 'bg-emerald-500 text-white'
                              : isSelected
                              ? 'bg-red-500 text-white'
                              : 'hidden'
                          }`}
                        >
                          {isCorrect ? '✓' : '✗'}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.button>
                )
              })}
            </div>
            
            {/* Result Feedback - Match actual app */}
            <AnimatePresence>
              {selectedAnswer !== null && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={`p-4 rounded-2xl text-center mb-4 ${
                    selectedAnswer === selectedWord.sense_id
                      ? 'bg-emerald-500/20 border border-emerald-500/50'
                      : 'bg-red-500/20 border border-red-500/50'
                  }`}
                >
                  <div className="text-4xl mb-2">
                    {selectedAnswer === selectedWord.sense_id ? '🎉' : '😅'}
                  </div>
                  <p className={`font-bold text-lg ${
                    selectedAnswer === selectedWord.sense_id ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {selectedAnswer === selectedWord.sense_id 
                      ? (showChinese ? '太棒了！' : 'Great!')
                      : (showChinese ? '再試一次！' : 'Try again!')
                    }
                  </p>
                  {selectedAnswer !== selectedWord.sense_id && (
                    <p className="text-slate-400 text-sm mt-1">
                      {showChinese ? '正確答案：' : 'Correct answer: '}
                      {selectedWord.emoji}
                    </p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Reserved message for full verification flow */}
            {selectedAnswer === selectedWord.sense_id && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-center"
              >
                <p className="text-xs text-slate-400">
                  {showChinese 
                    ? '完整驗證流程（多題測驗、進度追蹤）僅限已註冊用戶'
                    : 'Full verification flow (multi-question quiz, progress tracking) reserved for signed-in users'
                  }
                </p>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* STAGE 3: Result (Success + CTA) */}
        {stage === 'result' && selectedWord && (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            className="w-full flex flex-col items-center justify-center text-center"
          >
            <h3 className="text-4xl font-black text-white mb-2">
              {showChinese ? '記憶鏈已啟動！🔗' : 'Memory Chain Started! 🔗'}
            </h3>
            
            <div className="text-6xl mb-6">{selectedWord.emoji}</div>
            
            <p className="text-lg text-slate-300 mb-6 px-4">
              {showChinese 
                ? `你已經學會了「${selectedWord.translation}」！為了讓記憶持久，LexiCraft 會在 **1 天**、**3 天** 和 **1 週** 後提醒你複習。`
                : `You've learned '${capitalizeWord(selectedWord.word)}'! To make it stick, LexiCraft will remind you to review this in **1 day**, **3 days**, and **1 week**.`
              }
            </p>
            
            <Link
              href={`/signup?utm_source=demo&utm_medium=micro_journey&utm_campaign=${selectedWord.word.toLowerCase()}_demo`}
              onClick={handleSaveProgress}
              className="w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg"
            >
              {showChinese ? '建立免費帳號以保存進度' : 'Create Free Account to Save Progress'}
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

