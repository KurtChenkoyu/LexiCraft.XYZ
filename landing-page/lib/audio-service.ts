/**
 * Audio Service for LexiCraft
 * 
 * Handles loading and playing audio for:
 * - Word pronunciations (TTS from OpenAI)
 * - UI feedback sounds
 * - Celebration sounds
 * 
 * Audio file locations:
 * - /audio/emoji/{word}_{voice}.mp3 - Emoji pack word pronunciations
 *   Voices: alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer
 * - /audio/fx/correct.mp3 - Correct answer sound
 * - /audio/fx/wrong.mp3 - Wrong answer sound
 * - /audio/fx/celebrate.mp3 - Celebration sound
 */

// Audio cache to prevent reloading
const audioCache = new Map<string, HTMLAudioElement>()

// Volume settings
let masterVolume = 1.0
let sfxVolume = 1.0
let voiceVolume = 1.0

/**
 * Available OpenAI TTS voices
 * Each word has 9 voice variants for variety
 */
export const VOICES = ['alloy', 'ash', 'coral', 'echo', 'fable', 'nova', 'onyx', 'sage', 'shimmer'] as const
export type Voice = typeof VOICES[number]

// Default voice for consistent experience (nova is clear and friendly)
export const DEFAULT_VOICE: Voice = 'nova'

/**
 * Audio file paths by category
 */
export const AUDIO_PATHS = {
  emoji: '/audio/emoji',     // {word}_{voice}.mp3
  legacy: '/audio/legacy',   // {sense_id}.wav (future)
  fx: '/audio/fx',           // UI sound effects
  prompts: '/audio/prompts', // {prompt_id}_{voice}.mp3 (in category subdirs)
  feedback: '/audio/feedback', // {feedback_id}_{voice}.mp3 (in category subdirs)
} as const

/**
 * Sound effect types
 */
export type SoundEffect = 
  | 'correct'     // Correct answer ding
  | 'wrong'       // Wrong answer buzz
  | 'celebrate'   // Big celebration
  | 'click'       // Button click
  | 'unlock'      // Achievement unlocked
  | 'levelup'     // Level up fanfare

/**
 * Audio Service singleton
 */
class AudioServiceClass {
  private enabled = true
  private preloadedSounds = new Map<SoundEffect, HTMLAudioElement>()
  
  constructor() {
    // Check localStorage for audio preference
    if (typeof window !== 'undefined') {
      const savedEnabled = localStorage.getItem('lexicraft_audio_enabled')
      this.enabled = savedEnabled !== 'false'
    }
  }
  
  /**
   * Toggle audio on/off
   */
  setEnabled(enabled: boolean) {
    this.enabled = enabled
    if (typeof window !== 'undefined') {
      localStorage.setItem('lexicraft_audio_enabled', String(enabled))
    }
  }
  
  isEnabled() {
    return this.enabled
  }
  
  /**
   * Set volume levels (0-1)
   */
  setMasterVolume(volume: number) {
    masterVolume = Math.max(0, Math.min(1, volume))
  }
  
  setSfxVolume(volume: number) {
    sfxVolume = Math.max(0, Math.min(1, volume))
  }
  
  setVoiceVolume(volume: number) {
    voiceVolume = Math.max(0, Math.min(1, volume))
  }
  
  /**
   * Play word pronunciation for emoji pack
   * Uses OpenAI TTS voice files with pattern: {word}_{voice}.mp3
   * 
   * @param word - The word to pronounce
   * @param pack - 'emoji' or 'legacy'
   * @param voice - Optional specific voice, or random/default if undefined
   */
  async playWord(
    word: string, 
    pack: 'emoji' | 'legacy' = 'emoji',
    voice?: Voice | 'random'
  ): Promise<void> {
    if (!this.enabled) return
    
    const basePath = pack === 'emoji' ? AUDIO_PATHS.emoji : AUDIO_PATHS.legacy
    const cleanWord = word.toLowerCase().replace(/\s+/g, '_')
    
    // Select voice
    let selectedVoice: Voice
    if (voice === 'random') {
      selectedVoice = VOICES[Math.floor(Math.random() * VOICES.length)]
    } else if (voice) {
      selectedVoice = voice
    } else {
      selectedVoice = DEFAULT_VOICE
    }
    
    // Emoji pack uses: {word}_{voice}.mp3
    // Legacy pack uses: {sense_id}.wav
    const path = pack === 'emoji' 
      ? `${basePath}/${cleanWord}_${selectedVoice}.mp3`
      : `${basePath}/${cleanWord}.wav`
    
    return this.playAudio(path, masterVolume * voiceVolume)
  }
  
