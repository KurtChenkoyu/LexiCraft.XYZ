/**
 * CACHING STRATEGY (IMMUTABLE - DO NOT CHANGE):
 * 
 * This file follows the "Last War" caching approach:
 * - IndexedDB is the ONLY cache for user data
 * - localStorage is FORBIDDEN for user data
 * - Load from IndexedDB first, sync from API in background
 * 
 * See: docs/ARCHITECTURE_PRINCIPLES.md
 * 
 * DO NOT add localStorage usage for user data here.
 */

/**
 * Download Service - Background data synchronization
 * 
 * Pre-downloads all user data on login for instant page loads.
 * Uses IndexedDB for persistent caching across sessions.
 */

import { localStore } from '@/lib/local-store'
import { authenticatedGet } from '@/lib/api-client'
import { 
  learnerProfileApi, 
  goalsApi, 
  notificationsApi,
  leaderboardsApi,
  LearnerGamificationProfile,
  Achievement,
  StreakInfo,
  Goal,
  Notification,
  LeaderboardEntry,
} from '@/services/gamificationApi'
import type { LearnerProfile } from '@/stores/useAppStore'

// Cache keys
const CACHE_KEYS = {
  PROFILE: 'user_profile',
  LEARNER_PROFILE: 'learner_profile',
  ACHIEVEMENTS: 'achievements',
  STREAKS: 'streaks',
  GOALS: 'goals',
  NOTIFICATIONS: 'notifications',
  CHILDREN: 'children',
  CHILDREN_SUMMARIES: 'children_summaries',
  LEARNERS: 'learners',  // Multi-profile system
  BALANCE: 'balance',
  PROGRESS: 'learning_progress',
  LEADERBOARD: 'leaderboard',
  DUE_CARDS: 'due_cards',
  CURRENCIES: 'currencies',
  ROOMS: 'rooms',
  LAST_SYNC: 'last_full_sync',
}

// Learner-scoped helpers
const getLearnerDueCardsCacheKey = (learnerId: string) =>
  `${CACHE_KEYS.DUE_CARDS}_${learnerId}`

const getLearnerCurrenciesKey = (learnerId: string) =>
  `${CACHE_KEYS.CURRENCIES}_${learnerId}`

const getLearnerRoomsKey = (learnerId: string) =>
  `${CACHE_KEYS.ROOMS}_${learnerId}`

export const getLearnerMineBlocksKey = (learnerId: string) =>
  `emoji_mine_blocks_${learnerId}`

// Cache TTLs (in ms) - Using very long TTLs for offline-first approach
// Data persists until explicitly invalidated (mutations, manual refresh, logout)
// These long TTLs ensure data remains available even when backend is down
const CACHE_TTL = {
  SHORT: 7 * 24 * 60 * 60 * 1000,   // 7 days - frequently changing data
  MEDIUM: 30 * 24 * 60 * 60 * 1000, // 30 days - moderately stable (children, profile)
  LONG: 365 * 24 * 60 * 60 * 1000,  // 1 year - rarely changing (effectively permanent)
}

// Types
interface DownloadProgress {
  total: number
  completed: number
  current: string
  errors: string[]
}

type ProgressCallback = (progress: DownloadProgress) => void

interface UserProfile {
  id: string
  email: string
  name: string | null
  age: number | null
  roles: string[]
  email_confirmed: boolean
}

interface Child {
  id: string
  name: string | null
  age: number | null
  email: string
}

interface ChildSummary {
  id: string
  name: string | null
  age: number | null
  email: string
  level: number
  total_xp: number
  current_streak: number
  vocabulary_size: number
  words_learned_this_week: number
  last_active_date: string | null
}

interface Balance {
  total_earned: number
  available_points: number
  locked_points: number
  withdrawn_points: number
}

interface ProgressData {
  progress: Array<{ sense_id: string; status: string; tier?: number }>
  stats: { total_discovered: number; solid_count: number; hollow_count: number; raw_count: number }
}

interface DueCard {
  verification_schedule_id: number
  learning_progress_id: number
  learning_point_id: string
  word: string | null
  scheduled_date: string
  days_overdue: number
  mastery_level: string
  retention_predicted: number | null
}

/**
 * Download Service
 */
class DownloadService {
  private isDownloading = false
  private lastSyncTime = 0
  private minSyncInterval = 60 * 1000 // 1 minute minimum between syncs

  /**
   * Check if we should sync (not too frequent)
   */
  shouldSync(): boolean {
    return Date.now() - this.lastSyncTime > this.minSyncInterval
  }

