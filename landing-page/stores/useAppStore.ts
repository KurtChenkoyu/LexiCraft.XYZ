/**
 * CACHING STRATEGY (IMMUTABLE - DO NOT CHANGE):
 * 
 * This file follows the "Last War" caching approach:
 * - Zustand holds the LIVE session state (in-memory)
 * - IndexedDB holds the PERSISTENT cache (offline)
 * - Components READ from Zustand (instant)
 * - Bootstrap loads from IndexedDB → Zustand at /start
 * 
 * See: .cursorrules - "Caching & Bootstrap Strategy"
 * 
 * DO NOT add localStorage usage for user data here.
 */

/**
 * App Store - Central state management using Zustand
 * 
 * The "Game Engine" state that enables instant rendering.
 * All components read from this store, never from API directly.
 * 
 * Data Flow:
 * 1. Bootstrap loads IndexedDB → Zustand at /start
 * 2. Components read from Zustand (instant, no spinners)
 * 3. Background sync updates IndexedDB → Zustand
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { shallow } from 'zustand/shallow'
import type { 
  LearnerProfile, 
  Achievement, 
  Goal, 
  Notification 
} from '@/services/gamificationApi'
import { localStore } from '@/lib/local-store'
import { progressApi } from '@/services/progressApi'

// Mining queue persistence key and TTL (30 days)
const MINING_QUEUE_CACHE_KEY = 'mining_queue'
const MINING_QUEUE_TTL = 30 * 24 * 60 * 60 * 1000

// ============================================
// Delta Strategy Types
// ============================================

/**
 * ActionDelta - Standardized response for all high-frequency actions.
 * Backend returns "what changed", frontend applies it instantly.
 * 
 * This enables the "Video Game" feel:
 * 1. User acts → UI updates instantly (frontend math)
 * 2. Backend confirms → Reconcile if needed (rare)
 * 3. Periodic full sync → Correct any drift
 */
export interface ActionDelta {
  // XP changes
  delta_xp?: number           // e.g., +10 for correct answer
  delta_level?: number        // e.g., +1 for level up
  
  // Currency changes (Three-Currency System)
  delta_sparks?: number       // e.g., +5 for fast answer
  delta_essence?: number      // e.g., +1 for perfect score
  delta_energy?: number       // e.g., -1 for mining action
  delta_blocks?: number       // e.g., +1 for completing word
  
  // Points (wallet balance)
  delta_points?: number       // e.g., +$2 for correct MCQ
  
  // Progress changes
  delta_discovered?: number   // e.g., +1 for new word
  delta_solid?: number        // e.g., +1 for mastered word
  delta_hollow?: number       // e.g., +1 for in-progress word
  
  // Streak
  streak_extended?: boolean
  new_streak_days?: number
  
  // Special events (trigger UI effects)
  achievements_unlocked?: string[]  // Achievement IDs to show toast
  level_up_to?: number              // New level (triggers celebration)
}

// ============================================
// Types
// ============================================

interface UserProfile {
  id: string
  email: string
  name: string | null
  age: number | null
  roles: string[]
  email_confirmed: boolean
}

// Mining Queue Types
export interface QueuedSense {
  senseId: string
  word: string
  addedAt: number
}

interface Child {
  id: string
  name: string | null
  age: number | null
  email: string
}

export interface ChildSummary {
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

interface ProgressStats {
  total_discovered: number
  solid_count: number
  hollow_count: number
  raw_count: number
}

interface VocabularyWord {
  sense_id: string
  word: string
  definition: string
  tier: number
  status?: 'raw' | 'hollow' | 'solid'
}

// ============================================
// Store State
// ============================================

interface AppState {
  // User Data
  user: UserProfile | null
  children: Child[]
  childrenSummaries: ChildSummary[]
  selectedChildId: string | null
  
  // Wallet
  balance: Balance
  