  /**
   * Play word with a random voice for variety
   */
  async playWordRandom(word: string, pack: 'emoji' | 'legacy' = 'emoji'): Promise<void> {
    return this.playWord(word, pack, 'random')
  }
  
  /**
   * Play sound effect
   * Uses generated Web Audio since we don't have SFX files yet
   */
  async playSfx(effect: SoundEffect): Promise<void> {
    if (!this.enabled) return
    
    // For now, always use generated sound (no files in /audio/fx/)
    // TODO: Once we have real SFX files, uncomment file-based playback
    // const path = `${AUDIO_PATHS.fx}/${effect}.mp3`
    // try {
    //   await this.playAudio(path, masterVolume * sfxVolume)
    // } catch {
    //   return this.playGeneratedSfx(effect)
    // }
    
    return this.playGeneratedSfx(effect)
  }
  
  /**
   * Generate simple sound effect using Web Audio API
   * Used as fallback when audio files are not available
   */
  private async playGeneratedSfx(effect: SoundEffect): Promise<void> {
    if (typeof window === 'undefined' || !window.AudioContext) return
    
    try {
      const ctx = new AudioContext()
      const oscillator = ctx.createOscillator()
      const gainNode = ctx.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(ctx.destination)
      
      const volume = masterVolume * sfxVolume * 0.3
      gainNode.gain.value = volume
      
      let duration = 0.3 // Default duration
      
      switch (effect) {
        case 'correct':
          // Happy ascending tone
          oscillator.frequency.setValueAtTime(523.25, ctx.currentTime) // C5
          oscillator.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1) // E5
          oscillator.frequency.setValueAtTime(783.99, ctx.currentTime + 0.2) // G5
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.3)
          duration = 0.3
          break
          
        case 'wrong':
          // Descending buzz
          oscillator.type = 'sawtooth'
          oscillator.frequency.setValueAtTime(200, ctx.currentTime)
          oscillator.frequency.setValueAtTime(150, ctx.currentTime + 0.15)
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.2)
          duration = 0.2
          break
          
