'use client'

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { Block } from '@/types/mine'
import { audioService, VOICES, Voice, DEFAULT_VOICE, AUDIO_PATHS } from '@/lib/audio-service'
import { CampaignConfig, trackCampaignEvent } from '@/lib/campaign-config'
import { useAuth } from '@/contexts/AuthContext'

// Demo words array - 12 diverse words for the funnel
// Note: Using Partial<Block> would be cleaner, but we'll add required fields for type safety
const DEMO_WORDS: Block[] = [
  { sense_id: 'rocket.demo.01', word: 'Rocket', emoji: '🚀', translation: '火箭', category: 'Travel', difficulty: 1, status: 'raw', definition_preview: 'A vehicle that travels through space', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
  { sense_id: 'avocado.demo.01', word: 'Avocado', emoji: '🥑', translation: '酪梨', category: 'Food', difficulty: 2, status: 'raw', definition_preview: 'A green fruit with a large seed', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'ghost.demo.01', word: 'Ghost', emoji: '👻', translation: '鬼', category: 'Fantasy', difficulty: 1, status: 'raw', definition_preview: 'A spirit of a dead person', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
  { sense_id: 'pizza.demo.01', word: 'Pizza', emoji: '🍕', translation: '比薩', category: 'Food', difficulty: 1, status: 'raw', definition_preview: 'A flat bread with toppings', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
  { sense_id: 'trex.demo.01', word: 'T-Rex', emoji: '🦖', translation: '暴龍', category: 'Animal', difficulty: 3, status: 'raw', definition_preview: 'A large meat-eating dinosaur', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'robot.demo.01', word: 'Robot', emoji: '🤖', translation: '機器人', category: 'Tech', difficulty: 1, status: 'raw', definition_preview: 'A machine that can do tasks', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
  { sense_id: 'rainbow.demo.01', word: 'Rainbow', emoji: '🌈', translation: '彩虹', category: 'Nature', difficulty: 1, status: 'raw', definition_preview: 'A colorful arc in the sky', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
  { sense_id: 'popcorn.demo.01', word: 'Popcorn', emoji: '🍿', translation: '爆米花', category: 'Food', difficulty: 2, status: 'raw', definition_preview: 'Popped corn kernels', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'unicorn.demo.01', word: 'Unicorn', emoji: '🦄', translation: '獨角獸', category: 'Fantasy', difficulty: 3, status: 'raw', definition_preview: 'A mythical horse with a horn', rank: 3, base_xp: 25, connection_count: 0, total_value: 25 },
  { sense_id: 'fire.demo.01', word: 'Fire', emoji: '🔥', translation: '火', category: 'Nature', difficulty: 1, status: 'raw', definition_preview: 'Burning flames', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
  { sense_id: 'ninja.demo.01', word: 'Ninja', emoji: '🥷', translation: '忍者', category: 'Job', difficulty: 2, status: 'raw', definition_preview: 'A skilled warrior from Japan', rank: 2, base_xp: 15, connection_count: 0, total_value: 15 },
  { sense_id: 'cookie.demo.01', word: 'Cookie', emoji: '🍪', translation: '餅乾', category: 'Food', difficulty: 1, status: 'raw', definition_preview: 'A sweet baked treat', rank: 1, base_xp: 10, connection_count: 0, total_value: 10 },
]

const DEMO_GATE_THRESHOLD = 5
const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000

interface TrophyOverlayProps {
  forgedWords: Block[]
  onSaveProgress: () => void
  onKeepPlaying: () => void
  isLoggedIn: boolean
}

function TrophyOverlay({ forgedWords, onSaveProgress, onKeepPlaying, isLoggedIn }: TrophyOverlayProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 bg-slate-900/95 backdrop-blur-xl rounded-3xl flex items-center justify-center z-50 p-6"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="text-center max-w-sm w-full"
      >
        <h3 className="text-4xl font-black text-white mb-2">🎉 Great Job!</h3>
        <p className="text-xl text-slate-300 mb-4">You've forged 5 words!</p>
        
        {/* Stack of emojis */}
        <div className="flex justify-center gap-2 mb-6 text-4xl">
          {forgedWords.slice(0, 5).map((word, i) => (
            <motion.span
              key={word.sense_id}
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: i * 0.1, type: 'spring' }}
            >
              {word.emoji}
            </motion.span>
          ))}
        </div>
        
        <p className="text-slate-400 mb-6 text-sm">
          {isLoggedIn 
            ? "You're logged in! Your words are saved."
            : "Create a free account to save them to your permanent collection."
          }
        </p>
        
        <div className="space-y-3">
          {isLoggedIn ? (
            <Link
              href="/learner/mine"
              className="block w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl"
            >
              💾 View My Collection
            </Link>
          ) : (
            <Link
              href="/signup?utm_source=demo&utm_medium=funnel&utm_campaign=forge_gate"
              onClick={onSaveProgress}
              className="block w-full py-3 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl"
            >
              💾 Save My Progress
            </Link>
          )}
          
          <button
            onClick={onKeepPlaying}
            className="w-full py-2 text-slate-400 hover:text-white text-sm transition-colors"
          >
            No thanks, keep playing
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

interface DemoWordDetailProps {
  campaign: CampaignConfig
}

export function DemoWordDetail({ campaign }: DemoWordDetailProps) {
  const { user } = useAuth()
  const [currentWordIndex, setCurrentWordIndex] = useState(0)
  const [isForging, setIsForging] = useState(false)
  const [forgeCount, setForgeCount] = useState(0)
  const [showTrophyOverlay, setShowTrophyOverlay] = useState(false)
  const [forgedWords, setForgedWords] = useState<Block[]>([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [selectedVoice, setSelectedVoice] = useState<Voice>(DEFAULT_VOICE)
  const [isPlayingAll, setIsPlayingAll] = useState(false)
  const [isPreloading, setIsPreloading] = useState(false)
  const [preloadComplete, setPreloadComplete] = useState(false)
  const [showTranslation, setShowTranslation] = useState(false)
  const [showSparkAnimation, setShowSparkAnimation] = useState(false)
  const sparkAnimationRef = useRef<NodeJS.Timeout | null>(null)

  // Load persisted state on mount (with 24-hour expiry)
  useEffect(() => {
    try {
      const savedCount = localStorage.getItem('demo_forge_count')
      const savedWords = localStorage.getItem('demo_forged_words')
      const lastActive = localStorage.getItem('demo_last_active_at')
      
      const now = Date.now()
      const isExpired = lastActive && (now - parseInt(lastActive, 10)) > TWENTY_FOUR_HOURS
      
      if (isExpired) {
        // Clear expired state
        localStorage.removeItem('demo_forge_count')
        localStorage.removeItem('demo_forged_words')
        localStorage.removeItem('demo_last_active_at')
        setForgeCount(0)
        setForgedWords([])
      } else {
        // Load valid state
        if (savedCount) {
          const count = parseInt(savedCount, 10)
          setForgeCount(count)
          if (count === DEMO_GATE_THRESHOLD) {
            setShowTrophyOverlay(true)
          }
        }
        if (savedWords) {
          try {
            const words = JSON.parse(savedWords)
            setForgedWords(words)
          } catch (e) {
            console.warn('Failed to parse saved words:', e)
          }
        }
      }
    } catch (e) {
      // Handle localStorage errors (e.g., incognito mode)
      console.warn('localStorage access failed:', e)
    }
  }, [])

  // Preload audio for all demo words
  useEffect(() => {
    setIsPreloading(true)
    const words = DEMO_WORDS.map(w => w.word.toLowerCase().replace(/\s+/g, '_'))
    
    Promise.all([
      audioService.preloadWords(words, 'emoji'),
      audioService.preloadSfx(['correct']),
    ]).then(() => {
      setIsPreloading(false)
      setPreloadComplete(true)
    }).catch((err) => {
      console.warn('Audio preload failed (non-critical):', err)
      setIsPreloading(false)
      setPreloadComplete(true) // Continue anyway
    })
  }, [])

  const currentWord = DEMO_WORDS[currentWordIndex]

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

  // Voice color mapping
  const voiceColorMap: Record<Voice, string> = {
    alloy: 'bg-blue-400',
    ash: 'bg-purple-500',
    coral: 'bg-pink-400',
    echo: 'bg-indigo-400',
    fable: 'bg-violet-400',
    nova: 'bg-rose-400',
    onyx: 'bg-slate-700',
    sage: 'bg-emerald-500',
    shimmer: 'bg-amber-400',
  }

  // Echo cursor for disabled buttons
  const echoCursor = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'56\' height=\'36\' viewBox=\'0 0 56 36\'%3E%3Crect width=\'56\' height=\'36\' fill=\'%231e293b\' fill-opacity=\'0.9\' rx=\'4\'/%3E%3Cg transform=\'translate(0, -2)\'%3E%3Cpath fill=\'%2306b6d4\' d=\'M10 10v6h2v-6H10zm5 1v4h2v-4h-2zm5-1v6h2v-6h-2zm5-1v6h2v-6h-2zm5 1v4h2v-4h-2zm5-2v8h2v-8h-2z\' transform=\'translate(-4, 0)\'/%3E%3Ctext x=\'28\' y=\'30\' font-size=\'10\' fill=\'%2306b6d4\' font-weight=\'bold\' text-anchor=\'middle\' font-family=\'Arial, sans-serif\'%3EECHO%3C/text%3E%3C/g%3E%3C/svg%3E") 28 18, auto'

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
    if (!currentWord || !preloadComplete) return
    setIsPlaying(true)
    
    if (isPlayingAll) {
      const shuffledVoices = shuffleVoices([...VOICES])
      for (let i = 0; i < shuffledVoices.length; i++) {
        await audioService.playWord(currentWord.word, 'emoji', shuffledVoices[i])
        if (i < shuffledVoices.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }
    } else {
      await audioService.playWord(currentWord.word, 'emoji', selectedVoice)
    }
    
    setTimeout(() => setIsPlaying(false), 500)
  }, [currentWord, preloadComplete, selectedVoice, isPlayingAll])

  const handlePlayWithVoice = async (voice: Voice) => {
    if (!currentWord || !preloadComplete || isPlaying) return
    setSelectedVoice(voice)
    setIsPlayingAll(false)
    setIsPlaying(true)
    await audioService.playWord(currentWord.word, 'emoji', voice)
    setTimeout(() => setIsPlaying(false), 500)
  }

  const handlePlayAllVoices = async () => {
    if (!currentWord || !preloadComplete || isPlaying) return
    
    setIsPlayingAll(true)
    setSelectedVoice(DEFAULT_VOICE)
    setIsPlaying(true)
    const shuffledVoices = shuffleVoices([...VOICES])
    
    for (let i = 0; i < shuffledVoices.length; i++) {
      await audioService.playWord(currentWord.word, 'emoji', shuffledVoices[i])
      if (i < shuffledVoices.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }
    
    setTimeout(() => setIsPlaying(false), 500)
  }

  const handleForge = useCallback(() => {
    if (isForging || !currentWord) return
    
    setIsForging(true)
    setShowSparkAnimation(true)
    
    // Play success sound
    audioService.playSfx('correct').catch(() => {}) // Silent fail if missing
    
    // Clear spark animation after 500ms
    if (sparkAnimationRef.current) {
      clearTimeout(sparkAnimationRef.current)
    }
    sparkAnimationRef.current = setTimeout(() => {
      setShowSparkAnimation(false)
    }, 500)
    
    // Increment count and add word
    const newCount = forgeCount + 1
    const newForgedWords = [...forgedWords, currentWord]
    
    setForgeCount(newCount)
    setForgedWords(newForgedWords)
    
    // Persist to localStorage
    try {
      localStorage.setItem('demo_forge_count', newCount.toString())
      localStorage.setItem('demo_forged_words', JSON.stringify(newForgedWords))
      localStorage.setItem('demo_last_active_at', Date.now().toString())
    } catch (e) {
      console.warn('localStorage write failed:', e)
    }
    
    // Track analytics
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'word_forged',
      word: currentWord.word,
      count: newCount,
      forged_words: newForgedWords.map(w => w.word),
    })
    
    // Check if we've reached the gate
    if (newCount === DEMO_GATE_THRESHOLD) {
      // Show trophy overlay
      setShowTrophyOverlay(true)
      
      // Track gate reached
      trackCampaignEvent(campaign, 'signupStart', {
        source: 'demo_funnel',
        forged_words: newForgedWords.map(w => w.word),
      })
      
      setIsForging(false)
    } else {
      // Cycle to next word after animation
      setTimeout(() => {
        setCurrentWordIndex((prev) => (prev + 1) % DEMO_WORDS.length)
        setIsForging(false)
      }, 500)
    }
  }, [currentWord, forgeCount, forgedWords, isForging, campaign])

  const handleSaveProgress = () => {
    trackCampaignEvent(campaign, 'signupStart', {
      source: 'demo_funnel',
      action: 'signup_cta_clicked',
      forged_words: forgedWords.map(w => w.word),
    })
  }

  const handleKeepPlaying = () => {
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'keep_playing',
    })
    
    // Reset state
    try {
      localStorage.removeItem('demo_forge_count')
      localStorage.removeItem('demo_forged_words')
      localStorage.removeItem('demo_last_active_at')
    } catch (e) {
      console.warn('localStorage clear failed:', e)
    }
    
    setForgeCount(0)
    setForgedWords([])
    setShowTrophyOverlay(false)
  }

  if (!currentWord) return null

  return (
    <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-700 flex flex-col">
      {/* Forge Counter Badge */}
      {forgeCount > 0 && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-4 right-4 bg-amber-500 text-white text-xs font-bold px-3 py-1.5 rounded-full z-10"
        >
          Forged: {forgeCount}/5
        </motion.div>
      )}

      {/* Trophy Overlay */}
      <AnimatePresence>
        {showTrophyOverlay && (
          <TrophyOverlay
            forgedWords={forgedWords}
            onSaveProgress={handleSaveProgress}
            onKeepPlaying={handleKeepPlaying}
            isLoggedIn={!!user}
          />
        )}
      </AnimatePresence>

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

      {/* SECTION 1: Unified Top Bar */}
      <div className="flex items-center justify-between mb-4">
        {/* Left: Status + Translation Toggle */}
        <div className="flex items-center gap-2">
          <span className="px-4 py-1.5 rounded-lg text-sm font-bold bg-gradient-to-r from-slate-500 to-slate-600 text-white">
            🪨 RAW
          </span>
          {currentWord.translation && (
            <button
              onClick={() => setShowTranslation(!showTranslation)}
              className={`px-2 py-1 rounded-md text-xs font-medium transition-all ${
                showTranslation
                  ? 'bg-slate-700 text-slate-300'
                  : 'bg-slate-800/50 text-slate-600 hover:bg-slate-800/70'
              }`}
            >
              {showTranslation ? currentWord.translation : '塊'}
            </button>
          )}
        </div>
        
        {/* Right: Category + Stars */}
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-300">
            {currentWord.category || '基礎'}
          </div>
          <div className="text-slate-300">
            {currentWord.difficulty === 1 ? '⭐' : currentWord.difficulty === 2 ? '⭐⭐' : '⭐⭐⭐'}
          </div>
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
            {currentWord.emoji || '📝'}
          </motion.span>
        </div>
        
        {/* Word Row: English + Play Icon */}
        <button
          onClick={handlePlayWord}
          disabled={!preloadComplete || isPlaying}
          className="flex items-center gap-3 mb-4 group"
          style={isPlaying ? { cursor: echoCursor } : undefined}
        >
          <h2 className="text-4xl font-black text-white group-hover:text-cyan-400 transition-colors">
            {currentWord.word}
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

        {/* FORGE Button */}
        <div className="relative w-full mb-6">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleForge}
            disabled={isForging || showTrophyOverlay}
            className="w-full h-12 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-lg flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-lg">🔥 FORGE</span>
          </motion.button>
        </div>
      </div>
      
      {/* SECTION 3: Unified Bottom - Actions */}
      <div className="space-y-2">
        {/* Voice Grid */}
        <div className="w-full">
          <div className="grid grid-rows-2 grid-cols-5 gap-3 w-full" style={{ height: 'calc(3rem * 1.6)' }}>
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
            {/* Play All button */}
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
      </div>
    </div>
  )
}