  // Learner Profile (Gamification)
  learnerProfile: LearnerProfile | null
  achievements: Achievement[]
  goals: Goal[]
  notifications: Notification[]
  
  // Progress
  progress: ProgressStats
  vocabulary: VocabularyWord[]
  
  // Building Data (for Build page)
  currencies: any | null
  rooms: any[]
  
  // Mining Inventory (Phase 5)
  minedSenses: Set<string>
  
  // Mining Queue (for batch operations)
  miningQueue: QueuedSense[]
  
  // Word Detail Navigation
  wordDetailStack: Array<{ senseId: string; word: string }>
  
  // Mine Page State (persists across navigation)
  mineBlocks: any[] // Block data for Mine page
  mineDataLoaded: boolean // Whether Mine page has loaded data
  
  // Verification Page State (persists across navigation)
  dueCards: any[] // Due cards for verification
  
  // Leaderboard Page State (persists across navigation)
  leaderboardData: {
    entries: any[]
    userRank: any | null
    period: string
    metric: string
    timestamp: number
  } | null
  
  // Active Vocabulary Pack
  activePack: {
    id: string           // 'emoji_core'
    name: string         // 'Core Emoji'
    word_count: number
  } | null
  
  // Kid Mode (Parent's device, child using)
  kidMode: {
    active: boolean
    childId: string | null
    childName: string | null
    enteredAt: number | null  // Timestamp, for session tracking
  }
  
  // Loading States
  isBootstrapped: boolean
  isSyncing: boolean
  
  // Bootstrap Error
  bootstrapError: string | null
  
  // Actions
  setUser: (user: UserProfile | null) => void
  setChildren: (children: Child[]) => void
  setChildrenSummaries: (summaries: ChildSummary[]) => void
  setSelectedChild: (childId: string | null) => void
  setBalance: (balance: Balance) => void
  setLearnerProfile: (profile: LearnerProfile | null) => void
  setAchievements: (achievements: Achievement[]) => void
  setGoals: (goals: Goal[]) => void
  setNotifications: (notifications: Notification[]) => void
  setProgress: (progress: ProgressStats) => void
  setVocabulary: (vocabulary: VocabularyWord[]) => void
  setCurrencies: (currencies: any | null) => void
  setRooms: (rooms: any[]) => void
  setBootstrapped: (value: boolean) => void
  setIsSyncing: (value: boolean) => void
  setBootstrapError: (error: string | null) => void
  
  // Batch Updates
  updateWallet: (delta: number) => void
  updateProgress: (updates: Partial<ProgressStats>) => void
  markNotificationAsRead: (notificationId: string) => void
  
  // Delta Strategy: Apply backend deltas to local state (instant)
  applyDelta: (delta: ActionDelta) => void
  
  // Mining Actions (Phase 5)
  mineSenses: (senseIds: string[]) => void
  isSenseMined: (senseId: string) => boolean
  
  // Mining Queue Actions
  addToQueue: (senseId: string, word: string) => void
  removeFromQueue: (senseId: string) => void
  clearQueue: () => void
  isInQueue: (senseId: string) => boolean
  mineAllQueued: () => void
  hydrateMiningQueue: () => Promise<void>
  
  // Word Detail Navigation Actions
  pushWordDetail: (senseId: string, word: string) => void
  popWordDetail: () => { senseId: string; word: string } | null
  clearWordDetailStack: () => void
  
  // Mine Page Actions
  setMineBlocks: (blocks: any[]) => void
  setMineDataLoaded: (loaded: boolean) => void
  
  // Verification Page Actions
  setDueCards: (cards: any[]) => void
  
  // Leaderboard Page Actions
  setLeaderboardData: (data: { entries: any[], userRank: any | null, period: string, metric: string }) => void
  setActivePack: (pack: { id: string, name: string, word_count: number } | null) => void
  
  // Kid Mode Actions
  enterKidMode: (childId: string, childName: string) => void
  exitKidMode: () => void
  isKidModeActive: () => boolean
  