        case 'celebrate':
          // Fanfare-like sound
          oscillator.frequency.setValueAtTime(523.25, ctx.currentTime) // C5
          oscillator.frequency.setValueAtTime(659.25, ctx.currentTime + 0.15) // E5
          oscillator.frequency.setValueAtTime(783.99, ctx.currentTime + 0.3) // G5
          oscillator.frequency.setValueAtTime(1046.50, ctx.currentTime + 0.45) // C6
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.6)
          duration = 0.6
          break
          
        default:
          // Simple click
          oscillator.frequency.setValueAtTime(800, ctx.currentTime)
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.05)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.05)
          duration = 0.05
      }
      
      // Wait for the sound to finish
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          resolve()
        }, duration * 1000 + 50) // Add 50ms buffer
      })
    } catch (err) {
      console.warn('Failed to generate SFX:', err)
    }
  }
  
  /**
   * Play correct answer sound
   */
  async playCorrect(): Promise<void> {
    return this.playSfx('correct')
  }
  
  /**
   * Play wrong answer sound
   */
  async playWrong(): Promise<void> {
    return this.playSfx('wrong')
  }
  
  /**
   * Play celebration sound
   */
  async playCelebrate(): Promise<void> {
    return this.playSfx('celebrate')
  }
  
  /**
   * Internal: Play audio file
   */
  private async playAudio(path: string, volume: number): Promise<void> {
    // Silently fail if audio files don't exist (MVP: audio files not yet generated)
    // This prevents 404 errors from cluttering the console
    if (typeof window === 'undefined') return
    
    try {
      let audio = audioCache.get(path)
      
      if (!audio) {
        audio = new Audio(path)
        // Handle 404 errors silently (audio files not yet generated for MVP)
        audio.addEventListener('error', (e) => {
          // Silently ignore 404 errors for missing audio files
          if (audio?.error?.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED) {
            // File doesn't exist - expected for MVP, fail silently
            return
          }
        })
        audioCache.set(path, audio)
      }
      
      // Check if audio failed to load (404)
      if (audio?.error?.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED) {
        // File doesn't exist - expected for MVP, fail silently
        return
      }
      
      // Reset and play
      audio.currentTime = 0
      audio.volume = volume
      
      await audio.play().catch(err => {
        // Browser might block autoplay or file doesn't exist - fail silently
        // Don't log 404 errors for missing audio files (expected in MVP)
        if (!err.message?.includes('404') && !err.message?.includes('Failed to load')) {
          console.warn('Audio playback blocked:', err.message)
        }
      })
      
      // Wait for audio to finish playing
      return new Promise<void>((resolve) => {
        const handleEnded = () => {
          audio.removeEventListener('ended', handleEnded)
          resolve()
        }
        audio.addEventListener('ended', handleEnded)
        
        // Fallback: resolve after a maximum duration (3 seconds) to prevent hanging
        setTimeout(() => {
          audio.removeEventListener('ended', handleEnded)
          resolve()
        }, 3000)
      })
    } catch (err) {
      console.warn('Failed to play audio:', path, err)
    }
  }
  
  /**
   * Preload audio files for instant playback
   */
  async preloadSfx(effects: SoundEffect[]): Promise<void> {
    if (typeof window === 'undefined') return
    
    for (const effect of effects) {
      const path = `${AUDIO_PATHS.fx}/${effect}.mp3`
      const audio = new Audio()
      audio.preload = 'auto'
      audio.src = path
      audioCache.set(path, audio)
    }
  }
  
  /**
   * Preload word pronunciations
   * Only preloads the default voice to save bandwidth
   */
  async preloadWords(words: string[], pack: 'emoji' | 'legacy' = 'emoji'): Promise<void> {
    if (typeof window === 'undefined') return
    
    const basePath = pack === 'emoji' ? AUDIO_PATHS.emoji : AUDIO_PATHS.legacy
    
    for (const word of words) {
      const cleanWord = word.toLowerCase().replace(/\s+/g, '_')
      
      // Preload default voice only
      const path = pack === 'emoji'
        ? `${basePath}/${cleanWord}_${DEFAULT_VOICE}.mp3`
        : `${basePath}/${cleanWord}.wav`
      
      const audio = new Audio()
      audio.preload = 'auto'
      audio.src = path
      audioCache.set(path, audio)
    }
  }
  
  /**
   * Get all available voice variants for a word
   */
  getWordVariants(word: string, pack: 'emoji' | 'legacy' = 'emoji'): string[] {
    const basePath = pack === 'emoji' ? AUDIO_PATHS.emoji : AUDIO_PATHS.legacy
    const cleanWord = word.toLowerCase().replace(/\s+/g, '_')
    
    if (pack === 'emoji') {
      // Return all 9 voice variants
      return VOICES.map(voice => `${basePath}/${cleanWord}_${voice}.mp3`)
    }
    
    return [`${basePath}/${cleanWord}.wav`]
  }
  
/**
 * Play MCQ question prompt audio
 * @param promptId - ID of the prompt (e.g., 'which_emoji_matches', 'click_on_apple')
 * @param category - Category subdirectory ('questions' or 'instructions')
 * @param voice - Optional specific voice (defaults to the voice specified in the prompt data)
 */
async playPrompt(
  promptId: string,
  category: 'questions' | 'instructions' = 'questions',
  voice?: Voice
): Promise<void> {
  if (!this.enabled) return
  
  // Normalize prompt ID for filename
  const normalizedId = promptId.toLowerCase().replace(/\s+/g, '_').replace('?', '').replace('!', '').replace(',', '').replace("'", "")
  
  // Load prompt data to get the correct voice if not specified
  let selectedVoice: Voice = voice || 'echo' // Fallback default
  
  if (!voice) {
    try {
      const response = await fetch('/data/audio-prompts.json')
      const data = await response.json()
      
      // Search through all prompt categories to find the matching prompt
      for (const promptCategory of Object.values(data.prompts || {})) {
        const prompts = Array.isArray(promptCategory) ? promptCategory : []
        const prompt = prompts.find((p: any) => p.id === promptId)
        if (prompt && prompt.voice) {
          selectedVoice = prompt.voice as Voice
          break
        }
      }
    } catch (err) {
      // If loading fails, use fallback default based on category
      selectedVoice = category === 'questions' ? 'echo' : 'nova'
      console.warn('Failed to load prompt data, using default voice:', err)
    }
  }
  
  const path = `${AUDIO_PATHS.prompts}/${category}/${normalizedId}_${selectedVoice}.mp3`
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔊 Playing prompt: ${path}`)
  }
  
  return this.playAudio(path, masterVolume * voiceVolume).catch(err => {
    console.warn(`Failed to play prompt audio at ${path}:`, err)
    // Don't throw, just log warning so game continues
  })
}

/**
 * Play MCQ feedback message audio
 * @param feedbackId - ID of the feedback (e.g., 'well_done', 'almost_so_close')
 * @param category - Category ('correct' or 'incorrect')
 * @param voice - Optional specific voice (defaults to the voice specified in the feedback data)
 */
async playFeedback(
  feedbackId: string,
  category: 'correct' | 'incorrect' = 'correct',
  voice?: Voice
): Promise<void> {
  if (!this.enabled) return
  
  // Normalize feedback ID for filename
  // The IDs from JSON are already normalized (well_done, youre_on_fire, etc.)
  // But handle edge cases where text might be passed instead of ID
  // "Well Done!" -> "well_done"
  // "Try Again..." -> "try_again"
  const normalizedId = feedbackId
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '_') // Replace non-alphanumeric with _
    .replace(/^_+|_+$/g, '')     // Trim leading/trailing _
  
  // If voice not specified, use default (coral for correct, nova for incorrect)
  const defaultVoice = category === 'correct' ? 'coral' : 'nova'
  const selectedVoice = voice || defaultVoice
  
  const path = `${AUDIO_PATHS.feedback}/${category}/${normalizedId}_${selectedVoice}.mp3`
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔊 Attempting to play feedback: ${path}`)
  }
  
  // Calculate volume with emphasis (1.1x) but clamp to valid range [0, 1]
  const calculatedVolume = masterVolume * voiceVolume * 1.1
  const clampedVolume = Math.max(0, Math.min(1, calculatedVolume))
  
  return this.playAudio(path, clampedVolume).catch(err => {
    console.warn(`Failed to play feedback audio at ${path}:`, err)
    // Don't throw, just log warning so game continues
  })
}

