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
  LearnerProfile,
  Achievement,
  StreakInfo,
  Goal,
  Notification,
  LeaderboardEntry,
} from '@/services/gamificationApi'

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
  BALANCE: 'balance',
  PROGRESS: 'learning_progress',
  LEADERBOARD: 'leaderboard',
  DUE_CARDS: 'due_cards',
  CURRENCIES: 'currencies',
  ROOMS: 'rooms',
  LAST_SYNC: 'last_full_sync',
}

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
  words_learned_today: number
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

    // Run all downloads in parallel with error handling
    const downloadTasks = [
      // 1. User Profile
      this.downloadWithCache(
        CACHE_KEYS.PROFILE,
        () => authenticatedGet<UserProfile>('/api/users/me'),
        CACHE_TTL.MEDIUM
      ).then(() => updateProgress('profile'))
        .catch(e => updateProgress('profile', `Profile: ${e.message}`)),

      // 2. Children
      this.downloadWithCache(
        CACHE_KEYS.CHILDREN,
        () => authenticatedGet<Child[]>('/api/users/me/children').catch(() => []),
        CACHE_TTL.MEDIUM
      ).then(() => updateProgress('children'))
        .catch(e => updateProgress('children', `Children: ${e.message}`)),

      // 3. Learner Profile (gamification)
      this.downloadWithCache(
        CACHE_KEYS.LEARNER_PROFILE,
        () => learnerProfileApi.getProfile(),
        CACHE_TTL.SHORT
      ).then(() => updateProgress('learnerProfile'))
        .catch(e => updateProgress('learnerProfile', `Learner Profile: ${e.message}`)),

      // 4. Achievements
      this.downloadWithCache(
        CACHE_KEYS.ACHIEVEMENTS,
        () => learnerProfileApi.getAchievements(),
        CACHE_TTL.MEDIUM
      ).then(() => updateProgress('achievements'))
        .catch(e => updateProgress('achievements', `Achievements: ${e.message}`)),

      // 5. Streaks
      this.downloadWithCache(
        CACHE_KEYS.STREAKS,
        () => learnerProfileApi.getStreaks(),
        CACHE_TTL.SHORT
      ).then(() => updateProgress('streaks'))
        .catch(e => updateProgress('streaks', `Streaks: ${e.message}`)),

      // 6. Goals
      this.downloadWithCache(
        CACHE_KEYS.GOALS,
        () => goalsApi.getGoals().catch(() => []),
        CACHE_TTL.MEDIUM
      ).then(() => updateProgress('goals'))
        .catch(e => updateProgress('goals', `Goals: ${e.message}`)),

      // 7. Notifications
      this.downloadWithCache(
        CACHE_KEYS.NOTIFICATIONS,
        () => notificationsApi.getNotifications(false, 50).catch(() => []),
        CACHE_TTL.SHORT
      ).then(() => updateProgress('notifications'))
        .catch(e => updateProgress('notifications', `Notifications: ${e.message}`)),

      // 8. Learning Progress
      this.downloadProgress().then(() => updateProgress('progress'))
        .catch(e => updateProgress('progress', `Progress: ${e.message}`)),

      // 9. Leaderboard (weekly XP - default view)
      this.downloadWithCache(
        CACHE_KEYS.LEADERBOARD,
        () => leaderboardsApi.getGlobal('weekly', 50, 'xp').catch(() => []),
        CACHE_TTL.SHORT
      ).then(() => updateProgress('leaderboard'))
        .catch(e => updateProgress('leaderboard', `Leaderboard: ${e.message}`)),

      // 10. Due Cards for verification
      this.downloadWithCache(
        CACHE_KEYS.DUE_CARDS,
        () => authenticatedGet<DueCard[]>('/api/v1/verification/due?limit=20').catch(() => []),
        CACHE_TTL.SHORT
      ).then(() => updateProgress('dueCards'))
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
   * Download learning progress and import into IndexedDB
   */
  private async downloadProgress(): Promise<void> {
    try {
      const data = await authenticatedGet<ProgressData>('/api/v1/mine/progress')
      
      if (data?.progress?.length > 0) {
        // Import into the progress store (separate from cache)
        await localStore.importProgress(data.progress)
        // Also cache the full response
        await localStore.setCache(CACHE_KEYS.PROGRESS, data, CACHE_TTL.SHORT)
      }
    } catch (error) {
      console.debug('Failed to download progress:', error)
      throw error
    }
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
  async getChildren(): Promise<Child[] | undefined> {
    // Try cache first
    const cached = await this.getCached<Child[]>(CACHE_KEYS.CHILDREN)
    if (cached) {
      return cached
    }
    
    // Cache miss - fetch from API and cache it
    console.log('📡 Children not in cache, fetching from API...')
    try {
      const children = await authenticatedGet<Child[]>('/api/users/children')
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
  async getLearnerProfile(): Promise<LearnerProfile | undefined> {
    // Try cache first
    const cached = await this.getCached<LearnerProfile>(CACHE_KEYS.LEARNER_PROFILE)
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