  // Reset
  reset: () => void
}

// ============================================
// Default Values
// ============================================

const defaultBalance: Balance = {
  total_earned: 0,
  available_points: 0,
  locked_points: 0,
  withdrawn_points: 0,
}

const defaultProgress: ProgressStats = {
  total_discovered: 0,
  solid_count: 0,
  hollow_count: 0,
  raw_count: 0,
}

// ============================================
// Store
// ============================================

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial State
      user: null,
      children: [],
      childrenSummaries: [],
      selectedChildId: null,
      balance: defaultBalance,
      learnerProfile: null,
      achievements: [],
      goals: [],
      notifications: [],
      progress: defaultProgress,
      vocabulary: [],
      currencies: null,
      rooms: [],
      minedSenses: new Set(),
      miningQueue: [],
      wordDetailStack: [],
      mineBlocks: [],
      mineDataLoaded: false,
      dueCards: [],
      leaderboardData: null,
      activePack: { id: 'emoji_core', name: 'Core Emoji', word_count: 200 }, // Default pack
      kidMode: {
        active: false,
        childId: null,
        childName: null,
        enteredAt: null,
      },
      isBootstrapped: false,
      isSyncing: false,
      bootstrapError: null,

      // Actions
      setUser: (user) => set({ user }, false, 'setUser'),
      
      setChildren: (children) => set({ children }, false, 'setChildren'),
      
      setChildrenSummaries: (summaries) => set({ childrenSummaries: summaries }, false, 'setChildrenSummaries'),
      
      setSelectedChild: (childId) => set({ selectedChildId: childId }, false, 'setSelectedChild'),
      
      setBalance: (balance) => set({ balance }, false, 'setBalance'),
      
      setLearnerProfile: (profile) => set({ learnerProfile: profile }, false, 'setLearnerProfile'),
      
      setAchievements: (achievements) => set({ achievements }, false, 'setAchievements'),
      
      setGoals: (goals) => set({ goals }, false, 'setGoals'),
      
      setNotifications: (notifications) => set({ notifications }, false, 'setNotifications'),
      
      setProgress: (progress) => set({ progress }, false, 'setProgress'),
      
      setVocabulary: (vocabulary) => set({ vocabulary }, false, 'setVocabulary'),
      
      setCurrencies: (currencies) => set({ currencies }, false, 'setCurrencies'),
      
      setRooms: (rooms) => set({ rooms }, false, 'setRooms'),
      
      setMineBlocks: (blocks) => set({ mineBlocks: blocks }, false, 'setMineBlocks'),
      
      setMineDataLoaded: (loaded) => set({ mineDataLoaded: loaded }, false, 'setMineDataLoaded'),
      
      setDueCards: (cards) => set({ dueCards: cards }, false, 'setDueCards'),
      
      setLeaderboardData: (data) => set({ 
        leaderboardData: { ...data, timestamp: Date.now() } 
      }, false, 'setLeaderboardData'),
      
      setActivePack: (pack) => set({ activePack: pack }, false, 'setActivePack'),
      
      // Kid Mode Actions
      enterKidMode: (childId, childName) => set({
        kidMode: {
          active: true,
          childId,
          childName,
          enteredAt: Date.now(),
        }
      }, false, 'enterKidMode'),
      
      exitKidMode: () => set({
        kidMode: {
          active: false,
          childId: null,
          childName: null,
          enteredAt: null,
        }
      }, false, 'exitKidMode'),
      
      isKidModeActive: () => get().kidMode.active,
      
      setBootstrapped: (value) => set({ isBootstrapped: value }, false, 'setBootstrapped'),
      
      setIsSyncing: (value) => set({ isSyncing: value }, false, 'setIsSyncing'),
      
      setBootstrapError: (error) => set({ bootstrapError: error }, false, 'setBootstrapError'),