/**
 * Play a random feedback message from a category
 * @param category - 'correct' or 'incorrect'
 * @param voice - Optional specific voice
 */
async playRandomFeedback(
  category: 'correct' | 'incorrect',
  voice?: Voice
): Promise<void> {
  // Load feedback data to get available IDs
  try {
    const response = await fetch('/data/audio-feedback.json')
    const data = await response.json()
    const feedbackItems = data.feedback[category] || []
    
    if (feedbackItems.length === 0) {
      console.warn(`No feedback items found for category: ${category}`)
      return
    }
    
    // Pick random feedback
    const randomItem = feedbackItems[Math.floor(Math.random() * feedbackItems.length)]
    const feedbackId = randomItem.id
    const defaultVoice = randomItem.voice || (category === 'correct' ? 'coral' : 'nova')
    const selectedVoice = voice || defaultVoice
    
    await this.playFeedback(feedbackId, category, selectedVoice)
  } catch (err) {
    console.warn('Failed to load feedback data:', err)
    // Fallback to a simple feedback
    const fallbackId = category === 'correct' ? 'well_done' : 'good_try'
    await this.playFeedback(fallbackId, category, voice)
  }
}

/**
 * Preload prompt audio files
 */
async preloadPrompts(promptIds: string[], category: 'questions' | 'instructions' = 'questions'): Promise<void> {
  if (typeof window === 'undefined') return
  
  for (const promptId of promptIds) {
    const normalizedId = promptId.toLowerCase().replace(/\s+/g, '_').replace('?', '').replace('!', '').replace(',', '').replace("'", "")
    // Try to load with default voice (we'll need to check the actual voice from data)
    const defaultVoice = category === 'questions' ? 'echo' : 'nova'
    const path = `${AUDIO_PATHS.prompts}/${category}/${normalizedId}_${defaultVoice}.mp3`
    
    const audio = new Audio()
    audio.preload = 'auto'
    audio.src = path
    audioCache.set(path, audio)
  }
}

/**
 * Preload feedback audio files
 */
async preloadFeedback(feedbackIds: string[], category: 'correct' | 'incorrect' = 'correct'): Promise<void> {
  if (typeof window === 'undefined') return
  
  for (const feedbackId of feedbackIds) {
    const normalizedId = feedbackId.toLowerCase().replace(/\s+/g, '_').replace('?', '').replace('!', '').replace(',', '').replace("'", "")
    const defaultVoice = category === 'correct' ? 'coral' : 'nova'
    const path = `${AUDIO_PATHS.feedback}/${category}/${normalizedId}_${defaultVoice}.mp3`
    
    const audio = new Audio()
    audio.preload = 'auto'
    audio.src = path
    audioCache.set(path, audio)
  }
}

/**
 * Get list of all available voices
 */
getAvailableVoices(): readonly Voice[] {
  return VOICES
}

/**
 * Clear audio cache
 */
clearCache() {
  audioCache.clear()
}
}

// Export singleton
export const audioService = new AudioServiceClass()

// Convenience hooks for React
export function useAudio() {
  return audioService
}