  /**
   * Download ALL user data in parallel
   * Call this on login or app startup
   */
  async downloadAllUserData(
    userId: string,
    onProgress?: ProgressCallback
  ): Promise<{ success: boolean; errors: string[] }> {
    if (this.isDownloading) {
      return { success: false, errors: ['Download already in progress'] }
    }

    if (!this.shouldSync()) {
      console.debug('Skipping sync - too recent')
      return { success: true, errors: [] }
    }

    this.isDownloading = true
    const errors: string[] = []
    const tasks = [
      'profile',
      'children',
      'learnerProfile',
      'achievements',
      'streaks',
      'goals',
      'notifications',
      'progress',
      'leaderboard',
      'dueCards',
    ]

    const progress: DownloadProgress = {
      total: tasks.length,
      completed: 0,
      current: '',
      errors: [],
    }

    const updateProgress = (task: string, error?: string) => {
      progress.completed++
      progress.current = task
      if (error) {
        progress.errors.push(error)
        errors.push(error)
      }
      onProgress?.(progress)
    }

    console.log('📥 Starting background download of all user data...')

    // Helper: Timeout wrapper for background syncs (5s timeout)
    const downloadWithTimeout = async <T>(
      taskName: string,
      downloadFn: () => Promise<T>,
      timeoutMs: number = 5000 // 5 seconds for background sync
    ): Promise<T | null> => {
      try {
        const result = await Promise.race([
          downloadFn(),
          new Promise<null>((_, reject) => 
            setTimeout(() => reject(new Error(`timeout of ${timeoutMs}ms exceeded`)), timeoutMs)
          )
        ])
        return result
      } catch (error: any) {
        const errorMsg = `${taskName}: ${error.message || 'timeout'}`
        // Only warn for real errors, not just skipping due to cache
        if (!error.message?.includes('skipped')) {
          console.warn(`⚠️ ${errorMsg}`)
        }
        return null
      }
    }

    // Run all downloads in parallel with error handling and timeouts
    const downloadTasks = [
      // 1. User Profile
      downloadWithTimeout('Profile', () => this.downloadWithCache(
        CACHE_KEYS.PROFILE,
        () => authenticatedGet<UserProfile>('/api/users/me'),
        CACHE_TTL.MEDIUM
      )).then(() => updateProgress('profile'))
        .catch(e => updateProgress('profile', `Profile: ${e.message}`)),

      // 2. Children
      downloadWithTimeout('Children', () => this.downloadWithCache(
        CACHE_KEYS.CHILDREN,
        () => authenticatedGet<Child[]>('/api/users/me/children').catch(() => []),
        CACHE_TTL.MEDIUM
      )).then(() => updateProgress('children'))
        .catch(e => updateProgress('children', `Children: ${e.message}`)),

      // 2b. Learners (Multi-Profile System - NEW)
      downloadWithTimeout('Learners', () => this.downloadWithCache(
        CACHE_KEYS.LEARNERS,
        () => authenticatedGet<LearnerProfile[]>('/api/users/me/learners').catch(() => []),
        CACHE_TTL.MEDIUM
      )).then(() => updateProgress('learners'))
        .catch(e => updateProgress('learners', `Learners: ${e.message}`)),

      // 3. Learner Profile (gamification)
      downloadWithTimeout('Learner Profile', () => this.downloadWithCache(
        CACHE_KEYS.LEARNER_PROFILE,
        () => learnerProfileApi.getProfile(),
        CACHE_TTL.SHORT
      )).then(() => updateProgress('learnerProfile'))
        .catch(e => updateProgress('learnerProfile', `Learner Profile: ${e.message}`)),

      // 4. Achievements
      downloadWithTimeout('Achievements', () => this.downloadWithCache(
        CACHE_KEYS.ACHIEVEMENTS,
        () => learnerProfileApi.getAchievements(),
        CACHE_TTL.MEDIUM
      )).then(() => updateProgress('achievements'))
        .catch(e => updateProgress('achievements', `Achievements: ${e.message}`)),

      // 5. Streaks
      downloadWithTimeout('Streaks', () => this.downloadWithCache(
        CACHE_KEYS.STREAKS,
        () => learnerProfileApi.getStreaks(),
        CACHE_TTL.SHORT
      )).then(() => updateProgress('streaks'))
        .catch(e => updateProgress('streaks', `Streaks: ${e.message}`)),

      // 6. Goals
      downloadWithTimeout('Goals', () => this.downloadWithCache(
        CACHE_KEYS.GOALS,
        () => goalsApi.getGoals().catch(() => []),
        CACHE_TTL.MEDIUM
      )).then(() => updateProgress('goals'))
        .catch(e => updateProgress('goals', `Goals: ${e.message}`)),

      // 7. Notifications
      downloadWithTimeout('Notifications', () => this.downloadWithCache(
        CACHE_KEYS.NOTIFICATIONS,
        () => notificationsApi.getNotifications(false, 50).catch(() => []),
        CACHE_TTL.SHORT
      )).then(() => updateProgress('notifications'))
        .catch(e => updateProgress('notifications', `Notifications: ${e.message}`)),

      // 8. Learning Progress
      // Download progress for all learners (fallback if Bootstrap failed)
      downloadWithTimeout('Progress', async () => {
        try {
          // Try to get learners from cache first (should be available from step 2b)
          const learners = await this.getCached<LearnerProfile[]>(CACHE_KEYS.LEARNERS)
          
          if (learners && learners.length > 0) {
            // Download progress for all learners in parallel (with individual timeouts)
            const progressPromises = learners.map(learner => 
              downloadWithTimeout(`Progress-${learner.id}`, () => this.downloadProgress(learner.id), 10000) // Increased from 3000ms to allow slower API responses
            )
            
            await Promise.allSettled(progressPromises)
            
            if (process.env.NODE_ENV === 'development') {
              console.log(`📥 Background sync: Attempted progress download for ${learners.length} learners`)
            }
          } else {
            // Fallback: Try to get active learner from store (if available)
            // This is a last resort if learners cache is empty
            try {
              const { useAppStore } = await import('@/stores/useAppStore')
              const activeLearner = useAppStore.getState().activeLearner
              if (activeLearner?.id) {
                await this.downloadProgress(activeLearner.id)
                if (process.env.NODE_ENV === 'development') {
                  console.log(`📥 Background sync: Downloaded progress for active learner ${activeLearner.id}`)
                }
              }
            } catch (storeErr) {
              // Store not available - silently skip
              if (process.env.NODE_ENV === 'development') {
                console.debug('Background sync: Could not access store for active learner')
              }
            }
          }
          
          return true
        } catch (error) {
          // Don't throw - progress download is non-critical for background sync
          if (process.env.NODE_ENV === 'development') {
            console.debug('Background sync: Progress download failed (non-critical):', error)
          }
          return true
        }
      }).then(() => updateProgress('progress'))
        .catch(e => updateProgress('progress', `Progress: ${e.message}`)),

      // 9. Leaderboard (weekly XP - default view)
      downloadWithTimeout('Leaderboard', () => this.downloadWithCache(
        CACHE_KEYS.LEADERBOARD,
        () => leaderboardsApi.getGlobal('weekly', 50, 'xp').catch(() => []),
        CACHE_TTL.SHORT
      )).then(() => updateProgress('leaderboard'))
        .catch(e => updateProgress('leaderboard', `Leaderboard: ${e.message}`)),

      // 10. Due Cards for verification
      downloadWithTimeout('Due Cards', () => this.downloadWithCache(
        CACHE_KEYS.DUE_CARDS,
        () => authenticatedGet<DueCard[]>('/api/v1/verification/due?limit=50').catch(() => []),
        CACHE_TTL.SHORT
      )).then(() => updateProgress('dueCards'))
        .catch(e => updateProgress('dueCards', `Due Cards: ${e.message}`)),
    ]

    await Promise.allSettled(downloadTasks)

    this.isDownloading = false
    this.lastSyncTime = Date.now()
    await localStore.setCache(CACHE_KEYS.LAST_SYNC, Date.now())

    console.log(`✅ Background download complete. ${errors.length} errors.`)
    
    return { success: errors.length === 0, errors }
  }