      // Batch Updates
      updateWallet: (delta) =>
        set(
          (state) => ({
            balance: {
              ...state.balance,
              available_points: state.balance.available_points + delta,
              total_earned: state.balance.total_earned + (delta > 0 ? delta : 0),
            },
          }),
          false,
          'updateWallet'
        ),

      updateProgress: (updates) =>
        set(
          (state) => ({
            progress: {
              ...state.progress,
              ...updates,
            },
          }),
          false,
          'updateProgress'
        ),

      markNotificationAsRead: (notificationId) =>
        set(
          (state) => ({
            notifications: state.notifications.map((n) =>
              n.id === notificationId ? { ...n, read: true } : n
            ),
          }),
          false,
          'markNotificationAsRead'
        ),

      // Delta Strategy: Apply backend deltas to local state (instant)
      // This is the "Video Game" pattern - update UI immediately with math
      applyDelta: (delta) =>
        set(
          (state) => {
            const updates: Partial<AppState> = {}
            
            // Update learner profile (XP, level, currencies)
            if (state.learnerProfile && (
              delta.delta_xp || delta.delta_sparks || delta.delta_essence || 
              delta.delta_energy || delta.delta_blocks || delta.level_up_to
            )) {
              const profile = { ...state.learnerProfile }
              
              // XP
              if (delta.delta_xp) {
                profile.level = {
                  ...profile.level,
                  total_xp: (profile.level.total_xp || 0) + delta.delta_xp,
                }
              }
              
              // Level up (recalculate level info)
              if (delta.level_up_to) {
                profile.level = {
                  ...profile.level,
                  level: delta.level_up_to,
                }
              }
              
              // Currencies
              if (profile.currencies) {
                if (delta.delta_sparks) {
                  profile.currencies.sparks = (profile.currencies.sparks || 0) + delta.delta_sparks
                }
                if (delta.delta_essence) {
                  profile.currencies.essence = (profile.currencies.essence || 0) + delta.delta_essence
                }
                if (delta.delta_energy) {
                  profile.currencies.energy = (profile.currencies.energy || 0) + delta.delta_energy
                }
                if (delta.delta_blocks) {
                  profile.currencies.blocks = (profile.currencies.blocks || 0) + delta.delta_blocks
                }
              }
              
              // Streak
              if (delta.new_streak_days !== undefined) {
                profile.streak = {
                  ...profile.streak,
                  current_streak: delta.new_streak_days,
                }
              }
              
              updates.learnerProfile = profile
            }
            
            // Update wallet balance (points)
            if (delta.delta_points) {
              updates.balance = {
                ...state.balance,
                available_points: state.balance.available_points + delta.delta_points,
                total_earned: state.balance.total_earned + delta.delta_points,
              }
            }
            
            // Update progress stats
            if (delta.delta_discovered || delta.delta_solid || delta.delta_hollow) {
              updates.progress = {
                ...state.progress,
                total_discovered: state.progress.total_discovered + (delta.delta_discovered || 0),
                solid_count: state.progress.solid_count + (delta.delta_solid || 0),
                hollow_count: state.progress.hollow_count + (delta.delta_hollow || 0),
              }
            }
            
            // Log for debugging
            console.log('🎮 applyDelta:', delta, '→', updates)
            
            return updates
          },
          false,
          'applyDelta'
        ),

