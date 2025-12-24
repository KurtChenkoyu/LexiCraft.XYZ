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

type Stage = 'grid' | 'mining' | 'verifying' | 'result' | 'smelting' | 'day-complete' | 'day5-intro' | 'day5-demo-review' | 'reset-explanation'

interface DemoFlowProps {
  campaign: CampaignConfig
}

const MAX_DEMO_WORDS = 7

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
  const [wordStatus, setWordStatus] = useState<Map<string, 'raw' | 'hollow' | 'solid'>>(new Map()) // Status-based progress tracking
  const [showPaywallModal, setShowPaywallModal] = useState(false)
  
  // 7-Day Progression State
  const [demoDay, setDemoDay] = useState<number>(1) // 1-7
  const [wordsCollectedToday, setWordsCollectedToday] = useState<number>(0) // Track if user collected word today
  const [wordsByDay, setWordsByDay] = useState<Map<number, Block[]>>(new Map()) // Track which day each word was forged
  const [resetWords, setResetWords] = useState<Set<string>>(new Set()) // Track words that were reset (need immediate review)
  
  // Day 5 Special Demo State
  const [isSpecialDayDemo, setIsSpecialDayDemo] = useState<boolean>(false) // Day 5 special demo mode
  const [demoWordToReset, setDemoWordToReset] = useState<Block | null>(null) // Word being used for reset demonstration
  const [hasSeenDay5Intro, setHasSeenDay5Intro] = useState<boolean>(false) // Track if user has seen Day 5 intro
  
  const [smeltingProgress, setSmeltingProgress] = useState<{
    currentInterval: number // 0 = 1 day, 1 = 3 days, 2 = 1 week
    currentWordIndex: number // Index within current interval's word list
    wordsByInterval: {
      interval0: Block[] // All words that need 1-day review
      interval1: Block[] // All words that need 3-day review
      interval2: Block[] // All words that need 1-week review
    }
    completedWords: Set<string> // Words that completed all required intervals
    showMcq: boolean // Whether to show MCQ for current review
    smeltingMcqOptions: Block[] // MCQ options for smelting review
    smeltingAnswer: string | null // Selected answer for smelting MCQ
  } | null>(null)
  const sparkAnimationRef = useRef<NodeJS.Timeout | null>(null)
  
  // Helper functions for status-based system
  const getWordStatus = (senseId: string): 'raw' | 'hollow' | 'solid' => {
    return wordStatus.get(senseId) || 'raw'
  }
  
  const isWordForged = (senseId: string): boolean => {
    const status = getWordStatus(senseId)
    return status === 'hollow' || status === 'solid'
  }
  
  const isWordSmelted = (senseId: string): boolean => {
    return getWordStatus(senseId) === 'solid'
  }
  
  // Derived: Count of forged words (hollow or solid)
  const forgedWordsCount = Array.from(wordStatus.values()).filter(
    s => s === 'hollow' || s === 'solid'
  ).length

  // Load demo progress from localStorage on mount
  // Only load words that exist in DEMO_WORDS to prevent stale data
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const validSenseIds = new Set(DEMO_WORDS.map(w => w.sense_id))
      
      // Try to load new format (status map)
      const stored = localStorage.getItem('demo_word_status')
      if (stored) {
        try {
          const statusData = JSON.parse(stored)
          const statusMap = new Map<string, 'raw' | 'hollow' | 'solid'>()
          Object.entries(statusData).forEach(([senseId, status]) => {
            if (validSenseIds.has(senseId) && ['raw', 'hollow', 'solid'].includes(status as string)) {
              statusMap.set(senseId, status as 'raw' | 'hollow' | 'solid')
            }
          })
          setWordStatus(statusMap)
        } catch (e) {
          console.warn('Failed to load demo word status from localStorage:', e)
          localStorage.removeItem('demo_word_status')
        }
      }
      
      // MIGRATION: Try to migrate old format (forged words set)
      const oldForged = localStorage.getItem('demo_forged_words')
      if (oldForged && !stored) {
        try {
          const oldWords = JSON.parse(oldForged)
          const migratedMap = new Map<string, 'raw' | 'hollow' | 'solid'>()
          oldWords.forEach((senseId: string) => {
            if (validSenseIds.has(senseId)) {
              migratedMap.set(senseId, 'hollow') // Assume hollow for old data
            }
          })
          if (migratedMap.size > 0) {
            setWordStatus(migratedMap)
            // Save in new format
            const statusObj = Object.fromEntries(migratedMap)
            localStorage.setItem('demo_word_status', JSON.stringify(statusObj))
            // Clean up old format
            localStorage.removeItem('demo_forged_words')
            console.log(`[DemoFlow] Migrated ${migratedMap.size} words from old format to status-based system`)
          }
        } catch (e) {
          console.warn('Failed to migrate old demo data:', e)
        }
      }
      
      const storedDay = localStorage.getItem('demo_day')
      const storedWordsByDay = localStorage.getItem('demo_words_by_day')
      const storedWordsCollectedToday = localStorage.getItem('demo_words_collected_today')
      
      // Load day progression
      if (storedDay) {
        try {
          const day = parseInt(storedDay, 10)
          if (day >= 1 && day <= 7) {
            setDemoDay(day)
          }
        } catch (e) {
          console.warn('Failed to load demo day from localStorage:', e)
        }
      }
      
      // Load words by day
      if (storedWordsByDay) {
        try {
          const wordsByDayData = JSON.parse(storedWordsByDay)
          const wordsByDayMap = new Map<number, Block[]>()
          const validSenseIds = new Set(DEMO_WORDS.map(w => w.sense_id))
          
          Object.entries(wordsByDayData).forEach(([dayStr, wordIds]: [string, any]) => {
            const day = parseInt(dayStr, 10)
            if (day >= 1 && day <= 7 && Array.isArray(wordIds)) {
              const validWords = wordIds
                .map((id: string) => DEMO_WORDS.find(w => w.sense_id === id))
                .filter((w): w is Block => w !== undefined && validSenseIds.has(w.sense_id))
              if (validWords.length > 0) {
                wordsByDayMap.set(day, validWords)
              }
            }
          })
          
          setWordsByDay(wordsByDayMap)
        } catch (e) {
          console.warn('Failed to load words by day from localStorage:', e)
        }
      }
      
      // Load words collected today
      if (storedWordsCollectedToday) {
        try {
          const count = parseInt(storedWordsCollectedToday, 10)
          if (count >= 0 && count <= 1) {
            setWordsCollectedToday(count)
          }
        } catch (e) {
          console.warn('Failed to load words collected today from localStorage:', e)
        }
      }
      
      // Load Day 5 intro status
      const storedDay5Intro = localStorage.getItem('demo_day5_intro_seen')
      if (storedDay5Intro === 'true') {
        setHasSeenDay5Intro(true)
      }
    }
  }, [])
  
  // Save demo progress to localStorage whenever state changes
  // Only save valid words (those in DEMO_WORDS)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const validSenseIds = new Set(DEMO_WORDS.map(w => w.sense_id))
      const statusObj: Record<string, 'raw' | 'hollow' | 'solid'> = {}
      
      wordStatus.forEach((status, senseId) => {
        if (validSenseIds.has(senseId)) {
          statusObj[senseId] = status
        }
      })
      
      if (Object.keys(statusObj).length > 0) {
        localStorage.setItem('demo_word_status', JSON.stringify(statusObj))
      } else {
        localStorage.removeItem('demo_word_status')
      }
    }
  }, [wordStatus])
  
  // Save day progression to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('demo_day', demoDay.toString())
    }
  }, [demoDay])
  
  // Save words by day to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const wordsByDayObj: Record<string, string[]> = {}
      wordsByDay.forEach((words, day) => {
        wordsByDayObj[day.toString()] = words.map(w => w.sense_id)
      })
      localStorage.setItem('demo_words_by_day', JSON.stringify(wordsByDayObj))
    }
  }, [wordsByDay])
  
  // Save words collected today to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('demo_words_collected_today', wordsCollectedToday.toString())
    }
  }, [wordsCollectedToday])
  
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
    // 7-Day Progression: Only allow 1 word per day
    if (wordsCollectedToday >= 1) {
      // User already collected word today - show message or do nothing
      return
    }
    
    // Prevent selecting words that have already been forged
    if (isWordForged(word.sense_id)) {
      // Word already forged - do nothing
      return
    }
    
    // Check if user has reached demo limit (7 words total)
    if (forgedWordsCount >= MAX_DEMO_WORDS && getWordStatus(word.sense_id) === 'raw') {
      setShowPaywallModal(true)
      trackCampaignEvent(campaign, 'ctaClick', {
        action: 'paywall_modal_shown',
        word: word.word,
        forged_count: forgedWordsCount,
      })
      return
    }
    
    setSelectedWord(word)
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'word_selected',
      word: word.word,
      emoji: word.emoji,
      forged_count: forgedWordsCount,
      day: demoDay,
    })
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'demo_stage_mining',
    })
    setStage('mining')
  }

  const handleForge = useCallback(() => {
    if (!selectedWord) return
    
    // Set word status to 'hollow' (forged, in SRS queue)
    setWordStatus(prev => {
      const next = new Map(prev)
      next.set(selectedWord.sense_id, 'hollow')
      return next
    })
    
    // Track which day word was collected
    setWordsByDay(prev => {
      const next = new Map(prev)
      const dayWords = next.get(demoDay) || []
      next.set(demoDay, [...dayWords, selectedWord])
      return next
    })
    
    // Mark word as collected today
    setWordsCollectedToday(1)
    
    // Track word forged event
    const newCount = forgedWordsCount + 1
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'word_forged',
      word: selectedWord.word,
      forged_count: newCount,
      day: demoDay,
    })
    
    // Check if demo is complete
    if (newCount >= MAX_DEMO_WORDS) {
      trackCampaignEvent(campaign, 'ctaClick', {
        action: 'demo_completed',
        forged_count: newCount,
      })
    }
    
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
  }, [selectedWord, forgedWordsCount, demoDay, campaign])

  const handleMcqAnswer = async (option: Block) => {
    if (!selectedWord) {
      console.warn('[DemoFlow] handleMcqAnswer: No selectedWord')
      return
    }
    
    if (isPlaying) {
      console.warn('[DemoFlow] handleMcqAnswer: Already playing, ignoring click')
      return
    }
    
    console.log('[DemoFlow] handleMcqAnswer:', { 
      option: option.word, 
      selectedWord: selectedWord.word,
      isCorrect: option.sense_id === selectedWord.sense_id 
    })
    
    setSelectedAnswer(option.sense_id)
    setIsPlaying(true)
    
    const isCorrect = option.sense_id === selectedWord.sense_id
    
    try {
      if (isCorrect) {
        await audioService.playSfx('correct')
        trackCampaignEvent(campaign, 'ctaClick', {
          action: 'mcq_answered',
          correct: true,
          word: selectedWord.word,
        })
        
        console.log('[DemoFlow] Correct answer, transitioning to result in 1s...')
        
        // Check if there are words due for review after 1 second
        setTimeout(() => {
          console.log('[DemoFlow] Checking for words due for review')
          setIsPlaying(false) // Reset playing state before transition
          trackCampaignEvent(campaign, 'ctaClick', {
            action: 'demo_stage_result',
          })
          // Only track demo_completed if we've reached the limit
          // (forgedWordsCount will be updated after handleForge, so check +1)
          if (forgedWordsCount + 1 >= MAX_DEMO_WORDS) {
            trackCampaignEvent(campaign, 'ctaClick', {
              action: 'demo_completed',
              word: selectedWord.word,
              forged_count: forgedWordsCount + 1,
            })
          }
          
          // Check if there are words due for review today
          const wordsDueForReview = getWordsDueForReview(demoDay, wordsByDay, resetWords)
          
          if (wordsDueForReview.length > 0) {
            // Start review session for due words
            console.log(`[DemoFlow] Starting review session for ${wordsDueForReview.length} words`)
            startReviewSession(wordsDueForReview)
            setStage('smelting')
          } else {
            // No words due - go to day complete
            console.log('[DemoFlow] No words due for review, going to day-complete')
            setStage('day-complete')
          }
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
    } catch (error) {
      console.error('[DemoFlow] Error in handleMcqAnswer:', error)
      // Reset state on error to prevent hanging
      setIsPlaying(false)
      if (isCorrect) {
        // Still transition to result even if audio fails
        setTimeout(() => {
          setStage('result')
        }, 500)
      }
    }
  }
  
  // Helper function to get words due for review on current day
  const getWordsDueForReview = useCallback((currentDay: number, wordsByDay: Map<number, Block[]>, resetWords: Set<string>): Block[] => {
    const dueWords: Block[] = []
    
    // PRIORITY 1: Words that were reset need immediate review (available the day after reset)
    // Check all words in wordsByDay that are in resetWords
    wordsByDay.forEach((words, day) => {
      words.forEach(word => {
        if (resetWords.has(word.sense_id) && getWordStatus(word.sense_id) !== 'solid') {
          // Reset words are due for review immediately (next day after reset)
          // Don't add duplicates
          if (!dueWords.find(dw => dw.sense_id === word.sense_id)) {
            dueWords.push(word)
          }
        }
      })
    })
    
    // PRIORITY 2: Words need review 2 days after collection (1-day interval)
    // So Day 1 words are due on Day 3, Day 2 words due on Day 4, etc.
    const reviewDay = currentDay - 2
    
    if (reviewDay >= 1) {
      const wordsToReview = wordsByDay.get(reviewDay) || []
      // Filter out words that are already smelted (status === 'solid') or already in dueWords
      wordsToReview.forEach(w => {
        if (getWordStatus(w.sense_id) !== 'solid' && !dueWords.find(dw => dw.sense_id === w.sense_id)) {
          dueWords.push(w)
        }
      })
    }
    
    // PRIORITY 3: Also check for 3-day interval (Day N words due on Day N+3)
    // But only if we're past Day 3
    if (currentDay >= 4) {
      const threeDayReviewDay = currentDay - 3
      if (threeDayReviewDay >= 1) {
        const wordsToReview = wordsByDay.get(threeDayReviewDay) || []
        // Only add words that haven't been smelted yet and aren't already in dueWords
        wordsToReview.forEach(w => {
          if (getWordStatus(w.sense_id) !== 'solid' && !dueWords.find(dw => dw.sense_id === w.sense_id)) {
            dueWords.push(w)
          }
        })
      }
    }
    
    return dueWords
  }, [wordStatus])
  
  // Helper to start review session
  const startReviewSession = useCallback((wordsToReview: Block[]) => {
    if (wordsToReview.length === 0) return
    
    const firstWord = wordsToReview[0]
    const distractors = DEMO_WORDS
      .filter(w => w.sense_id !== firstWord.sense_id)
      .sort(() => Math.random() - 0.5)
      .slice(0, 3)
    const options = [firstWord, ...distractors].sort(() => Math.random() - 0.5)
    
    setSmeltingProgress({
      currentInterval: 0, // Start with first interval
      currentWordIndex: 0,
      wordsByInterval: {
        interval0: wordsToReview, // All due words need review
        interval1: [],
        interval2: [],
      },
      completedWords: new Set<string>(),
      showMcq: false,
      smeltingMcqOptions: options,
      smeltingAnswer: null,
    })
  }, [])
  
  const handleDayComplete = () => {
    if (demoDay < 7) {
      // Move to next day
      setDemoDay(prev => prev + 1)
      setWordsCollectedToday(0) // Reset words collected for new day
      setSelectedWord(null)
      setSelectedAnswer(null)
      setStage('grid')
      trackCampaignEvent(campaign, 'ctaClick', {
        action: 'day_progression',
        day: demoDay + 1,
        forged_count: forgedWordsCount,
      })
    } else {
      // Day 7 complete - show smelt all option
      setSelectedWord(null)
      setSelectedAnswer(null)
      setStage('grid')
    }
  }
  
  const handleTryAnother = () => {
    setSelectedWord(null)
    setStage('grid')
    setSelectedAnswer(null)
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'try_another_clicked',
      forged_count: forgedWordsCount,
    })
  }
  
  const handleClearProgress = () => {
    // Clear all localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('demo_forged_words')
      localStorage.removeItem('demo_day')
      localStorage.removeItem('demo_words_by_day')
      localStorage.removeItem('demo_words_collected_today')
      localStorage.removeItem('demo_day5_intro_seen')
      localStorage.removeItem('demo_word_status')
    }
    
    // Reset all state
    setDemoDay(1)
    setWordsCollectedToday(0)
    setWordsByDay(new Map())
    setWordStatus(new Map())
    setResetWords(new Set())
    setSelectedWord(null)
    setSelectedAnswer(null)
    setStage('grid')
    setSmeltingProgress(null)
    setIsSpecialDayDemo(false)
    setDemoWordToReset(null)
    setHasSeenDay5Intro(false)
    
    trackCampaignEvent(campaign, 'ctaClick', {
      action: 'clear_progress_clicked',
    })
  }
  
  // Check if Day 5 intro should be shown when entering grid
  useEffect(() => {
    if (stage === 'grid' && demoDay === 5 && !hasSeenDay5Intro && wordsByDay.size > 0) {
      const demoWord = wordsByDay.get(1)?.[0] || wordsByDay.get(2)?.[0]
      if (demoWord) {
        setStage('day5-intro')
      }
    }
  }, [stage, demoDay, hasSeenDay5Intro, wordsByDay])

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
    <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-4 sm:p-6 max-w-md w-full shadow-2xl border border-slate-700 flex flex-col h-[85vh] max-h-[650px] min-h-[500px] overflow-hidden">
      {/* Unified Top Bar - Fixed */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-700/50 flex-shrink-0">
        {/* Clear Progress Button - Left */}
        {(forgedWordsCount > 0 || demoDay > 1) ? (
          <button
            onClick={handleClearProgress}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-red-700/30 hover:bg-red-700/50 border border-red-600/50 rounded-lg text-xs text-red-300 hover:text-red-200 transition-all"
            title={showChinese ? '重置所有進度' : 'Reset All Progress'}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span className="hidden sm:inline">{showChinese ? '重置' : 'Reset'}</span>
          </button>
        ) : (
          <div className="w-1" /> // Spacer to keep center aligned
        )}
        
        {/* Day Badge - Center */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1.5 rounded-lg text-sm font-bold">
          {showChinese ? `第 ${demoDay} 天/7` : `Day ${demoDay}/7`}
        </div>
        
        {/* Language Toggle - Right */}
        <button
          onClick={() => setShowChinese(!showChinese)}
          className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-700/30 hover:bg-slate-700/50 border border-slate-600/50 rounded-lg text-xs text-slate-300 hover:text-white transition-all"
          title={showChinese ? 'Switch to English' : '切換到中文'}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
          </svg>
          <span className="hidden sm:inline">{showChinese ? 'EN' : '中文'}</span>
        </button>
      </div>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden -mx-2 sm:-mx-6 px-2 sm:px-6">
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

            {/* Title Section */}
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-white mb-2">
                {showChinese ? '選擇一個單字開始' : 'Pick a word to start'}
              </h3>
              <div className="flex items-center justify-center gap-3 text-sm">
                <p className="text-slate-400">
                  {showChinese ? '點擊任意字塊開始學習' : 'Click any word to begin'}
                </p>
                <span className="text-slate-600">•</span>
                <p className="text-slate-400">
                  {showChinese 
                    ? `${forgedWordsCount}/7 個單字`
                    : `${forgedWordsCount}/7 words`
                  }
                </p>
              </div>
            </div>
            
            {/* Smelt All Collected Button - Only show after Day 7 is complete */}
            {demoDay === 7 && forgedWordsCount >= 7 && (
              <motion.button
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => {
                  // Get all forged words (hollow or solid status)
                  const allForgedWords = DEMO_WORDS.filter(w => isWordForged(w.sense_id))
                  
                  trackCampaignEvent(campaign, 'ctaClick', {
                    action: 'smelt_all_clicked',
                    forged_count: forgedWordsCount,
                  })
                  
                  // Separate words by interval based on collection day
                  // Interval 0 (1 day): ALL 7 words need 1-day review
                  // Interval 1 (3 days): Days 1-4 words need 3-day review (4 words)
                  // Interval 2 (1 week): Days 1-3 words need 1-week review (3 words)
                  const wordsByInterval = {
                    interval0: allForgedWords, // All words get first review
                    interval1: [] as Block[], // Words from Day 1-4
                    interval2: [] as Block[], // Words from Day 1-3
                  }
                  
                  // Populate intervals based on collection day
                  wordsByDay.forEach((words, day) => {
                    if (day <= 4) {
                      // Days 1-4: Need 3-day review (interval 1)
                      wordsByInterval.interval1.push(...words)
                    }
                    if (day <= 3) {
                      // Days 1-3: Need 1-week review (interval 2)
                      wordsByInterval.interval2.push(...words)
                    }
                  })
                  
                  // Start with first word of interval 0
                  const firstWord = wordsByInterval.interval0[0]
                  const distractors = DEMO_WORDS
                    .filter(w => w.sense_id !== firstWord.sense_id)
                    .sort(() => Math.random() - 0.5)
                    .slice(0, 3) // 3 distractors = 4 total options
                  const options = [firstWord, ...distractors].sort(() => Math.random() - 0.5)
                  
                  setSmeltingProgress({
                    currentInterval: 0, // Start with 1 day review (interval 0)
                    currentWordIndex: 0, // Start with first word in interval 0
                    wordsByInterval: wordsByInterval,
                    completedWords: new Set<string>(),
                    showMcq: false, // Start by showing word info
                    smeltingMcqOptions: options,
                    smeltingAnswer: null,
                  })
                  setStage('smelting')
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full mb-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold rounded-lg shadow-lg transition-all flex items-center justify-center gap-2"
              >
                <span className="text-lg">🔥</span>
                <span>{showChinese ? '熔煉所有收集的單字' : 'Smelt All Collected'}</span>
              </motion.button>
            )}
            
            <div className="grid grid-cols-3 gap-3">
              {DEMO_WORDS.map((word) => {
                const status = getWordStatus(word.sense_id)
                const isForged = status === 'hollow' || status === 'solid'
                const isSmelted = status === 'solid'
                // Disable if: already collected today, already forged, or reached limit on day 7
                const isDisabled = wordsCollectedToday >= 1 || isForged || (demoDay === 7 && forgedWordsCount >= 7)
                return (
                  <motion.button
                    key={word.sense_id}
                    whileHover={!isDisabled ? { scale: 1.05 } : {}}
                    whileTap={!isDisabled ? { scale: 0.95 } : {}}
                    onClick={() => !isDisabled && handleWordSelect(word)}
                    disabled={isDisabled}
                    className={`relative rounded-lg p-4 flex flex-col items-center justify-center border transition-all ${
                      isDisabled && !isForged
                        ? 'bg-slate-800/30 border-slate-700 opacity-50 cursor-not-allowed'
                        : isSmelted
                        ? 'bg-amber-500/20 border-amber-400/50 hover:bg-amber-500/30'
                        : isForged
                        ? 'bg-emerald-500/20 border-emerald-400/50 hover:bg-emerald-500/30'
                        : 'bg-slate-700/50 hover:bg-slate-700 border-slate-600'
                    }`}
                  >
                    {isSmelted && (
                      <div className="absolute top-1 right-1 w-5 h-5 bg-amber-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">🔥</span>
                      </div>
                    )}
                    {isForged && !isSmelted && (
                      <div className="absolute top-1 right-1 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">✓</span>
                      </div>
                    )}
                    <span className="text-3xl mb-2">{word.emoji}</span>
                    <span className="text-sm font-bold text-white">{capitalizeWord(word.word)}</span>
                    <span className={`text-xs mt-1 ${
                      status === 'solid'
                        ? 'text-amber-400' 
                        : status === 'hollow'
                        ? 'text-emerald-400' 
                        : 'text-slate-400'
                    }`}>
                      {status === 'solid' ? '🔥 FORGED' : status === 'hollow' ? '✨ FORGING' : '🪨 RAW'}
                    </span>
                  </motion.button>
                )
              })}
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

        {/* STAGE 3: Result (Success + CTA) - Kept for backward compatibility but not used in 7-day flow */}
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
            
            <div className="text-6xl mb-4">{selectedWord.emoji}</div>
            
            {/* Progress Indicator */}
            <div className="mb-4">
              <p className="text-sm text-slate-400 mb-2">
                {showChinese 
                  ? `鍛造中 ${forgedWordsCount}/7 個單字`
                  : `Forging ${forgedWordsCount}/7 words`
                }
              </p>
              {/* Progress Bar */}
              <div className="w-full max-w-xs mx-auto h-2 bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(forgedWordsCount / MAX_DEMO_WORDS) * 100}%` }}
                  transition={{ duration: 0.5 }}
                  className="h-full bg-gradient-to-r from-amber-400 to-orange-500"
                />
              </div>
            </div>
            
            <p className="text-lg text-slate-300 mb-6 px-4">
              {forgedWordsCount < MAX_DEMO_WORDS
                ? (showChinese 
                  ? `你已經學會了「${selectedWord.translation}」！再試 ${MAX_DEMO_WORDS - forgedWordsCount} 個單字體驗完整功能。`
                  : `You've learned '${capitalizeWord(selectedWord.word)}'! Try ${MAX_DEMO_WORDS - forgedWordsCount} more words to see the full experience.`)
                : (showChinese
                  ? `你已經體驗完整示範！準備解鎖全部 200+ 單字了嗎？`
                  : `You've experienced the full demo! Ready to unlock all 200+ words?`)
              }
            </p>
            
            <div className="w-full space-y-3">
              {/* Try Another Word Button (only if < 7 words) */}
              {forgedWordsCount < MAX_DEMO_WORDS && (
                <motion.button
                  onClick={handleTryAnother}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-3 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-xl border border-slate-600 transition-all"
                >
                  {showChinese ? '🔄 再試一個單字' : '🔄 Try Another Word'}
                </motion.button>
              )}
              
              {/* Buy Now Button */}
              <Link
                href={`/signup?plan=lifetime&redirect=checkout&utm_source=demo&utm_medium=micro_journey&utm_campaign=${selectedWord.word.toLowerCase()}_demo`}
                onClick={handleSaveProgress}
                className="block w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg hover:from-amber-500 hover:to-orange-600 transition-all"
              >
                {showChinese 
                  ? `💳 立即購買 - 永久使用 NT$299`
                  : `💳 Buy Now - Lifetime Access NT$299`
                }
              </Link>
              <p className="text-xs text-slate-400 mt-2">
                {showChinese ? '一次付費，永久使用' : 'One-Time Payment. Own it forever.'}
              </p>
            </div>
          </motion.div>
        )}

        {/* STAGE: Day 5 Intro */}
        {stage === 'day5-intro' && (
          <motion.div
            key="day5-intro"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            className="w-full flex flex-col items-center justify-center text-center"
          >
            <div className="text-6xl mb-4">🎓</div>
            <h3 className="text-3xl font-black text-white mb-4">
              {showChinese ? '學習時刻：錯誤答案會重置進度' : 'Learning Moment: Wrong Answers Reset Progress'}
            </h3>
            <p className="text-lg text-slate-300 mb-4 px-4">
              {showChinese 
                ? '讓我們看看當你答錯複習題時會發生什麼。'
                : "Let's see what happens when you get a review wrong."
              }
            </p>
            <p className="text-base text-slate-400 mb-6 px-4">
              {showChinese 
                ? '在這個示範中，我們會故意選擇錯誤答案，看看單字如何重置回第 1 天。'
                : "For this demonstration, we'll intentionally make a wrong answer to see how the word resets to Day 1."
              }
            </p>
            <motion.button
              onClick={() => {
                // Find a word from Day 1 or 2 to use for demo
                const demoWord = wordsByDay.get(1)?.[0] || wordsByDay.get(2)?.[0]
                if (demoWord) {
                  setDemoWordToReset(demoWord)
                  setIsSpecialDayDemo(true)
                  setHasSeenDay5Intro(true)
                  if (typeof window !== 'undefined') {
                    localStorage.setItem('demo_day5_intro_seen', 'true')
                  }
                  // Start review session with this word
                  startReviewSession([demoWord])
                  setStage('day5-demo-review')
                  trackCampaignEvent(campaign, 'ctaClick', {
                    action: 'day5_demo_started',
                    word: demoWord.word,
                  })
                } else {
                  // No words available for demo, skip to grid
                  setHasSeenDay5Intro(true)
                  if (typeof window !== 'undefined') {
                    localStorage.setItem('demo_day5_intro_seen', 'true')
                  }
                  setStage('grid')
                }
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg hover:from-amber-500 hover:to-orange-600 transition-all"
            >
              {showChinese ? '開始示範' : 'Show Me'}
            </motion.button>
          </motion.div>
        )}

        {/* STAGE: Reset Explanation */}
        {stage === 'reset-explanation' && demoWordToReset && (
          <motion.div
            key="reset-explanation"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            className="w-full flex flex-col items-center justify-center text-center"
          >
            <div className="text-6xl mb-4">🔄</div>
            <h3 className="text-3xl font-black text-white mb-4">
              {showChinese ? '單字已重置至第 1 天！' : 'Word Reset to Day 1!'}
            </h3>
            <p className="text-lg text-slate-300 mb-4 px-4">
              {showChinese 
                ? `你選擇了錯誤答案（這是示範的預期行為）。`
                : `You selected the wrong answer (as intended for this demo).`
              }
            </p>
            <div className="bg-slate-700/50 rounded-xl p-4 mb-6 w-full">
              <p className="text-xl font-bold text-amber-400 mb-2">
                {capitalizeWord(demoWordToReset.word)}
              </p>
              <p className="text-sm text-slate-300">
                {showChinese 
                  ? '已重置至第 1 天，需要從頭開始複習。'
                  : 'has been reset to Day 1 and needs to be reviewed from the beginning.'
                }
              </p>
            </div>
            <p className="text-base text-slate-400 mb-6 px-4">
              {showChinese 
                ? '在間隔複習系統中，錯誤答案會重置進度。這就是為什麼準確性很重要！'
                : 'In Spaced Repetition, wrong answers reset progress. This is why accuracy matters!'
              }
            </p>
            <motion.button
              onClick={() => {
                setIsSpecialDayDemo(false)
                setDemoWordToReset(null)
                setStage('grid') // Continue to collect Day 5 word
                trackCampaignEvent(campaign, 'ctaClick', {
                  action: 'day5_demo_completed',
                  word: demoWordToReset.word,
                })
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg hover:from-amber-500 hover:to-orange-600 transition-all"
            >
              {showChinese ? '我明白了 - 繼續' : 'I Understand - Continue'}
            </motion.button>
          </motion.div>
        )}

        {/* STAGE: Day Complete */}
        {stage === 'day-complete' && selectedWord && (() => {
          const wordsDueForReview = getWordsDueForReview(demoDay, wordsByDay, resetWords)
          
          return (
          <motion.div
            key="day-complete"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            className="w-full flex flex-col items-center justify-center text-center"
          >
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-3xl font-black text-white mb-2">
              {showChinese ? `第 ${demoDay} 天完成！` : `Day ${demoDay} Complete!`}
            </h3>
            <p className="text-lg text-slate-300 mb-4">
              {showChinese 
                ? `你已經收集了 ${forgedWordsCount} 個單字`
                : `You've collected ${forgedWordsCount} words`
              }
            </p>
            
            {demoDay < 7 ? (
              <>
                {wordsDueForReview.length > 0 ? (
                  <>
                    <p className="text-sm text-amber-400 mb-4 px-4 font-bold">
                      {showChinese 
                        ? `有 ${wordsDueForReview.length} 個單字需要複習`
                        : `${wordsDueForReview.length} words need review`
                      }
                    </p>
                    <motion.button
                      onClick={() => {
                        startReviewSession(wordsDueForReview)
                        setStage('smelting')
                      }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold rounded-xl text-lg hover:from-orange-600 hover:to-red-600 transition-all mb-3"
                    >
                      {showChinese ? '🔥 開始複習' : '🔥 Start Review'}
                    </motion.button>
                    <motion.button
                      onClick={handleDayComplete}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full py-3 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-xl border border-slate-600 transition-all"
                    >
                      {showChinese ? `跳過複習，開始第 ${demoDay + 1} 天` : `Skip Review, Start Day ${demoDay + 1}`}
                    </motion.button>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-slate-400 mb-6 px-4">
                      {showChinese 
                        ? '完成 7 天後，你可以熔煉所有單字'
                        : 'After 7 days, you can smelt all words through SRS'
                      }
                    </p>
                    <motion.button
                      onClick={handleDayComplete}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg hover:from-amber-500 hover:to-orange-600 transition-all"
                    >
                      {showChinese ? `開始第 ${demoDay + 1} 天` : `Start Day ${demoDay + 1}`}
                    </motion.button>
                  </>
                )}
              </>
            ) : (
              <>
                <p className="text-sm text-slate-400 mb-6 px-4">
                  {showChinese 
                    ? '現在你可以熔煉所有收集的單字了！'
                    : 'Now you can smelt all collected words!'
                  }
                </p>
                <motion.button
                  onClick={handleDayComplete}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg hover:from-amber-500 hover:to-orange-600 transition-all"
                >
                  {showChinese ? '返回' : 'Back to Grid'}
                </motion.button>
              </>
            )}
          </motion.div>
          )
        })()}

        {/* STAGE: Smelting (SRS Process) - Also used for Day 5 Demo Review */}
        {(stage === 'smelting' || stage === 'day5-demo-review') && smeltingProgress && (() => {
          // Get current interval's words
          const currentWords = smeltingProgress.wordsByInterval[`interval${smeltingProgress.currentInterval}` as keyof typeof smeltingProgress.wordsByInterval]
          
          // Safety check: ensure we have words and valid index
          if (!currentWords || currentWords.length === 0 || smeltingProgress.currentWordIndex >= currentWords.length) {
            // Invalid state - reset to grid
            setStage('grid')
            setSmeltingProgress(null)
            return null
          }
          
          const currentWord = currentWords[smeltingProgress.currentWordIndex]
          const intervalLabels = [
            { interval: 0, days: 1, label: showChinese ? '1 天' : '1 day', emoji: '📅' },
            { interval: 1, days: 3, label: showChinese ? '3 天' : '3 days', emoji: '📆' },
            { interval: 2, days: 7, label: showChinese ? '1 週' : '1 week', emoji: '🗓️' },
          ]
          const currentIntervalLabel = intervalLabels[smeltingProgress.currentInterval]
          const isDay5Demo = stage === 'day5-demo-review' || isSpecialDayDemo
          
          return (
          <motion.div
            key="smelting"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            className="w-full flex flex-col items-center justify-center text-center"
          >
            <div className="text-6xl mb-4">🔥</div>
            <h3 className="text-3xl font-black text-white mb-4">
              {showChinese ? '熔煉中...' : 'Smelting...'}
            </h3>
            
            {/* SRS Explanation - Always Visible, Cannot Dismiss */}
            <div className="bg-gradient-to-br from-slate-700/60 to-slate-800/60 rounded-xl p-4 mb-6 w-full border border-amber-500/40 shadow-lg">
              {isDay5Demo ? (
                <div className="mb-3 pb-3 border-b border-amber-500/20">
                  <p className="text-xs text-amber-400 mb-1 font-bold">
                    {showChinese 
                      ? '🎓 示範模式：正確答案已鎖定'
                      : '🎓 Demo Mode: Correct answer locked'
                    }
                  </p>
                  <p className="text-xs text-slate-400">
                    {showChinese 
                      ? '請選擇錯誤答案以查看重置效果'
                      : "Select wrong answer to see reset effect"
                    }
                  </p>
                </div>
              ) : null}
              
              {/* SRS Header */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-white">
                    {showChinese ? '間隔複習系統' : 'Spaced Repetition System'}
                  </h4>
                  <span className="text-[10px] text-cyan-400 font-semibold bg-cyan-500/10 px-2 py-0.5 rounded">
                    FSRS
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {showChinese 
                    ? '根據遺忘曲線理論，在最佳時機複習可以強化記憶。系統採用 FSRS 演算法，根據你的學習表現動態調整複習間隔（1、3、7、14、30、60、120+ 天），在記憶即將衰退時提醒你複習，讓記憶從短期轉為長期記憶。此示範展示前 3 個階段。'
                    : 'Based on forgetting curve theory, reviewing at optimal intervals strengthens memory. Uses FSRS algorithm that adapts review intervals (1, 3, 7, 14, 30, 60, 120+ days) based on your performance, reminding you just before you forget to transform short-term into long-term memory. This demo shows the first 3 stages.'
                  }
                </p>
              </div>
              
              {/* Review Intervals - Horizontal Scroll for Mobile */}
              <div className="overflow-x-auto -mx-4 px-4 pb-2 mb-3">
                <div className="flex gap-2 w-full">
                  {intervalLabels.map((item, idx) => {
                    const isActive = smeltingProgress.currentInterval === item.interval
                    const isCompleted = smeltingProgress.currentInterval > item.interval
                    return (
                      <div
                        key={idx}
                        className={`flex flex-col items-center gap-1.5 p-2.5 rounded-lg transition-all flex-1 ${
                          isActive
                            ? 'bg-amber-500/20 border-2 border-amber-400/50'
                            : isCompleted
                            ? 'bg-emerald-500/10 border border-emerald-500/30'
                            : 'bg-slate-800/30 border border-slate-600/30'
                        }`}
                      >
                        <span className={`text-xl ${isActive ? 'scale-110' : ''} transition-transform`}>
                          {item.emoji}
                        </span>
                        <div className="text-center">
                          <div className={`text-xs font-semibold ${
                            isActive
                              ? 'text-amber-400'
                              : isCompleted
                              ? 'text-emerald-400'
                              : 'text-slate-400'
                          }`}>
                            {item.label}
                          </div>
                          {isActive && (
                            <div className="text-[10px] text-amber-300/80 mt-0.5">
                              {showChinese ? '進行中' : 'Active'}
                            </div>
                          )}
                          {isCompleted && (
                            <div className="text-[10px] text-emerald-300/80 mt-0.5">
                              {showChinese ? '完成' : 'Done'}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                  {/* Extended intervals indicator */}
                  <div className="flex flex-col items-center justify-center gap-1.5 p-2.5 rounded-lg bg-slate-800/30 border border-slate-600/30 flex-1">
                    <span className="text-xl text-slate-500">📆</span>
                    <div className="text-center">
                      <div className="text-xs font-semibold text-slate-400">
                        {showChinese ? '14 天...' : '14 days...'}
                      </div>
                      <div className="text-[10px] text-slate-500/80 mt-0.5">
                        {showChinese ? '後續' : 'More'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Goal */}
              <div className="pt-2 border-t border-slate-600/30">
                <p className="text-xs text-slate-400 text-center">
                  {showChinese 
                    ? '完成 3 次複習 → 長期記憶 🔥 (完整系統會持續調整至 120+ 天)'
                    : '3 reviews → Long-term memory 🔥 (Full system adapts up to 120+ days)'
                  }
                </p>
              </div>
            </div>
            
            {/* Batch Progress Display */}
            <div className="mb-4 w-full">
              <p className="text-sm text-slate-300 mb-2">
                {showChinese 
                  ? `處理 ${currentIntervalLabel.label}: ${smeltingProgress.currentWordIndex + 1} / ${currentWords.length} 個單字`
                  : `Processing ${currentIntervalLabel.label}: ${smeltingProgress.currentWordIndex + 1} / ${currentWords.length} words`
                }
              </p>
              <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ 
                    width: `${((smeltingProgress.currentWordIndex + 1) / currentWords.length) * 100}%` 
                  }}
                  transition={{ duration: 0.3 }}
                  className="h-full bg-gradient-to-r from-orange-500 to-red-500"
                />
              </div>
            </div>
            
            {/* Current Word Being Smelted */}
            {currentWord && (
              <>
                {!smeltingProgress.showMcq ? (
                  // Word Info View (before MCQ)
                  <>
                    <div className="mb-6">
                      <div className="flex items-center justify-center gap-3 mb-4">
                        <p className="text-3xl font-bold text-white">
                          {capitalizeWord(currentWord.word)}
                        </p>
                        {/* Play Sound Button */}
                        <button
                          onClick={() => {
                            const randomVoice = VOICES[Math.floor(Math.random() * VOICES.length)]
                            audioService.playWord(currentWord.word, 'emoji', randomVoice).catch(() => {})
                          }}
                          className="p-2 rounded-full bg-slate-700 hover:bg-slate-600 text-cyan-400 transition-colors"
                          aria-label={showChinese ? '播放發音' : 'Play pronunciation'}
                        >
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                          </svg>
                        </button>
                      </div>
                      <p className="text-sm text-slate-400 mt-1">
                        {showChinese 
                          ? `${smeltingProgress.currentWordIndex + 1} / ${currentWords.length}`
                          : `${smeltingProgress.currentWordIndex + 1} / ${currentWords.length}`
                        }
                      </p>
                    </div>
                    
                    {/* Start Review Button */}
                    <motion.button
                      onClick={() => {
                        // Generate MCQ options for current word
                        const distractors = DEMO_WORDS
                          .filter(w => w.sense_id !== currentWord.sense_id)
                          .sort(() => Math.random() - 0.5)
                          .slice(0, 3) // 3 distractors = 4 total options
                        const options = [currentWord, ...distractors].sort(() => Math.random() - 0.5)
                        
                        // Auto-play word audio
                        const randomVoice = VOICES[Math.floor(Math.random() * VOICES.length)]
                        audioService.playWord(currentWord.word, 'emoji', randomVoice).catch(() => {})
                        
                        setSmeltingProgress({
                          ...smeltingProgress,
                          showMcq: true,
                          smeltingMcqOptions: options,
                          smeltingAnswer: null,
                        })
                      }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold rounded-xl text-lg transition-all mb-4"
                    >
                      {showChinese ? '開始複習' : 'Start Review'}
                    </motion.button>
                  </>
                ) : (
                  // MCQ Review View
                  <>
                    <div className="mb-4">
                      <p className="text-lg text-white mb-4">
                        {showChinese 
                          ? '哪個表情符號符合這個單字？'
                          : 'Which emoji matches this word?'
                        }
                      </p>
                      <p className="text-2xl font-bold text-white mb-4">
                        {capitalizeWord(currentWord.word)}
                      </p>
                    </div>
                    
                    {/* MCQ Options */}
                    <div className="grid grid-cols-2 gap-4 mb-6 w-full">
                      {smeltingProgress.smeltingMcqOptions.map((option) => {
                        const isCorrect = option.sense_id === currentWord.sense_id
                        const isSelected = smeltingProgress.smeltingAnswer === option.sense_id
                        const hasFeedback = smeltingProgress.smeltingAnswer !== null
                        // In Day 5 demo, disable the correct answer
                        const isDisabled = isDay5Demo && isCorrect && !hasFeedback
                        
                        return (
                          <motion.button
                            key={option.sense_id}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            whileHover={!hasFeedback && !isDisabled ? { scale: 1.05 } : {}}
                            whileTap={!hasFeedback && !isDisabled ? { scale: 0.95 } : {}}
                            onClick={() => {
                              if (hasFeedback || isPlaying || isDisabled) return
                              
                              setSmeltingProgress((prev) => {
                                if (!prev) return null
                                return {
                                  ...prev,
                                  smeltingAnswer: option.sense_id,
                                }
                              })
                              
                              setIsPlaying(true)
                              
                              if (isCorrect) {
                                audioService.playSfx('correct').then(() => {
                                  setIsPlaying(false)
                                  // Move to next word in current interval after 1 second
                                  setTimeout(() => {
                                    // Use functional update to get latest state
                                    setSmeltingProgress((prev) => {
                                      if (!prev) return null
                                      
                                      const currentWords = prev.wordsByInterval[`interval${prev.currentInterval}` as keyof typeof prev.wordsByInterval]
                                      
                                      if (!currentWords || prev.currentWordIndex >= currentWords.length) {
                                        // Invalid state - exit
                                        return null
                                      }
                                      
                                      if (prev.currentWordIndex < currentWords.length - 1) {
                                        // Move to next word in same interval
                                        const nextWord = currentWords[prev.currentWordIndex + 1]
                                        const distractors = DEMO_WORDS
                                          .filter(w => w.sense_id !== nextWord.sense_id)
                                          .sort(() => Math.random() - 0.5)
                                          .slice(0, 3) // 3 distractors = 4 total options
                                        const options = [nextWord, ...distractors].sort(() => Math.random() - 0.5)
                                        
                                        return {
                                          ...prev,
                                          currentWordIndex: prev.currentWordIndex + 1,
                                          showMcq: false,
                                          smeltingMcqOptions: options,
                                          smeltingAnswer: null,
                                        }
                                      } else {
                                        // All words in current interval complete
                                        // Check if there are more intervals to process
                                        const nextInterval = prev.currentInterval + 1
                                        const nextIntervalKey = `interval${nextInterval}` as keyof typeof prev.wordsByInterval
                                        const nextIntervalWords = prev.wordsByInterval[nextIntervalKey] || []
                                        
                                        if (nextIntervalWords.length > 0 && nextInterval <= 2) {
                                          // Move to next interval
                                          const firstWord = nextIntervalWords[0]
                                          const distractors = DEMO_WORDS
                                            .filter(w => w.sense_id !== firstWord.sense_id)
                                            .sort(() => Math.random() - 0.5)
                                            .slice(0, 3)
                                          const options = [firstWord, ...distractors].sort(() => Math.random() - 0.5)
                                          
                                          return {
                                            ...prev,
                                            currentInterval: nextInterval,
                                            currentWordIndex: 0,
                                            showMcq: false,
                                            smeltingMcqOptions: options,
                                            smeltingAnswer: null,
                                          }
                                        } else {
                                          // All intervals complete - Mark all reviewed words as 'solid'
                                          const allReviewedWords = new Set<string>()
                                          Object.values(prev.wordsByInterval).forEach(words => {
                                            words.forEach(w => allReviewedWords.add(w.sense_id))
                                          })
                                          
                                          // Update word status
                                          setWordStatus((statusPrev) => {
                                            const next = new Map(statusPrev)
                                            allReviewedWords.forEach(senseId => {
                                              next.set(senseId, 'solid')
                                            })
                                            return next
                                          })
                                          
                                          // Remove reviewed words from resetWords
                                          setResetWords((resetPrev) => {
                                            const next = new Set(resetPrev)
                                            allReviewedWords.forEach(senseId => {
                                              next.delete(senseId)
                                            })
                                            return next
                                          })
                                          
                                          trackCampaignEvent(campaign, 'ctaClick', {
                                            action: 'review_session_completed',
                                            words_count: allReviewedWords.size,
                                            day: demoDay,
                                          })
                                          
                                          // After review session, go to day-complete or grid
                                          setTimeout(() => {
                                            if (demoDay < 7) {
                                              setStage('day-complete')
                                            } else {
                                              setStage('grid')
                                            }
                                          }, 0)
                                          
                                          return null // Clear smelting progress
                                        }
                                      }
                                    })
                                  }, 1000)
                                }).catch((err) => {
                                  console.warn('Audio error in smelting:', err)
                                  setIsPlaying(false)
                                })
                              } else {
                                audioService.playSfx('wrong').then(() => {
                                  setIsPlaying(false)
                                  
                                  // Special Day 5 Demo: Show reset explanation
                                  if (isSpecialDayDemo || stage === 'day5-demo-review') {
                                    // Capture currentWord from closure to avoid stale state
                                    const wordToReset = demoWordToReset || currentWord
                                    
                                    // REAL RESET LOGIC - Actually move word back to Day 1
                                    setWordsByDay(prev => {
                                      const next = new Map(prev)
                                      // Remove from all days
                                      for (let day = 1; day <= 7; day++) {
                                        const dayWords = next.get(day) || []
                                        const filtered = dayWords.filter(w => w.sense_id !== wordToReset.sense_id)
                                        if (filtered.length > 0) {
                                          next.set(day, filtered)
                                        } else if (dayWords.length > 0 && dayWords.some(w => w.sense_id === wordToReset.sense_id)) {
                                          next.delete(day)
                                        }
                                      }
                                      // Add to Day 1
                                      const day1Words = next.get(1) || []
                                      if (!day1Words.find(w => w.sense_id === wordToReset.sense_id)) {
                                        next.set(1, [...day1Words, wordToReset])
                                      }
                                      return next
                                    })
                                    
                                    // Reset status back to 'raw'
                                    setWordStatus(prev => {
                                      const next = new Map(prev)
                                      next.set(wordToReset.sense_id, 'raw')
                                      return next
                                    })
                                    
                                    // Mark word as reset so it appears in next day's review
                                    setResetWords(prev => {
                                      const next = new Set(prev)
                                      next.add(wordToReset.sense_id)
                                      return next
                                    })
                                    
                                    // Show reset explanation
                                    setTimeout(() => {
                                      setStage('reset-explanation')
                                      setSmeltingProgress(null)
                                    }, 1500)
                                  } else {
                                    // Normal retry logic - use functional update
                                    setTimeout(() => {
                                      setSmeltingProgress((prev) => {
                                        if (!prev) return null
                                        return {
                                          ...prev,
                                          smeltingAnswer: null,
                                        }
                                      })
                                    }, 1000)
                                  }
                                }).catch((err) => {
                                  console.warn('Audio error in smelting (wrong answer):', err)
                                  setIsPlaying(false)
                                  // Still allow retry even if audio fails
                                  setTimeout(() => {
                                    setSmeltingProgress((prev) => {
                                      if (!prev) return null
                                      return {
                                        ...prev,
                                        smeltingAnswer: null,
                                      }
                                    })
                                  }, 1000)
                                })
                              }
                            }}
                            disabled={hasFeedback || isPlaying || isDisabled}
                            className={`relative flex items-center justify-center rounded-2xl border-4 transition-all duration-200 min-h-[100px] ${
                              hasFeedback
                                ? isCorrect
                                  ? 'bg-emerald-500/30 border-emerald-400'
                                  : isSelected
                                  ? 'bg-red-500/30 border-red-400'
                                  : 'bg-slate-800/30 border-slate-700 opacity-50'
                                : isDisabled
                                ? 'bg-slate-800/30 border-slate-700 opacity-30 cursor-not-allowed'
                                : isSelected
                                ? 'bg-cyan-500/20 border-cyan-400 scale-95'
                                : 'bg-slate-800/50 border-slate-600 hover:border-slate-500 hover:bg-slate-700/50'
                            }`}
                          >
                            <span className="text-5xl">{option.emoji}</span>
                            
                            {/* Disabled Indicator for Day 5 Demo */}
                            {isDisabled && (
                              <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 rounded-2xl">
                                <div className="text-center">
                                  <span className="text-2xl mb-1 block">🚫</span>
                                  <span className="text-xs text-slate-400 font-bold">
                                    {showChinese ? '正確答案已鎖定' : 'Correct Answer Locked'}
                                  </span>
                                </div>
                              </div>
                            )}
                            
                            {/* Feedback Indicator */}
                            {hasFeedback && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
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
                          </motion.button>
                        )
                      })}
                    </div>
                  </>
                )}
              </>
            )}
            
            {/* Back Button */}
            <button
              onClick={() => {
                setStage('grid')
                setSmeltingProgress(null)
              }}
              className="mt-4 text-slate-400 hover:text-white text-sm transition-colors"
            >
              {showChinese ? '返回' : 'Back'}
            </button>
          </motion.div>
          )
        })()}
        </AnimatePresence>
      </div>
      
      {/* Paywall Modal */}
      <AnimatePresence>
        {showPaywallModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => {
              setShowPaywallModal(false)
              trackCampaignEvent(campaign, 'ctaClick', {
                action: 'paywall_modal_dismissed',
                forged_count: forgedWordsCount,
              })
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-8 max-w-md w-full border-2 border-amber-500/50 shadow-2xl"
            >
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">🎉</div>
                <h3 className="text-3xl font-black text-white mb-2">
                  {showChinese ? '你已經探索了 7 個單字！' : "You've Explored 7 Words!"}
                </h3>
                <p className="text-slate-400">
                  {showChinese 
                    ? '解鎖全部 200+ 單字，繼續你的學習之旅'
                    : 'Unlock all 200+ words to continue your learning journey'
                  }
                </p>
              </div>
              
              {/* Pricing Comparison */}
              <div className="bg-slate-700/50 rounded-xl p-4 mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-300 text-sm">
                    {showChinese ? '月費方案' : 'Monthly Plan'}
                  </span>
                  <span className="text-white font-bold">NT$99/月</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-amber-400 font-bold">
                    {showChinese ? '⭐ 最划算' : '⭐ Best Value'}
                  </span>
                  <span className="text-white font-bold text-xl">NT$299</span>
                </div>
                <p className="text-xs text-slate-400 mt-2 text-center">
                  {showChinese 
                    ? '一次付費，永久使用（3 個月回本）'
                    : 'One-time payment. Own forever (pays for itself in 3 months)'
                  }
                </p>
              </div>
              
              {/* CTAs */}
              <div className="space-y-3">
                <Link
                  href={`/signup?plan=lifetime&redirect=checkout&utm_source=demo&utm_medium=paywall&utm_campaign=${campaign.id}`}
                  onClick={() => {
                    trackCampaignEvent(campaign, 'checkoutStart', {
                      source: 'paywall_modal',
                      action: 'cta_clicked',
                      forged_count: forgedWordsCount,
                      plan: 'lifetime',
                    })
                    setShowPaywallModal(false)
                  }}
                  className="block w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold rounded-xl text-lg hover:from-amber-500 hover:to-orange-600 transition-all text-center"
                >
                  {showChinese ? '💳 購買永久版 - NT$299' : '💳 Buy Lifetime - NT$299'}
                </Link>
                <Link
                  href={`/signup?plan=monthly&redirect=checkout&utm_source=demo&utm_medium=paywall&utm_campaign=${campaign.id}`}
                  onClick={() => {
                    trackCampaignEvent(campaign, 'checkoutStart', {
                      source: 'paywall_modal',
                      action: 'cta_clicked',
                      forged_count: forgedWordsCount,
                      plan: 'monthly',
                    })
                    setShowPaywallModal(false)
                  }}
                  className="block w-full py-3 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-xl border border-slate-600 transition-all text-center"
                >
                  {showChinese ? '開始月費方案 - NT$99/月' : 'Start Monthly - NT$99/month'}
                </Link>
                <button
                  onClick={() => {
                    setShowPaywallModal(false)
                    trackCampaignEvent(campaign, 'ctaClick', {
                      action: 'paywall_modal_dismissed',
                      forged_count: forgedWordsCount,
                    })
                  }}
                  className="w-full py-2 text-slate-400 hover:text-white text-sm transition-colors"
                >
                  {showChinese ? '關閉' : 'Close'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

