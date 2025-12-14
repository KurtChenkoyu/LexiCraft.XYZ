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
    //   this.playGeneratedSfx(effect)
    // }
    
    this.playGeneratedSfx(effect)
  }
  
  /**
   * Generate simple sound effect using Web Audio API
   * Used as fallback when audio files are not available
   */
  private playGeneratedSfx(effect: SoundEffect): void {
    if (typeof window === 'undefined' || !window.AudioContext) return
    
    try {
      const ctx = new AudioContext()
      const oscillator = ctx.createOscillator()
      const gainNode = ctx.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(ctx.destination)
      
      const volume = masterVolume * sfxVolume * 0.3
      gainNode.gain.value = volume
      
      switch (effect) {
        case 'correct':
          // Happy ascending tone
          oscillator.frequency.setValueAtTime(523.25, ctx.currentTime) // C5
          oscillator.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1) // E5
          oscillator.frequency.setValueAtTime(783.99, ctx.currentTime + 0.2) // G5
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.3)
          break
          
        case 'wrong':
          // Descending buzz
          oscillator.type = 'sawtooth'
          oscillator.frequency.setValueAtTime(200, ctx.currentTime)
          oscillator.frequency.setValueAtTime(150, ctx.currentTime + 0.15)
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.2)
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
          break
          
        default:
          // Simple click
          oscillator.frequency.setValueAtTime(800, ctx.currentTime)
          gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.05)
          oscillator.start(ctx.currentTime)
          oscillator.stop(ctx.currentTime + 0.05)
      }
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
    if (typeof window === 'undefined') return
    
    try {
      let audio = audioCache.get(path)
      
      if (!audio) {
        audio = new Audio(path)
        audioCache.set(path, audio)
      }
      
      // Reset and play
      audio.currentTime = 0
      audio.volume = volume
      
      await audio.play().catch(err => {
        // Browser might block autoplay - fail silently
        console.warn('Audio playback blocked:', err.message)
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