      // Mining Actions (Phase 5)
      mineSenses: (senseIds) => {
        // 1. OPTIMISTIC UPDATE: Update UI immediately
        set(
          (state) => {
            const newMined = new Set(state.minedSenses)
            senseIds.forEach(id => newMined.add(id))
            
            // Optimistic: Add XP/currency (10 XP per word)
            const xpGained = senseIds.length * 10
            const newBalance: Balance = {
              ...state.balance,
              available_points: state.balance.available_points + xpGained,
              total_earned: state.balance.total_earned + xpGained,
              locked_points: state.balance.locked_points,
              withdrawn_points: state.balance.withdrawn_points,
            }
            
            return { 
              minedSenses: newMined, 
              balance: newBalance 
            } as Partial<AppState>
          },
          false,
          'mineSenses'
        )
        
        // 2. BACKGROUND SYNC: Persist to backend (fire-and-forget)
        import('@/services/gameService').then(({ gameService }) => {
          gameService.mineBatch(senseIds, 1)
            .then((result) => {
              console.log(`✅ Mining persisted: ${result.mined_count} new, ${result.skipped_count} skipped`)
              // Reconcile wallet balance with server truth
              set({ balance: result.new_wallet_balance }, false, 'reconcileWallet')
            })
            .catch((error) => {
              console.error('⚠️ Mining persistence failed:', error)
              // TODO: Show toast notification to user
              // For now, log only - eventual consistency
            })
        })
      },

      isSenseMined: (senseId: string): boolean => {
        const state = useAppStore.getState()
        return state.minedSenses.has(senseId)
      },

      // Mining Queue Actions (with IndexedDB persistence + Backend Smelting)
      addToQueue: (senseId, word) => {
        set(
          (state) => {
            // Don't add if already in queue
            if (state.miningQueue.some(q => q.senseId === senseId)) {
              return state
            }
            const newQueue = [
              ...state.miningQueue,
              { senseId, word, addedAt: Date.now() }
            ]
            // Persist to IndexedDB (fire and forget)
            localStore.setCache(MINING_QUEUE_CACHE_KEY, newQueue, MINING_QUEUE_TTL)
              .catch(err => console.warn('Failed to persist mining queue:', err))
            return { miningQueue: newQueue }
          },
          false,
          'addToQueue'
        )
        
        // 🔥 BACKEND: Start forging (smelting) the word so it enters SRS
        // This makes the word appear in verification page when due
        progressApi.startForging(senseId)
          .then((result) => {
            console.log(`⚒️ Started smelting "${word}":`, result.message)
            // Delta Strategy: Apply XP/progress from backend
            if (result.delta_xp || result.delta_sparks || result.delta_discovered) {
              useAppStore.getState().applyDelta({
                delta_xp: result.delta_xp,
                delta_sparks: result.delta_sparks,
                delta_discovered: result.delta_discovered,
                delta_hollow: result.delta_hollow,
              })
            }
          })
          .catch((err) => {
            // Don't fail loudly - word is still queued locally
            console.warn(`Failed to start smelting "${word}":`, err)
          })
      },

      removeFromQueue: (senseId) => {
        set(
          (state) => {
            const newQueue = state.miningQueue.filter(q => q.senseId !== senseId)
            // Persist to IndexedDB (fire and forget)
            localStore.setCache(MINING_QUEUE_CACHE_KEY, newQueue, MINING_QUEUE_TTL)
              .catch(err => console.warn('Failed to persist mining queue:', err))
            return { miningQueue: newQueue }
          },
          false,
          'removeFromQueue'
        )
      },

      clearQueue: () => {
        set({ miningQueue: [] }, false, 'clearQueue')
        // Persist empty queue to IndexedDB
        localStore.setCache(MINING_QUEUE_CACHE_KEY, [], MINING_QUEUE_TTL)
          .catch(err => console.warn('Failed to persist mining queue:', err))
      },

      isInQueue: (senseId: string): boolean => {
        const state = useAppStore.getState()
        return state.miningQueue.some(q => q.senseId === senseId)
      },

      mineAllQueued: () => {
        const state = useAppStore.getState()
        const senseIds = state.miningQueue.map(q => q.senseId)
        if (senseIds.length > 0) {
          state.mineSenses(senseIds)
          set({ miningQueue: [] }, false, 'mineAllQueued:clearQueue')
          // Persist empty queue to IndexedDB
          localStore.setCache(MINING_QUEUE_CACHE_KEY, [], MINING_QUEUE_TTL)
            .catch(err => console.warn('Failed to persist mining queue:', err))
        }
      },