  /**
   * Download data and cache it
   */
  private async downloadWithCache<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T | null> {
    try {
      const data = await fetcher()
      await localStore.setCache(key, data, ttl)
      return data
    } catch (error) {
      console.debug(`Failed to download ${key}:`, error)
      throw error
    }
  }

  /**
   * Download learning progress and import into IndexedDB (learner-scoped)
   * 
   * @param learnerId Learner ID to fetch progress for (required)
   */
  private async downloadProgress(learnerId: string): Promise<void> {
    if (!learnerId) {
      console.warn('⚠️ downloadProgress called without learnerId - skipping')
      return
    }
    try {
      const url = `/api/v1/mine/progress?learner_id=${learnerId}`
      const data = await authenticatedGet<ProgressData>(url)

      // IMPORTANT (Last War compatible):
      // - Only reach this point if network call succeeded (HTTP 200).
      // - Even if data.progress is empty, we must treat the backend as
      //   canonical and clear any stale local progress for this learner.
      if (data && Array.isArray(data.progress)) {
        // 1) Import into the progress store (learner-scoped)
        //    This will clear all existing rows for this learner and replace
        //    them with the provided array (possibly empty).
        await localStore.importProgress(learnerId, data.progress)

        // 2) Cache full response (keyed by learnerId) for quick stats access
        const cacheKey = `${CACHE_KEYS.PROGRESS}_${learnerId}`
        await localStore.setCache(cacheKey, data, CACHE_TTL.SHORT)

        // 3) Update Zustand store if emoji pack is active and this is
        //    the active learner. This keeps Mine / collection / profile
        //    perfectly aligned with the new learner-scoped state.
        try {
          const { useAppStore } = await import('@/stores/useAppStore')
          const store = useAppStore.getState()

          if (store.activePack?.id === 'emoji_core' && store.activeLearner?.id === learnerId) {
            const progressMap = await localStore.getAllProgress(learnerId)
            const srsLevelsMap = await localStore.getSRSLevels(learnerId)

            const { packLoader } = await import('@/lib/pack-loader')
            const packData = await packLoader.loadPack('emoji_core')
            
            // Always create Maps (even if packData fails) for consistent pipeline
            const emojiProgressMap = new Map<string, string>()
            const emojiSRSMap = new Map<string, string>()
            
            if (packData) {
              const emojiSenseIds = new Set(packData.vocabulary.map(w => w.sense_id))

              progressMap.forEach((status, senseId) => {
                if (emojiSenseIds.has(senseId)) {
                  emojiProgressMap.set(senseId, status)
                }
              })

              srsLevelsMap.forEach((masteryLevel, senseId) => {
                if (emojiSenseIds.has(senseId)) {
                  emojiSRSMap.set(senseId, masteryLevel)
                }
              })
            }
            // Even if packData is null, we still update with empty Maps (not null)
            // This ensures the pipeline is consistent - Maps are always Maps
            
            // CRITICAL: Double-check learner is still active before updating (race condition protection)
            // Get fresh state to avoid race conditions where learner switches during async operations
            const freshState = useAppStore.getState()
            if (freshState.activeLearner?.id !== learnerId) {
              if (process.env.NODE_ENV === 'development') {
                console.log(
                  `⏭️ Skipping emojiProgress update: learner ${learnerId} is no longer active (current: ${freshState.activeLearner?.id})`,
                )
              }
              return
            }
            
            // Fresh Map references ensure subscribers re-render
            store.setEmojiProgress(new Map(emojiProgressMap))
            store.setEmojiSRSLevels(new Map(emojiSRSMap))

            // Rebuild collectedWords from fresh progress data
            if (packData && emojiProgressMap.size > 0) {
              const collectedWords: import('@/stores/useAppStore').CollectedWord[] = []
              
              emojiProgressMap.forEach((status, senseId) => {
                const wordData = packData.vocabulary.find(w => w.sense_id === senseId)
                if (wordData) {
                  const masteryLevel = emojiSRSMap.get(senseId) || 'learning'
                  collectedWords.push({
                    ...wordData,
                    collectedAt: Date.now(),  // Will be merged with existing if present
                    status: status as 'hollow' | 'solid' | 'mastered',
                    masteryLevel: masteryLevel as 'learning' | 'familiar' | 'known' | 'mastered' | 'burned'
                  })
                }
              })
              
              // Merge with existing to preserve timestamps
              const existing = await localStore.getCollectedWords(learnerId)
              const collectedAtMap = new Map(existing.map(w => [w.sense_id, w.collectedAt]))
              const masteredAtMap = new Map(existing.map(w => [w.sense_id, w.masteredAt]).filter(([_, t]) => t !== undefined))
              const isArchivedMap = new Map(existing.map(w => [w.sense_id, w.isArchived || false]))
              
              collectedWords.forEach(w => {
                if (collectedAtMap.has(w.sense_id)) {
                  w.collectedAt = collectedAtMap.get(w.sense_id)!
                }
                if (masteredAtMap.has(w.sense_id)) {
                  w.masteredAt = masteredAtMap.get(w.sense_id)!
                }
                if (isArchivedMap.has(w.sense_id)) {
                  w.isArchived = isArchivedMap.get(w.sense_id)!
                }
              })
              
              // Add any archived words that might not be in progressMap
              existing.forEach(existingWord => {
                if (existingWord.isArchived && !collectedWords.find(w => w.sense_id === existingWord.sense_id)) {
                  collectedWords.push(existingWord)  // Keep archived words in collection
                }
              })
              
              // Set masteredAt timestamp when mastery level reaches 'mastered'
              collectedWords.forEach(w => {
                if (w.masteryLevel === 'mastered' && !w.masteredAt) {
                  w.masteredAt = Date.now()  // CRITICAL: Timestamp for payout validation
                }
              })
              
              // Save to IndexedDB
              await localStore.importCollectedWords(learnerId, collectedWords)
              
              // Update Zustand if active learner
              if (freshState.activeLearner?.id === learnerId) {
                store.setCollectedWords(collectedWords)
                
                // Update learnerCache snapshot
                const currentCache = freshState.learnerCache[learnerId]
                if (currentCache) {
                  store.setState((s) => ({
                    learnerCache: {
                      ...s.learnerCache,
                      [learnerId]: {
                        ...currentCache,
                        collectedWords: collectedWords,
                      }
                    }
                  }), false, 'downloadProgress:updateCache')
                }
              }
            }

            // Invalidate cached blocks (they need to be rebuilt with new status)
            try {
              await localStore.deleteCache(getLearnerMineBlocksKey(learnerId))
              if (process.env.NODE_ENV === 'development') {
                console.log(`🗑️ Invalidated mine blocks cache for learner ${learnerId} (progress updated)`)
              }
            } catch (err) {
              console.warn('Failed to invalidate mine blocks cache:', err)
            }

            if (process.env.NODE_ENV === 'development') {
              console.log(
                `✅ Updated emojiProgress store after sync: ${emojiProgressMap.size} items, emojiSRSLevels: ${emojiSRSMap.size} items for learner ${learnerId}`,
              )
            }
          } else {
            if (process.env.NODE_ENV === 'development') {
              const store = useAppStore.getState()
              console.log(
                `⏭️ Skipping emojiProgress update: conditions not met`,
                {
                  activePack: store.activePack?.id,
                  activeLearnerId: store.activeLearner?.id,
                  targetLearnerId: learnerId,
                }
              )
            }
          }
        } catch (storeErr) {
          if (process.env.NODE_ENV === 'development') {
            console.debug('Could not update Zustand store after progress sync:', storeErr)
          }
        }

        if (process.env.NODE_ENV === 'development') {
          console.log(`📥 Synced ${data.progress.length} items for learner ${learnerId} (may be 0 for fresh learners)`)
        }
      }
    } catch (error) {
      // Network or backend failure: do NOT touch IndexedDB.
      // This preserves Last War offline guarantees (show last known data).
      console.debug(`Failed to download progress for learner ${learnerId}:`, error)
      throw error
    }
  }

