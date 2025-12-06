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
  BALANCE: 'balance',
  PROGRESS: 'learning_progress',
  LEADERBOARD: 'leaderboard',
  DUE_CARDS: 'due_cards',
  LAST_SYNC: 'last_full_sync',
}

// Cache TTLs (in ms)
const CACHE_TTL = {
  SHORT: 5 * 60 * 1000,       // 5 minutes - frequently changing data
  MEDIUM: 30 * 60 * 1000,     // 30 minutes - moderately stable
  LONG: 24 * 60 * 60 * 1000,  // 24 hours - rarely changing
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
    await localStore.set(CACHE_KEYS.LAST_SYNC, Date.now())

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
   * Get user profile from cache
   */
  async getProfile(): Promise<UserProfile | undefined> {
    return this.getCached<UserProfile>(CACHE_KEYS.PROFILE)
  }

  /**
   * Get children from cache
   */
  async getChildren(): Promise<Child[] | undefined> {
    return this.getCached<Child[]>(CACHE_KEYS.CHILDREN)
  }

  /**
   * Get learner profile from cache
   */
  async getLearnerProfile(): Promise<LearnerProfile | undefined> {
    return this.getCached<LearnerProfile>(CACHE_KEYS.LEARNER_PROFILE)
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