      hydrateMiningQueue: async () => {
        try {
          // First, try to sync from backend progress (source of truth)
          try {
            const { progressApi } = await import('@/services/progressApi')
            const backendProgress = await progressApi.getUserProgress()
            
            if (backendProgress?.progress && backendProgress.progress.length > 0) {
              // Save ALL progress to IndexedDB for the Mine page to use
              for (const p of backendProgress.progress) {
                let status: 'raw' | 'hollow' | 'solid' = 'raw'
                if (p.status === 'verified' || p.status === 'mastered' || p.status === 'solid') {
                  status = 'solid'
                } else if (p.status === 'pending' || p.status === 'learning' || p.status === 'hollow') {
                  status = 'hollow'
                }
                await localStore.saveProgress(p.sense_id, status, {
                  tier: p.tier,
                  startedAt: p.started_at,
                  masteryLevel: p.mastery_level,
                })
              }
              console.log(`💾 Saved ${backendProgress.progress.length} progress items to IndexedDB`)
              
              // Filter for items that are "hollow" (pending/learning) for the queue
              const hollowItems = backendProgress.progress.filter((p: any) => 
                p.status === 'pending' || p.status === 'learning' || p.status === 'hollow'
              )
              
              if (hollowItems.length > 0) {
                // Convert to queue format
                const queueFromBackend: QueuedSense[] = hollowItems.map((p: any) => ({
                  senseId: p.sense_id,
                  word: p.word || p.sense_id.split('.')[0], // fallback to sense_id prefix
                  addedAt: Date.now(),
                }))
                
                // Update local queue to match backend
                set({ miningQueue: queueFromBackend }, false, 'hydrateMiningQueue:fromBackend')
                localStore.setCache(MINING_QUEUE_CACHE_KEY, queueFromBackend, MINING_QUEUE_TTL)
                  .catch(err => console.warn('Failed to persist mining queue:', err))
                console.log(`⛏️ Synced mining queue from backend: ${queueFromBackend.length} items`)
                return
              }
            }
          } catch (backendErr) {
            console.warn('Failed to sync mining queue from backend, falling back to local cache:', backendErr)
          }
          
          // Fallback: Try local IndexedDB cache
          const cached = await localStore.getCache<QueuedSense[]>(MINING_QUEUE_CACHE_KEY)
          if (cached && cached.length > 0) {
            set({ miningQueue: cached }, false, 'hydrateMiningQueue:fromCache')
            console.log(`⛏️ Hydrated mining queue from cache: ${cached.length} items`)
          }
        } catch (err) {
          console.warn('Failed to hydrate mining queue:', err)
        }
      },

      // Word Detail Navigation Actions
      pushWordDetail: (senseId, word) =>
        set(
          (state) => ({
            wordDetailStack: [...state.wordDetailStack, { senseId, word }]
          }),
          false,
          'pushWordDetail'
        ),

      popWordDetail: (): { senseId: string; word: string } | null => {
        const state = useAppStore.getState()
        if (state.wordDetailStack.length <= 1) {
          return null
        }
        // Remove current, return previous
        const newStack = state.wordDetailStack.slice(0, -1)
        const previous = newStack[newStack.length - 1] || null
        set({ wordDetailStack: newStack }, false, 'popWordDetail')
        return previous
      },

      clearWordDetailStack: () =>
        set({ wordDetailStack: [] }, false, 'clearWordDetailStack'),

      // Reset (for logout)
      reset: () =>
        set(
          {
            user: null,
            children: [],
            childrenSummaries: [],
            selectedChildId: null,
            balance: defaultBalance,
            learnerProfile: null,
            achievements: [],
            goals: [],
            notifications: [],
            progress: defaultProgress,
            vocabulary: [],
            currencies: null,
            rooms: [],
            minedSenses: new Set(),
            miningQueue: [],
            wordDetailStack: [],
            mineBlocks: [],
            mineDataLoaded: false,
            dueCards: [],
            leaderboardData: null,
            activePack: { id: 'emoji_core', name: 'Core Emoji', word_count: 200 },
            kidMode: {
              active: false,
              childId: null,
              childName: null,
              enteredAt: null,
            },
            isBootstrapped: false,
            isSyncing: false,
            bootstrapError: null,
          },
          false,
          'reset'
        ),
    }),
    {
      name: 'AppStore',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
)