  /**
   * Sync progress for a specific learner (public method for switching learners)
   * 
   * @param learnerId The learner ID to sync progress for (required)
   */
  async syncProgress(learnerId: string): Promise<void> {
    if (!learnerId) {
      console.warn('⚠️ syncProgress called without learnerId - skipping')
      return
    }
    await this.downloadProgress(learnerId)
  }

  /**
   * Get cached data (for instant page loads)
   */
  async getCached<T>(key: string): Promise<T | undefined> {
    return localStore.getCache<T>(key)
  }

  /**
   * Get user profile from cache, with API fallback
   * 
   * "Last War" pattern: Try cache first, fall back to API if empty.
   * This ensures Bootstrap always gets data even on first login.
   */
  async getProfile(): Promise<UserProfile | undefined> {
    // Try cache first
    const cached = await this.getCached<UserProfile>(CACHE_KEYS.PROFILE)
    if (cached) {
      return cached
    }
    
    // Cache miss - fetch from API and cache it
    console.log('📡 Profile not in cache, fetching from API...')
    try {
      const profile = await authenticatedGet<UserProfile>('/api/users/me')
      if (profile) {
        await localStore.setCache(CACHE_KEYS.PROFILE, profile, CACHE_TTL.MEDIUM)
        console.log('✅ Profile fetched and cached')
      }
      return profile
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Failed to fetch profile:', error)
      }
      return undefined
    }
  }

  /**
   * Get children from cache, with API fallback
   */
  async getLearners(): Promise<LearnerProfile[] | undefined> {
    // Tier 2: Try cache first (non-expired)
    const cached = await this.getCached<LearnerProfile[]>(CACHE_KEYS.LEARNERS)
    if (cached) {
      return cached
    }
    
    // Tier 3: Fetch from API with timeout (10s)
    console.log('📡 Learners not in cache, fetching from API...')
    try {
      const learners = await Promise.race([
        authenticatedGet<LearnerProfile[]>('/api/users/me/learners'),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('timeout of 10000ms exceeded')), 10000)
        )
      ])
      
      if (learners && learners.length > 0) {
        await localStore.setCache(CACHE_KEYS.LEARNERS, learners, CACHE_TTL.MEDIUM)
        console.log(`✅ ${learners.length} learners fetched and cached`)
      }
      return learners || []
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Failed to fetch learners (API timeout or error):', error)
      }
      
      // FALLBACK: Try expired cache (even if expired, use real data)
      try {
        const expiredCache = await localStore.getCacheIgnoreExpiry<LearnerProfile[]>(CACHE_KEYS.LEARNERS)
        if (expiredCache && expiredCache.length > 0) {
          console.log(`⚠️ Using expired cache for learners (${expiredCache.length} learners)`)
          // Re-cache it (refresh TTL) so it's available next time
          await localStore.setCache(CACHE_KEYS.LEARNERS, expiredCache, CACHE_TTL.MEDIUM)
          return expiredCache
        }
      } catch (cacheError) {
        // Ignore cache errors
      }
      
      return []
    }
  }

  /**
   * Force refresh learners from API, bypassing cache.
   * Use this after mutations (e.g., backfill, create child) to get fresh data.
   * 
   * Adds cache-busting query parameter to guarantee a network fetch.
   */
  async refreshLearners(): Promise<LearnerProfile[]> {
    console.log('🔄 Force refreshing learners from API (bypassing cache)...')
    try {
      // Add timestamp to URL to force fresh network request (bypasses Next.js/browser cache)
      const t = Date.now()
      const learners = await authenticatedGet<LearnerProfile[]>(`/api/users/me/learners?t=${t}`)
      
      if (!Array.isArray(learners)) {
        console.warn('⚠️ refreshLearners expected array, got:', typeof learners)
        return []
      }
      
      // Update cache with fresh data
      if (learners.length > 0) {
        await localStore.setCache(CACHE_KEYS.LEARNERS, learners, CACHE_TTL.MEDIUM)
        console.log(`✅ ${learners.length} learners refreshed and cached`)
      } else {
        // Clear cache if no learners returned (set to empty array)
        await localStore.setCache(CACHE_KEYS.LEARNERS, [], CACHE_TTL.MEDIUM)
        console.log('ℹ️ No learners returned, cache cleared')
      }
      
      return learners
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Failed to refresh learners:', error)
      }
      return []
    }
  }

  async getChildren(): Promise<Child[] | undefined> {
    // Try cache first
    const cached = await this.getCached<Child[]>(CACHE_KEYS.CHILDREN)
    if (cached) {
      return cached
    }
    
    // Cache miss - fetch from API and cache it
    console.log('📡 Children not in cache, fetching from API...')
    try {
      const children = await authenticatedGet<Child[]>('/api/users/me/children')
      if (children) {
        await localStore.setCache(CACHE_KEYS.CHILDREN, children, CACHE_TTL.MEDIUM)
        console.log(`✅ Children fetched and cached (${children.length} children)`)
      }
      return children
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Failed to fetch children:', error)
      }
      return []
    }
  }

  /**
   * Get learner profile from cache, with API fallback
   */
  async getLearnerProfile(): Promise<LearnerGamificationProfile | undefined> {
    // Try cache first
    const cached = await this.getCached<LearnerGamificationProfile>(CACHE_KEYS.LEARNER_PROFILE)
    if (cached) {
      return cached
    }
    
    // Cache miss - fetch from API and cache it
    console.log('📡 Learner profile not in cache, fetching from API...')
    try {
      const profile = await learnerProfileApi.getProfile()
      if (profile) {
        await localStore.setCache(CACHE_KEYS.LEARNER_PROFILE, profile, CACHE_TTL.SHORT)
        console.log('✅ Learner profile fetched and cached')
      }
      return profile
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Failed to fetch learner profile:', error)
      }
      return undefined
    }
  }

  /**
   * Get achievements from cache
   */
  async getAchievements(): Promise<Achievement[] | undefined> {
    return this.getCached<Achievement[]>(CACHE_KEYS.ACHIEVEMENTS)
  }

  /**
   * Get streaks from cache
   */
  async getStreaks(): Promise<StreakInfo | undefined> {
    return this.getCached<StreakInfo>(CACHE_KEYS.STREAKS)
  }

  /**
   * Get goals from cache
   */
  async getGoals(): Promise<Goal[] | undefined> {
    return this.getCached<Goal[]>(CACHE_KEYS.GOALS)
  }

  /**
   * Get notifications from cache
   */
  async getNotifications(): Promise<Notification[] | undefined> {
    return this.getCached<Notification[]>(CACHE_KEYS.NOTIFICATIONS)
  }

  /**
   * Get leaderboard from cache
   */
  async getLeaderboard(): Promise<LeaderboardEntry[] | undefined> {
    return this.getCached<LeaderboardEntry[]>(CACHE_KEYS.LEADERBOARD)
  }

  /**
   * Get due cards from cache
   */
  async getDueCards(): Promise<DueCard[] | undefined> {
    return this.getCached<DueCard[]>(CACHE_KEYS.DUE_CARDS)
  }

  /**
   * Get due cards for a specific learner (cache-first, learner-scoped)
   * 
   * @param learnerId - The learner ID to fetch due cards for
   * @param skipZustandUpdate - If true, skip updating Zustand store (for switchLearner() which handles its own updates)
   */
  async getLearnerDueCards(learnerId: string, skipZustandUpdate = false): Promise<DueCard[] | undefined> {
    if (!learnerId) {
      console.warn('⚠️ getLearnerDueCards called without learnerId - skipping')
      return []
    }

    const cacheKey = getLearnerDueCardsCacheKey(learnerId)

    // 1. Try learner-scoped cache first (offline-first, instant)
    const cached = await this.getCached<DueCard[]>(cacheKey)
    if (cached && cached.length > 0) {
      if (process.env.NODE_ENV === 'development') {
        console.log(`⚡ Loaded ${cached.length} due cards from cache for learner ${learnerId}`)
      }
      // Update Zustand store if this is the active learner (reactive background sync)
      // Skip if called from switchLearner() which handles its own update
      if (!skipZustandUpdate) {
        const { useAppStore } = await import('@/stores/useAppStore')
        const store = useAppStore.getState()
        if (store.activeLearner?.id === learnerId) {
          store.setDueCards(cached)
        }
      }
      return cached
    }

    // 2. Cache miss → fetch from API and cache (best effort)
    let cards: DueCard[] = []
    try {
      // Increased limit from 20 to 50 to avoid cutoff when user has many due cards
      const url = `/api/v1/verification/due?limit=50&learner_id=${learnerId}`
      cards = await authenticatedGet<DueCard[]>(url).catch(() => [])
      await localStore.setCache(cacheKey, cards, CACHE_TTL.SHORT)
      if (process.env.NODE_ENV === 'development') {
        console.log(`✅ Fetched and cached ${cards.length} due cards for learner ${learnerId}`)
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.debug('Failed to fetch learner due cards:', error)
      }
      return []
    }

    // Update Zustand store if this is the active learner (reactive background sync)
    // Skip if called from switchLearner() which handles its own update
    if (!skipZustandUpdate) {
      const { useAppStore } = await import('@/stores/useAppStore')
      const store = useAppStore.getState()
      if (store.activeLearner?.id === learnerId) {
        store.setDueCards(cards)
      }
    }

    return cards
  }

  /**
   * Force refresh due cards for a specific learner (network-first, learner-scoped)
   */
  async refreshLearnerDueCards(learnerId: string): Promise<DueCard[]> {
    if (!learnerId) {
      console.warn('⚠️ refreshLearnerDueCards called without learnerId - skipping')
      return []
    }

    const cacheKey = getLearnerDueCardsCacheKey(learnerId)

    let cards: DueCard[] = []
    try {
      // Increased limit from 20 to 50 to avoid cutoff when user has many due cards
      const url = `/api/v1/verification/due?limit=50&learner_id=${learnerId}`
      cards = await authenticatedGet<DueCard[]>(url).catch(() => [])
      await localStore.setCache(cacheKey, cards, CACHE_TTL.SHORT)
      if (process.env.NODE_ENV === 'development') {
        console.log(`🔄 Refreshed ${cards.length} due cards for learner ${learnerId}`)
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.debug('Failed to refresh learner due cards:', error)
      }
      // On failure, keep existing cache; caller can continue showing stale data
      return []
    }

    // Update Zustand store if this is the active learner (reactive background sync)
    const { useAppStore } = await import('@/stores/useAppStore')
    const store = useAppStore.getState()
    if (store.activeLearner?.id === learnerId) {
      store.setDueCards(cards)
    }

    return cards
  }

  /**
   * Get build state (currencies + rooms) for a specific learner.
   * 
   * MVP: Build state disabled – this is a no-op that always returns null.
   * The Build page is currently cosmetic-only and should not depend on
   * backend currencies/rooms.
   */
  async getBuildState(
    learnerId: string,
  ): Promise<{ currencies: any | null; rooms: any[] } | null> {
    if (!learnerId) {
      console.warn('⚠️ getBuildState called without learnerId - skipping')
      return null
    }

    if (process.env.NODE_ENV === 'development') {
      console.log('🧪 Build MVP: getBuildState no-op for', learnerId)
    }

    return null
  }

  /**
   * Sync build state (currencies + rooms) for a specific learner.
   * 
   * MVP: Build state disabled – this is a no-op that always returns null.
   * When the real economy is implemented, this can be re-enabled to
   * fetch and cache currencies/rooms per learner.
   */
  async syncBuildState(
    learnerId: string,
  ): Promise<{ currencies: any | null; rooms: any[] } | null> {
    if (!learnerId) {
      console.warn('⚠️ syncBuildState called without learnerId - skipping')
      return null
    }

    if (process.env.NODE_ENV === 'development') {
      console.log('🧪 Build MVP: syncBuildState no-op for', learnerId)
    }

    return null
  }

  /**
   * Get currencies from cache, with API fallback
   */
  async getCurrencies(): Promise<any | undefined> {
    const cached = await this.getCached<any>(CACHE_KEYS.CURRENCIES)
    if (cached) {
      console.log('⚡ Loaded currencies from cache')
      return cached
    }
    
    // Fetch from API
    try {
      const currencies = await authenticatedGet<any>('/api/v1/currencies')
      if (currencies) {
        await localStore.setCache(CACHE_KEYS.CURRENCIES, currencies, CACHE_TTL.SHORT)
        console.log('✅ Currencies fetched and cached')
      }
      return currencies
    } catch (error) {
      console.warn('⚠️ Failed to fetch currencies:', error)
      return undefined
    }
  }

  /**
   * Get rooms from cache, with API fallback
   */
  async getRooms(): Promise<any[] | undefined> {
    const cached = await this.getCached<any[]>(CACHE_KEYS.ROOMS)
    if (cached && cached.length > 0) {
      console.log(`⚡ Loaded ${cached.length} rooms from cache`)
      return cached
    }
    
    // Fetch from API
    try {
      const rooms = await authenticatedGet<any[]>('/api/v1/items/rooms')
      if (rooms) {
        await localStore.setCache(CACHE_KEYS.ROOMS, rooms, CACHE_TTL.MEDIUM)
        console.log(`✅ Rooms fetched and cached (${rooms.length} rooms)`)
      }
      return rooms
    } catch (error) {
      console.warn('⚠️ Failed to fetch rooms:', error)
      return undefined
    }
  }

  /**
   * Get children summaries from cache, with API fallback
   * 
   * NOTE: Always fetches from API if cache is empty, since empty array
   * could mean "API failed before" not "no children exist"
   */
  async getChildrenSummaries(): Promise<ChildSummary[] | undefined> {
    // Try cache first
    const cached = await this.getCached<ChildSummary[]>(CACHE_KEYS.CHILDREN_SUMMARIES)
    if (cached && cached.length > 0) {
      // Only trust cache if it has data
      console.log(`⚡ Loaded ${cached.length} children summaries from cache`)
      return cached
    }
    
    // Cache miss or empty - always fetch from API to get fresh data
    console.log('📡 Children summaries not in cache (or empty), fetching from API...')
    try {
      const summaries = await authenticatedGet<ChildSummary[]>('/api/users/me/children/summary')
      if (summaries) {
        await localStore.setCache(CACHE_KEYS.CHILDREN_SUMMARIES, summaries, CACHE_TTL.SHORT)
        console.log(`✅ Children summaries fetched and cached (${summaries.length} children)`)
      }
      return summaries
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Failed to fetch children summaries:', error)
      }
      return []
    }
  }

  /**
   * Check if we have cached data (for offline detection)
   */
  async hasCachedData(): Promise<boolean> {
    const profile = await this.getProfile()
    return !!profile
  }

  /**
   * Get last sync time
   */
  async getLastSyncTime(): Promise<number | undefined> {
    return localStore.get<number>(CACHE_KEYS.LAST_SYNC)
  }

  /**
   * Clear all cached data (for logout)
   */
  async clearAll(): Promise<void> {
    await localStore.clearAll()
    this.lastSyncTime = 0
  }
}

// Export singleton
export const downloadService = new DownloadService()

// Export cache keys for use by pages
export { CACHE_KEYS }