// ============================================
// Selectors (for optimized re-renders)
// ============================================

export const selectUser = (state: AppState) => state.user
export const selectChildren = (state: AppState) => state.children
export const selectChildrenSummaries = (state: AppState) => state.childrenSummaries
export const selectSelectedChild = (state: AppState) => 
  state.children.find(c => c.id === state.selectedChildId)
export const selectBalance = (state: AppState) => state.balance
export const selectLearnerProfile = (state: AppState) => state.learnerProfile
export const selectAchievements = (state: AppState) => state.achievements
export const selectUnlockedAchievements = (state: AppState) => 
  state.achievements.filter(a => a.unlocked_at !== null)
export const selectGoals = (state: AppState) => state.goals
export const selectActiveGoals = (state: AppState) => 
  state.goals.filter(g => g.status === 'active')
export const selectNotifications = (state: AppState) => state.notifications
export const selectUnreadNotifications = (state: AppState) => 
  state.notifications.filter(n => !n.read)
// FIXED: Selector that returns count (primitive) instead of array to avoid infinite loops
export const selectUnreadNotificationsCount = (state: AppState): number => 
  state.notifications.filter(n => !n.read).length
export const selectProgress = (state: AppState) => state.progress
export const selectVocabulary = (state: AppState) => state.vocabulary
export const selectIsBootstrapped = (state: AppState) => state.isBootstrapped
export const selectIsSyncing = (state: AppState) => state.isSyncing
export const selectBootstrapError = (state: AppState) => state.bootstrapError

// Mining Queue Selectors
export const selectMiningQueue = (state: AppState) => state.miningQueue
export const selectMiningQueueCount = (state: AppState): number => state.miningQueue.length
export const selectWordDetailStack = (state: AppState) => state.wordDetailStack
export const selectCurrentWordDetail = (state: AppState) => 
  state.wordDetailStack[state.wordDetailStack.length - 1] || null
export const selectCanGoBack = (state: AppState): boolean => state.wordDetailStack.length > 1
export const selectMineBlocks = (state: AppState) => state.mineBlocks
export const selectMineDataLoaded = (state: AppState) => state.mineDataLoaded

// Verification selectors
export const selectDueCards = (state: AppState) => state.dueCards

// Leaderboard selectors
export const selectLeaderboardData = (state: AppState) => state.leaderboardData
export const selectActivePack = (state: AppState) => state.activePack

// Kid Mode Selectors
export const selectKidMode = (state: AppState) => state.kidMode
export const selectIsKidModeActive = (state: AppState) => state.kidMode.active
export const selectKidModeChildId = (state: AppState) => state.kidMode.childId
export const selectKidModeChildName = (state: AppState) => state.kidMode.childName

// ============================================
// Derived Selectors (Computed from State)
// ============================================

/**
 * Compute onboarding status from user profile (no API call!)
 * Onboarding is complete if user has age AND roles.
 * 
 * ⚡ INSTANT: <1ms, no network, works offline
 * Following "Last War" caching strategy
 */
export const selectOnboardingStatus = (state: AppState) => {
  const user = state.user
  if (!user) {
    return { completed: false, missing: ['user'], ready: false, roles: [] }
  }
  
  const missing: string[] = []
  if (!user.age) missing.push('age')
  if (!user.roles || user.roles.length === 0) missing.push('roles')
  
  return {
    completed: missing.length === 0,
    missing,
    ready: true, // We have user data to check
    roles: user.roles || []
  }
}

