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
  LearnerGamificationProfile, 
  Achievement, 
  Goal, 
  Notification 
} from '@/services/gamificationApi'
import { localStore } from '@/lib/local-store'
import { progressApi } from '@/services/progressApi'
import type { PackVocabularyItem } from '@/lib/pack-types'

// Mining queue persistence key and TTL (30 days)
// CRITICAL: Must be learner-scoped to prevent data bleeding between learners
const getMiningQueueCacheKey = (learnerId: string) => `mining_queue_${learnerId}`
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

// Learner Profile (from learners table - new multi-profile system)
export interface LearnerProfile {
  id: string  // learner.id (UUID)
  user_id: string | null  // auth.users.id (NULL for children without accounts)
  guardian_id: string  // Parent's auth.users.id
  display_name: string
  avatar_emoji: string
  age_group: string | null
  is_parent_profile: boolean
  is_independent: boolean
  settings: Record<string, any>
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

export interface LearnerSummary {
  learner_id: string
  display_name: string
  avatar_emoji: string
  is_parent_profile: boolean
  // Summary stats (learner-scoped)
  level: number
  total_xp: number
  current_streak: number
  vocabulary_size: number
  words_in_progress: number  // Words with status 'hollow', 'learning', 'pending'
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

// Learner State Cache (in-memory snapshots for instant switching between learners)
type LearnerStateCache = {
  [learnerId: string]: {
    miningQueue: QueuedSense[]
    emojiProgress: Map<string, string>  // Always a Map (never null) for consistent pipeline
    emojiSRSLevels: Map<string, string>  // Always a Map (never null) for consistent pipeline
    progress: ProgressStats
    dueCards: any[]               // Cached verification list (SRS due cards)
    collectedWords: CollectedWord[]  // Per-learner inventory
    currencies?: any | null       // Cached build currencies for this learner (not used in emoji MVP)
    rooms?: any[]                 // Cached build rooms/items for this learner (not used in emoji MVP)
    timestamp: number             // Last update time (for optional pruning / debugging)
  }
}

interface VocabularyWord {
  sense_id: string
  word: string
  definition: string
  rank: number  // Renamed from tier to rank (word complexity 1-7)
  status?: 'raw' | 'hollow' | 'solid'
}

// Collected Word (Game-like inventory item)
// Extends PackVocabularyItem with collection metadata
export interface CollectedWord extends PackVocabularyItem {
  collectedAt: number        // Timestamp when word was first collected (CRITICAL for audit trail)
  masteredAt?: number       // Timestamp when word achieved "mastered" status (for payout validation)
  status: 'hollow' | 'solid' | 'mastered'  // Current status (never 'raw')
  masteryLevel: 'learning' | 'familiar' | 'known' | 'mastered' | 'burned'  // Current SRS level
  isArchived?: boolean       // Optional flag for suspended words
}

// ============================================
// Store State
// ============================================

interface AppState {
  // User Data
  user: UserProfile | null
  children: Child[]
  childrenSummaries: ChildSummary[]
  learnersSummaries: LearnerSummary[]  // NEW: Learner-scoped summaries (replaces childrenSummaries for leaderboard)
  selectedChildId: string | null
  
  // Learners (Multi-Profile System - NEW)
  learners: LearnerProfile[]  // All learner profiles (parent + children)
  activeLearner: LearnerProfile | null  // Currently active learner profile
  learnerCache: LearnerStateCache  // In-memory cache of per-learner state for instant switching
  
  // Wallet
  balance: Balance
  
  // Learner Profile (Gamification)
  learnerProfile: LearnerGamificationProfile | null
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
    emoji?: string       // Pack icon: '🎯'
  } | null
  
  // Emoji Pack Data (preloaded for instant rendering)
  emojiVocabulary: PackVocabularyItem[] | null  // All 200 words
  emojiProgress: Map<string, string> | null     // Progress filtered for emoji words (senseId -> status) - Runtime guards ensure never null when emoji pack is active
  emojiSRSLevels: Map<string, string> | null      // SRS mastery levels (senseId -> mastery_level: 'learning', 'familiar', 'known', 'mastered') - Runtime guards ensure never null when emoji pack is active
  emojiMasteredWords: PackVocabularyItem[] | null // Pre-filtered mastered words
  emojiStats: {
    totalWords: number
    collectedWords: number
    masteredWords: number
    learningWords: number
  } | null
  
  // Game-like Inventory (only collected words)
  collectedWords: CollectedWord[] | null
  
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
  setLearnersSummaries: (summaries: LearnerSummary[]) => void
  setSelectedChild: (childId: string | null) => void
  
  // Learners Actions (Multi-Profile System)
  setLearners: (learners: LearnerProfile[]) => void
  setActiveLearner: (learner: LearnerProfile | null) => void
  fetchLearners: () => Promise<void>  // Fetch learners from API
  switchLearner: (learnerId: string) => Promise<void>  // Switch and reload data
  setBalance: (balance: Balance) => void
  setLearnerProfile: (profile: LearnerGamificationProfile | null) => void
  setAchievements: (achievements: Achievement[]) => void
  setGoals: (goals: Goal[]) => void
  setNotifications: (notifications: Notification[]) => void
  setProgress: (progress: ProgressStats) => void
  setVocabulary: (vocabulary: VocabularyWord[]) => void
  setCurrencies: (currencies: any | null) => void
  setRooms: (rooms: any[]) => void
  setBuildState: (learnerId: string, currencies: any | null, rooms: any[]) => void
  setBuildState: (learnerId: string, currencies: any | null, rooms: any[]) => void
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
  
  // Verification Actions
  completeVerification: (results: Array<{ senseId: string, isCorrect: boolean }>) => void
  
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
  setActivePack: (pack: { id: string, name: string, word_count: number, emoji?: string } | null) => void

  // Emoji Pack Data Actions
  setEmojiVocabulary: (vocab: PackVocabularyItem[]) => void
  setEmojiProgress: (progress: Map<string, string> | null) => void  // Runtime guards ensure never null when emoji pack is active
  setEmojiSRSLevels: (levels: Map<string, string> | null) => void  // Runtime guards ensure never null when emoji pack is active
  setEmojiMasteredWords: (words: PackVocabularyItem[]) => void
  setEmojiStats: (stats: { totalWords: number; collectedWords: number; masteredWords: number; learningWords: number }) => void
  
  // Game-like Inventory Actions
  setCollectedWords: (words: CollectedWord[] | null) => void
  
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
    (set, get) => ({
      // Initial State
      user: null,
      children: [],
      childrenSummaries: [],
      learnersSummaries: [],
      selectedChildId: null,
      learners: [],
      activeLearner: null,
      learnerCache: {}, // In-memory learner state cache (per-learner snapshots)
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
      emojiVocabulary: null, // Preloaded emoji vocabulary
      emojiProgress: new Map<string, string>(), // Always a Map (never null) for consistent pipeline
      emojiSRSLevels: new Map<string, string>(), // Always a Map (never null) for consistent pipeline
      emojiMasteredWords: null, // Preloaded mastered words
      emojiStats: null, // Preloaded emoji stats
      collectedWords: null, // Game-like inventory (only collected words)
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
      
      setLearnersSummaries: (summaries) => set({ learnersSummaries: summaries }, false, 'setLearnersSummaries'),
      
      setSelectedChild: (childId) => set({ selectedChildId: childId }, false, 'setSelectedChild'),
      
      // Learners Actions
      setLearners: (learners) => set({ learners }, false, 'setLearners'),
      
      setActiveLearner: (learner) => set({ activeLearner: learner }, false, 'setActiveLearner'),
      
      fetchLearners: async () => {
        try {
          const { authenticatedGet } = await import('@/lib/api-client')
          const learners = await authenticatedGet<LearnerProfile[]>('/api/users/me/learners')
          
          if (learners && learners.length > 0) {
            set({ learners }, false, 'fetchLearners')
            
            // Auto-select parent if no active learner
            const state = get()
            if (!state.activeLearner) {
              const parent = learners.find(l => l.is_parent_profile)
              if (parent) {
                set({ activeLearner: parent }, false, 'fetchLearners:autoSelectParent')
              } else {
                // Fallback: use first learner
                set({ activeLearner: learners[0] }, false, 'fetchLearners:autoSelectFirst')
              }
            }
            
            console.log(`✅ Fetched ${learners.length} learners`)
          } else {
            set({ learners: [] }, false, 'fetchLearners:empty')
          }
        } catch (error) {
          console.error('Failed to fetch learners:', error)
          set({ learners: [] }, false, 'fetchLearners:error')
        }
      },
      
      switchLearner: async (learnerId) => {
        const state = get()
        const prevLearner = state.activeLearner
        const learner = state.learners.find(l => l.id === learnerId)
        if (!learner) {
          console.warn(`Learner ${learnerId} not found`)
          return
        }

        // Phase 0: SNAPSHOT - Save current learner's state into in-memory cache before switching
        if (prevLearner?.id && prevLearner.id !== learnerId) {
          const currentCache = {
            miningQueue: state.miningQueue,
            emojiProgress: state.emojiProgress || new Map<string, string>(), // Always a Map
            emojiSRSLevels: state.emojiSRSLevels || new Map<string, string>(), // Always a Map (not null)
            progress: state.progress,
            dueCards: state.dueCards || [],
            collectedWords: state.collectedWords || [],
            currencies: state.currencies,
            rooms: state.rooms,
            timestamp: Date.now(),
          }

          set(
            (s) => ({
              learnerCache: {
                ...s.learnerCache,
                [prevLearner.id]: currentCache,
              },
            }),
            false,
            'switchLearner:saveToCache',
          )
        }

        // Check if target learner has cached state in RAM
        const cachedData = state.learnerCache[learnerId]

        if (process.env.NODE_ENV === 'development') {
          console.log(
            `🔍 switchLearner: Checking cache for ${learner.display_name} (${learnerId})`,
            {
              hasCache: !!cachedData,
              cacheKeys: Object.keys(state.learnerCache),
              cachedEmojiProgressType: cachedData?.emojiProgress?.constructor?.name,
              cachedEmojiProgressSize: cachedData?.emojiProgress?.size,
              cachedEmojiSRSLevelsType: cachedData?.emojiSRSLevels?.constructor?.name,
              cachedEmojiSRSLevelsSize: cachedData?.emojiSRSLevels?.size,
            }
          )
        }

        if (cachedData) {
          // 🚀 FAST PATH: Restore learner state instantly from RAM (0ms)
          // Ensure Maps are always Maps (never null) for consistent pipeline
          // Note: We can use the same Map references from cache - components will react via activeLearner?.id dependency
          const restoredEmojiProgress = cachedData.emojiProgress || new Map<string, string>()
          const restoredEmojiSRSLevels = cachedData.emojiSRSLevels || new Map<string, string>()
          
          if (process.env.NODE_ENV === 'development') {
            console.log(
              `⚡ Instant-switch: Restoring learner ${learner.display_name} from RAM cache`,
              {
                emojiProgressSize: restoredEmojiProgress.size,
                emojiSRSLevelsSize: restoredEmojiSRSLevels.size,
                miningQueueLength: cachedData.miningQueue.length,
                restoredEmojiProgressType: restoredEmojiProgress.constructor.name,
                restoredEmojiSRSLevelsType: restoredEmojiSRSLevels.constructor.name,
              }
            )
          }
          
          set(
            {
              activeLearner: learner,
              miningQueue: cachedData.miningQueue,
              emojiProgress: restoredEmojiProgress, // Always a Map (new reference for React)
              emojiSRSLevels: restoredEmojiSRSLevels, // Always a Map (new reference for React)
              progress: cachedData.progress,
              currencies: cachedData.currencies ?? null,
              rooms: cachedData.rooms ?? [],
              mineBlocks: [],
              dueCards: cachedData.dueCards,
              collectedWords: cachedData.collectedWords || [],
            },
            false,
            'switchLearner:restoreFromCache',
          )

          console.log(
            `⚡ Instant-switch: Restored learner ${learner.display_name} from RAM cache with ${cachedData.miningQueue.length} queued items`,
          )
        } else {
          // Phase 1: Optimistic Update (instant UI) for first-time load
          set({ activeLearner: learner }, false, 'switchLearner:optimistic')

          // Phase 2: Cache-First Load (try IndexedDB first, ~10ms)
          // Clear learner-specific data that pages will reload
          // CRITICAL: Clear queue and emoji state to prevent data bleeding between learners
          set(
            {
              mineBlocks: [], // Reloaded by mine page
              dueCards: [], // Reloaded by verification page
              miningQueue: [], // Clear queue immediately (will reload below)
              emojiProgress: new Map<string, string>(), // Initialize as empty Map (will be populated below)
              emojiSRSLevels: new Map<string, string>(), // Initialize as empty Map (will be populated below)
              currencies: null, // Clear build currencies (will reload below)
              rooms: [], // Clear rooms (will reload below)
            },
            false,
            'switchLearner:clearLearnerSpecificData',
          )

          // Load due cards from IndexedDB cache (fast, ~10ms, cache-first)
          // This matches the pattern used for progress/emoji data
          // Load outside try block so it's available in catch block
          // Skip Zustand update - switchLearner() handles its own updates to avoid race conditions
          const { downloadService } = await import('@/services/downloadService')
          let cachedDueCards: any[] = []
          try {
            cachedDueCards = await downloadService.getLearnerDueCards(learnerId, true) || []
          } catch (dueCardsError) {
            // If due cards loading fails, continue with empty array
            if (process.env.NODE_ENV === 'development') {
              console.warn('Failed to load due cards from cache:', dueCardsError)
            }
          }

          // Load collectedWords from IndexedDB
          let cachedCollectedWords: import('@/stores/useAppStore').CollectedWord[] = []
          try {
            cachedCollectedWords = await localStore.getCollectedWords(learnerId)
          } catch (collectedWordsError) {
            if (process.env.NODE_ENV === 'development') {
              console.warn('Failed to load collectedWords from cache:', collectedWordsError)
            }
          }

          // Update Zustand store immediately (before processing progress)
          // This ensures verification page sees data instantly
          set(
            {
              dueCards: cachedDueCards,
              collectedWords: cachedCollectedWords,
            },
            false,
            'switchLearner:cacheDueCards',
          )

          try {
            // Load progress from IndexedDB cache (fast, learner-scoped)
            const cachedProgressMap = await localStore.getAllProgress(learnerId)

            // Update Zustand store immediately (before processing progress)
            // This ensures verification page sees data instantly
            set(
              {
                dueCards: cachedDueCards,
              },
              false,
              'switchLearner:cacheDueCards',
            )

            if (cachedProgressMap.size > 0) {
              // Cache found! Load and display immediately

              // Calculate progress stats from cache
              // Count mastered words (solid/mastered/verified)
              const solid = Array.from(cachedProgressMap.values()).filter(
                (s) => s === 'solid' || s === 'mastered' || s === 'verified',
              ).length
              // Count learning words (hollow/learning/pending)
              const hollow = Array.from(cachedProgressMap.values()).filter(
                (s) => s === 'hollow' || s === 'learning' || s === 'pending',
              ).length

              set(
                {
                  progress: {
                    total_discovered: solid + hollow,
                    solid_count: solid,
                    hollow_count: hollow,
                    raw_count: 0, // Will be updated from backend
                  },
                },
                false,
                'switchLearner:cacheProgressStats',
              )

              // If emoji pack is active, filter and calculate emoji stats
              if (state.activePack?.id === 'emoji_core') {
                const { packLoader } = await import('@/lib/pack-loader')
                const packData = await packLoader.loadPack('emoji_core')

                if (packData) {
                  const emojiSenseIds = new Set(packData.vocabulary.map((w) => w.sense_id))

                  // Filter cached progress to only emoji pack words
                  const emojiProgressMap = new Map<string, string>()
                  cachedProgressMap.forEach((status, senseId) => {
                    if (emojiSenseIds.has(senseId)) {
                      emojiProgressMap.set(senseId, status)
                    }
                  })

                  // Bulk load SRS levels (optimized - single query, not N+1)
                  const cachedSRSMap = await localStore.getSRSLevels(learnerId)
                  // Filter to only emoji pack words
                  const emojiSRSMap = new Map<string, string>()
                  cachedSRSMap.forEach((level, senseId) => {
                    if (emojiSenseIds.has(senseId)) {
                      emojiSRSMap.set(senseId, level)
                    }
                  })

                  // Update emoji progress and SRS levels in store immediately
                  set(
                    {
                      emojiProgress: emojiProgressMap,
                      emojiSRSLevels: emojiSRSMap,
                    },
                    false,
                    'switchLearner:cacheEmojiProgress',
                  )

                  // Recalculate emoji stats
                  const masteredWords = packData.vocabulary.filter((word) => {
                    const status = emojiProgressMap.get(word.sense_id)
                    return status === 'solid' || status === 'mastered'
                  })

                  const totalWords = packData.vocabulary.length
                  const collectedWords = emojiProgressMap.size
                  const masteredWordsCount = masteredWords.length
                  const learningWordsCount = Array.from(emojiProgressMap.values()).filter(
                    (s) => s === 'hollow' || s === 'learning' || s === 'pending',
                  ).length

                  set(
                    {
                      emojiMasteredWords: masteredWords,
                      emojiStats: {
                        totalWords,
                        collectedWords,
                        masteredWords: masteredWordsCount,
                        learningWords: learningWordsCount,
                      },
                    },
                    false,
                    'switchLearner:cacheEmojiStats',
                  )

                  console.log(
                    `⚡ Fast-switch (IndexedDB): Loaded ${emojiProgressMap.size} emoji items from cache for ${learner.display_name}`,
                  )
                }
              } else {
                // No emoji pack, but we have progress - clear emoji data
                // IMPORTANT: Also clear emojiMasteredWords so collection page
                // doesn't keep showing previous learner's trophies.
                // Use empty Maps (not null) for consistent pipeline
                set(
                  {
                    emojiProgress: new Map<string, string>(), // Empty Map for consistency
                    emojiSRSLevels: new Map<string, string>(), // Empty Map for consistency
                    emojiStats: null,
                    emojiMasteredWords: [],
                  },
                  false,
                  'switchLearner:clearEmojiData',
                )
              }

              console.log(
                `⚡ Fast-switch (IndexedDB): Loaded ${cachedProgressMap.size} progress items from cache for ${learner.display_name}`,
              )

              // Create/update learnerCache entry with due cards for instant future switches
              set(
                (s) => {
                  const learnerCache = {
                    ...s.learnerCache,
                    [learnerId]: {
                      miningQueue: s.miningQueue,
                      emojiProgress: s.emojiProgress || new Map<string, string>(),
                      emojiSRSLevels: s.emojiSRSLevels || new Map<string, string>(),
                      progress: s.progress,
                      dueCards: cachedDueCards,
                      collectedWords: cachedCollectedWords,
                      currencies: s.currencies,
                      rooms: s.rooms || [],
                      timestamp: Date.now(),
                    },
                  }
                  return { learnerCache }
                },
                false,
                'switchLearner:updateCacheWithDueCards',
              )
            } else {
              // No cache found - initialize as empty Maps (not null) for consistent pipeline
              // All learners should have Maps (even if empty), never null, so components don't need fallbacks
              const emptyEmojiStats = state.activePack?.id === 'emoji_core' ? {
                totalWords: 200,
                collectedWords: 0,
                masteredWords: 0,
                learningWords: 0,
              } : null
              
              const emptyEmojiProgress = new Map<string, string>()
              const emptyEmojiSRSLevels = new Map<string, string>()
              
              // CRITICAL: Create cache entry for empty learner so next switch is instant
              // Include due cards from IndexedDB (may be empty, but still cache for consistency)
              set(
                (s) => {
                  const learnerCache = {
                    ...s.learnerCache,
                    [learnerId]: {
                      miningQueue: [],
                      emojiProgress: emptyEmojiProgress,
                      emojiSRSLevels: emptyEmojiSRSLevels,
                      progress: defaultProgress,
                      dueCards: cachedDueCards, // Use loaded due cards (may be empty)
                      collectedWords: cachedCollectedWords, // Use loaded collectedWords (may be empty)
                      currencies: null,
                      rooms: [],
                      timestamp: Date.now(),
                    },
                  }
                  
                  return {
                    learnerCache,
                    emojiProgress: emptyEmojiProgress, // Always a Map, never null
                    emojiSRSLevels: emptyEmojiSRSLevels, // Always a Map, never null
                    emojiStats: emptyEmojiStats,
                    emojiMasteredWords: [],
                    progress: defaultProgress,
                  }
                },
                false,
                'switchLearner:noCache',
              )
              console.log(
                `⚠️ No progress cache found for ${learner.display_name}, initialized empty Maps and created cache entry`,
              )
            }
          } catch (e) {
            console.warn('Failed to load cached progress:', e)
            // On error, initialize as empty Maps (not null) for consistent pipeline
            const emptyEmojiStats = state.activePack?.id === 'emoji_core' ? {
              totalWords: 200,
              collectedWords: 0,
              masteredWords: 0,
              learningWords: 0,
            } : null
            
            const emptyEmojiProgress = new Map<string, string>()
            const emptyEmojiSRSLevels = new Map<string, string>()
            
            // CRITICAL: Create cache entry even on error so next switch is instant
            // Include due cards from IndexedDB (loaded before the try block, so available even on error)
            set(
              (s) => {
                const learnerCache = {
                  ...s.learnerCache,
                  [learnerId]: {
                    miningQueue: [],
                    emojiProgress: emptyEmojiProgress,
                    emojiSRSLevels: emptyEmojiSRSLevels,
                    progress: defaultProgress,
                    dueCards: cachedDueCards, // Use loaded due cards (may be empty)
                    currencies: null,
                    rooms: [],
                    timestamp: Date.now(),
                  },
                }
                
                return {
                  learnerCache,
                  emojiProgress: emptyEmojiProgress, // Always a Map, never null
                  emojiSRSLevels: emptyEmojiSRSLevels, // Always a Map, never null
                  emojiStats: emptyEmojiStats,
                  emojiMasteredWords: [],
                  progress: defaultProgress,
                }
              },
              false,
              'switchLearner:cacheError',
            )
          }
        }
        
        // Phase 3: Background Sync (non-blocking)
        // Trigger network sync, update IndexedDB, then rebuild snapshots from cache.
        try {
          const { downloadService } = await import('@/services/downloadService')
          const { packLoader } = await import('@/lib/pack-loader')

          const learnerIdAtStart = learnerId

          downloadService
            .syncProgress(learnerIdAtStart)
            .then(async () => {
              try {
                // After sync, re-read learner's progress from IndexedDB
                const progressMap = await localStore.getAllProgress(learnerIdAtStart)
                const srsLevelsMap = await localStore.getSRSLevels(learnerIdAtStart)

                const solid = Array.from(progressMap.values()).filter(
                  (s) => s === 'solid' || s === 'mastered' || s === 'verified',
                ).length
                const hollow = Array.from(progressMap.values()).filter(
                  (s) => s === 'hollow' || s === 'learning' || s === 'pending',
                ).length

                const progressStats: ProgressStats = {
                  total_discovered: solid + hollow,
                  solid_count: solid,
                  hollow_count: hollow,
                  raw_count: 0,
                }

                // Always initialize as empty Maps (not null) for consistent pipeline
                let emojiProgressMap: Map<string, string> = new Map<string, string>()
                let emojiSRSMap: Map<string, string> = new Map<string, string>()
                let emojiMasteredWords: PackVocabularyItem[] = []
                let emojiStats:
                  | { totalWords: number; collectedWords: number; masteredWords: number; learningWords: number }
                  | null = null

                const current = get()
                if (current.activePack?.id === 'emoji_core') {
                  try {
                    const packData = await packLoader.loadPack('emoji_core')
                    if (packData) {
                      const emojiSenseIds = new Set(packData.vocabulary.map((w) => w.sense_id))

                      // Maps already initialized above, just populate them
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

                      const mastered = packData.vocabulary.filter((word) => {
                        const status = emojiProgressMap!.get(word.sense_id)
                        return status === 'solid' || status === 'mastered'
                      })

                      emojiMasteredWords = mastered

                      const totalWords = packData.vocabulary.length
                      const collectedWords = emojiProgressMap.size
                      const masteredWordsCount = mastered.length
                      const learningWordsCount = Array.from(emojiProgressMap.values()).filter(
                        (s) => s === 'hollow' || s === 'learning' || s === 'pending',
                      ).length

                      emojiStats = {
                        totalWords,
                        collectedWords,
                        masteredWords: masteredWordsCount,
                        learningWords: learningWordsCount,
                      }
                    }
                  } catch (error) {
                    if (process.env.NODE_ENV === 'development') {
                      console.warn('⚠️ switchLearner: Failed to rebuild emoji snapshot after sync:', error)
                    }
                  }
                }

                // Apply updates only if learner still exists
                set(
                  (s) => {
                    const isActive = s.activeLearner?.id === learnerIdAtStart
                    const existing = s.learnerCache[learnerIdAtStart]

                    if (process.env.NODE_ENV === 'development') {
                      console.log(
                        `🔄 Background sync complete for ${learnerIdAtStart}`,
                        {
                          isActive,
                          hasExistingCache: !!existing,
                          emojiProgressMapSize: emojiProgressMap.size,
                          emojiSRSMapSize: emojiSRSMap.size,
                          emojiProgressMapType: emojiProgressMap.constructor.name,
                          emojiSRSMapType: emojiSRSMap.constructor.name,
                        }
                      )
                    }

                    const nextCacheEntry = {
                      miningQueue: existing?.miningQueue ?? s.miningQueue,
                      emojiProgress: emojiProgressMap, // Always a Map (never null) from above
                      emojiSRSLevels: emojiSRSMap, // Always a Map (never null) from above
                      progress: progressStats,
                      dueCards: existing?.dueCards ?? s.dueCards ?? [],
                      currencies: existing?.currencies ?? s.currencies ?? null,
                      rooms: existing?.rooms ?? s.rooms ?? [],
                      timestamp: Date.now(),
                    }

                    const learnerCache = {
                      ...s.learnerCache,
                      [learnerIdAtStart]: nextCacheEntry,
                    }

                    if (!isActive) {
                      return {
                        learnerCache,
                      }
                    }

                    return {
                      learnerCache,
                      progress: progressStats,
                      emojiProgress: nextCacheEntry.emojiProgress,
                      emojiSRSLevels: nextCacheEntry.emojiSRSLevels,
                      emojiMasteredWords:
                        emojiMasteredWords.length > 0 ? emojiMasteredWords : s.emojiMasteredWords,
                      emojiStats: emojiStats ?? s.emojiStats,
                    }
                  },
                  false,
                  'switchLearner:syncFromIndexedDB',
                )
              } catch (err) {
                console.warn('⚠️ Failed to apply synced progress from IndexedDB:', err)
              }
            })
            .catch((error) => {
              console.warn('⚠️ Background sync failed (using cached data):', error)
            })

          console.log(`✅ Switched to learner: ${learner.display_name} (${learnerIdAtStart})`)
        } catch (error) {
          console.error('Failed to start background sync:', error)
        }
      },
      
      setBalance: (balance) => set({ balance }, false, 'setBalance'),
      
      setLearnerProfile: (profile) => set({ learnerProfile: profile }, false, 'setLearnerProfile'),
      
      setAchievements: (achievements) => set({ achievements }, false, 'setAchievements'),
      
      setGoals: (goals) => set({ goals }, false, 'setGoals'),
      
      setNotifications: (notifications) => set({ notifications }, false, 'setNotifications'),
      
      setProgress: (progress) => set({ progress }, false, 'setProgress'),
      
      setVocabulary: (vocabulary) => set({ vocabulary }, false, 'setVocabulary'),
      
      setCurrencies: (currencies) => set({ currencies }, false, 'setCurrencies'),
      
      setRooms: (rooms) => set({ rooms }, false, 'setRooms'),
      
      // Build state (per-learner currencies/rooms) - keeps learnerCache in sync
      setBuildState: (learnerId, currencies, rooms) =>
        set(
          (s) => {
            const isActive = s.activeLearner?.id === learnerId

            const existing = s.learnerCache[learnerId] || {
              miningQueue: s.miningQueue,
              emojiProgress: s.emojiProgress || new Map<string, string>(),
              emojiSRSLevels: s.emojiSRSLevels || new Map<string, string>(), // Always a Map
              progress: s.progress,
              dueCards: s.dueCards || [],
              currencies: currencies,
              rooms: rooms,
              timestamp: 0,
            }

            return {
              ...(isActive
                ? {
                    currencies,
                    rooms,
                  }
                : {}),
              learnerCache: {
                ...s.learnerCache,
                [learnerId]: {
                  ...existing,
                  currencies,
                  rooms,
                  timestamp: Date.now(),
                },
              },
            }
          },
          false,
          'setBuildState',
        ),
      
      setMineBlocks: (blocks) => set({ mineBlocks: blocks }, false, 'setMineBlocks'),
      
      setMineDataLoaded: (loaded) => set({ mineDataLoaded: loaded }, false, 'setMineDataLoaded'),
      
      setDueCards: (cards) =>
        set(
          (state) => {
            const activeLearnerId = state.activeLearner?.id
            let learnerCache = state.learnerCache

            if (activeLearnerId) {
              const existing = state.learnerCache[activeLearnerId] || {
                miningQueue: state.miningQueue,
                emojiProgress: state.emojiProgress || new Map<string, string>(),
                emojiSRSLevels: state.emojiSRSLevels || new Map<string, string>(), // Always a Map
                progress: state.progress,
                dueCards: [],
                timestamp: 0,
              }

              learnerCache = {
                ...state.learnerCache,
                [activeLearnerId]: {
                  ...existing,
                  dueCards: cards,
                  timestamp: Date.now(),
                },
              }
            }

            return {
              dueCards: cards,
              learnerCache,
            }
          },
          false,
          'setDueCards',
        ),
      
      setLeaderboardData: (data) => set({ 
        leaderboardData: { ...data, timestamp: Date.now() } 
      }, false, 'setLeaderboardData'),
      
      setActivePack: (pack) => set({ activePack: pack }, false, 'setActivePack'),
      
      // Emoji Pack Data Actions
      setEmojiVocabulary: (vocab) => set({ emojiVocabulary: vocab }, false, 'setEmojiVocabulary'),
      setEmojiProgress: (progress) => {
        if (process.env.NODE_ENV === 'development') {
          const size = progress instanceof Map ? progress.size : progress === null ? 'null' : 'unknown'
          const stack = new Error().stack?.split('\n')[2]?.trim() || 'unknown'
          console.log(`🔄 Store: setEmojiProgress(${size})`, { caller: stack })
        }
        // CRITICAL: If emoji pack is active, ensure progress is always a Map (never null)
        const state = get()
        if (state.activePack?.id === 'emoji_core' && progress === null) {
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ setEmojiProgress: Attempted to set null while emoji pack is active, using empty Map instead')
          }
          set({ emojiProgress: new Map<string, string>() }, false, 'setEmojiProgress')
        } else {
          set({ emojiProgress: progress }, false, 'setEmojiProgress')
        }
      },
      setEmojiSRSLevels: (levels) => {
        // CRITICAL: If emoji pack is active, ensure levels is always a Map (never null)
        const state = get()
        if (state.activePack?.id === 'emoji_core' && levels === null) {
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ setEmojiSRSLevels: Attempted to set null while emoji pack is active, using empty Map instead')
          }
          set({ emojiSRSLevels: new Map<string, string>() }, false, 'setEmojiSRSLevels')
        } else {
          set({ emojiSRSLevels: levels }, false, 'setEmojiSRSLevels')
        }
      },
      setEmojiMasteredWords: (words) => set({ emojiMasteredWords: words }, false, 'setEmojiMasteredWords'),
      setEmojiStats: (stats) => set({ emojiStats: stats }, false, 'setEmojiStats'),
      
      // Game-like Inventory Actions
      setCollectedWords: (words) => set({ collectedWords: words }, false, 'setCollectedWords'),
      
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
              
              // Note: Currencies are stored separately in the store, not in learnerProfile
              // Currencies updates should be handled via the currencies state slice
              
              // Streak is already in learnerProfile as current_streak
              if (delta.new_streak_days !== undefined) {
                // Update current_streak directly (it's a number, not an object)
                profile.current_streak = delta.new_streak_days
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
      // ⚡ DELTA STRATEGY: Optimistic UI update, background sync
      addToQueue: (senseId, word) => {
        const state = get()
        const activeLearnerId = state.activeLearner?.id

        if (!activeLearnerId) {
          console.warn('⚠️ addToQueue: No activeLearner, skipping')
          return
        }

        // DEBUG: Log active learner when mining
        if (process.env.NODE_ENV === 'development') {
          console.log('[addToQueue] Mining word:', {
            senseId,
            word,
            activeLearnerId,
            activeLearnerName: state.activeLearner?.display_name,
            activeLearnerIsParent: state.activeLearner?.is_parent_profile,
          })
        }

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
            
            // ⚡ OPTIMISTIC UPDATE: Update emoji progress immediately (Delta Strategy)
            // NOTE: emojiProgress/emojiSRSLevels are always Maps (never null) due to unified pipeline.
            // We still create fresh Maps here to ensure the first mined word appears instantly.
            let newEmojiProgress = state.emojiProgress || new Map<string, string>()
            let newEmojiSRSLevels = state.emojiSRSLevels || new Map<string, string>()
            let newProgress = state.progress

            if (state.activePack?.id === 'emoji_core') {
              const baseProgressMap = state.emojiProgress ?? new Map<string, string>()
              const baseSrsMap = state.emojiSRSLevels ?? new Map<string, string>()

              newEmojiProgress = new Map(baseProgressMap)
              // Set status to 'hollow' (learning) immediately
              newEmojiProgress.set(senseId, 'hollow')

              // Also update SRS levels for Build/Collection (Parallel State Pattern)
              newEmojiSRSLevels = new Map(baseSrsMap)
              newEmojiSRSLevels.set(senseId, 'learning')  // Newly mined words start at 'learning'

              // Update progress stats optimistically
              newProgress = {
                ...state.progress,
                total_discovered: state.progress.total_discovered + 1,
                hollow_count: state.progress.hollow_count + 1,
              }

              // ⚡ OPTIMISTIC: Save progress to IndexedDB immediately (learner-scoped)
              // Include masteryLevel so it persists and Build/collection pages can read it.
              localStore
                .saveProgress(activeLearnerId, senseId, 'hollow', { masteryLevel: 'learning' })
                .catch(err => console.warn('Failed to save progress optimistically:', err))

              // Invalidate cached blocks (they need to be rebuilt with new status)
              // Fire-and-forget (non-blocking)
              localStore.deleteCache(getMiningQueueCacheKey(activeLearnerId))
                .then(() => {
                  // Also invalidate mine blocks cache
                  const { getLearnerMineBlocksKey } = require('@/services/downloadService')
                  return localStore.deleteCache(getLearnerMineBlocksKey(activeLearnerId))
                })
                .catch(err => {
                  console.warn('Failed to invalidate mine blocks cache after addToQueue:', err)
                })
            }


            // 🔁 Update in-memory learner cache snapshot for instant switching
            let learnerCache = state.learnerCache
            if (activeLearnerId) {
              const existing = state.learnerCache[activeLearnerId] || {
                miningQueue: state.miningQueue,
                emojiProgress: state.emojiProgress || new Map<string, string>(),
                emojiSRSLevels: state.emojiSRSLevels || new Map<string, string>(), // Always a Map
                progress: state.progress,
                dueCards: state.dueCards || [],
                timestamp: 0,
              }

              learnerCache = {
                ...state.learnerCache,
                [activeLearnerId]: {
                  ...existing,
                  miningQueue: newQueue,
                  emojiProgress: newEmojiProgress || existing.emojiProgress,
                  emojiSRSLevels: newEmojiSRSLevels ?? existing.emojiSRSLevels,
                  progress: newProgress,
                  // dueCards unchanged here
                  timestamp: Date.now(),
                },
              }
            }

            // Persist to IndexedDB (fire and forget) - learner-scoped cache key
            localStore.setCache(getMiningQueueCacheKey(activeLearnerId), newQueue, MINING_QUEUE_TTL)
              .catch(err => console.warn('Failed to persist mining queue:', err))

            return { 
              miningQueue: newQueue,
              emojiProgress: newEmojiProgress,
              emojiSRSLevels: newEmojiSRSLevels,
              progress: newProgress,
              learnerCache,
            }
          },
          false,
          'addToQueue:optimistic'
        )
        
        // Add to collectedWords if not already present (background, fire-and-forget)
        if (state.activePack?.id === 'emoji_core') {
          const currentCollected = get().collectedWords || []
          if (!currentCollected.find(w => w.sense_id === senseId)) {
            // Load pack data to get full word information
            import('@/lib/pack-loader').then(({ packLoader }) => {
              packLoader.loadPack('emoji_core').then(packData => {
                const wordData = packData?.vocabulary.find(w => w.sense_id === senseId)
                if (wordData) {
                  const collectedWord: CollectedWord = {
                    ...wordData,
                    collectedAt: Date.now(),  // CRITICAL: Timestamp for audit trail
                    status: 'hollow',
                    masteryLevel: 'learning'
                  }
                  
                  const freshCollected = get().collectedWords || []
                  if (!freshCollected.find(w => w.sense_id === senseId)) {
                    const newCollected = [...freshCollected, collectedWord]
                    set({ collectedWords: newCollected }, false, 'addToQueue:addToCollection')
                    
                    // Save to IndexedDB
                    localStore.saveCollectedWord(activeLearnerId, collectedWord)
                      .catch(err => console.warn(`Failed to save collected word ${senseId}:`, err))
                    
                    // Update learnerCache snapshot
                    const currentCache = get().learnerCache[activeLearnerId]
                    if (currentCache) {
                      set((s) => ({
                        learnerCache: {
                          ...s.learnerCache,
                          [activeLearnerId]: {
                            ...currentCache,
                            collectedWords: newCollected,
                          }
                        }
                      }), false, 'addToQueue:updateCache')
                    }
                  }
                }
              }).catch(err => console.warn('Failed to load pack data for collectedWords:', err))
            }).catch(err => console.warn('Failed to import pack-loader:', err))
          }
        }
        
        // 🔥 BACKGROUND SYNC: Start forging (smelting) the word so it enters SRS
        // Fire-and-forget: Don't block UI, reconcile later if needed
        progressApi.startForging(senseId, activeLearnerId)
          .then(async (result) => {
            console.log(`⚒️ Started smelting "${word}" for learner ${activeLearnerId}:`, result.message)
            // Delta Strategy: Apply XP/progress from backend (reconcile)
            if (result.delta_xp || result.delta_sparks || result.delta_discovered) {
              useAppStore.getState().applyDelta({
                delta_xp: result.delta_xp,
                delta_sparks: result.delta_sparks,
                delta_discovered: result.delta_discovered,
                delta_hollow: result.delta_hollow,
              })
            }
            
            // ⚡ OPTIMISTIC UPDATE: Add to dueCards immediately (Tier 1: Zustand + Tier 2: IndexedDB)
            // This gives instant feedback while API refresh happens in background
            // Respects 3-tier cache: Optimistic (Tier 1/2) → API Refresh (Tier 3) → Reconcile
            const currentState = useAppStore.getState()
            if (currentState.activeLearner?.id === activeLearnerId) {
              const currentDueCards = currentState.dueCards || []
              // Check if card already exists (avoid duplicates)
              const cardExists = currentDueCards.some(card => card.learning_point_id === senseId)
              if (!cardExists) {
                // Create optimistic due card (will be replaced by real data from API)
                const optimisticCard = {
                  verification_schedule_id: 0, // Placeholder, will be updated by API
                  learning_progress_id: result.learning_progress_id || 0,
                  learning_point_id: senseId,
                  word: word,
                  scheduled_date: new Date().toISOString().split('T')[0], // Today
                  days_overdue: 0,
                  mastery_level: 'learning',
                  retention_predicted: null,
                }
                const newDueCards = [...currentDueCards, optimisticCard]
                currentState.setDueCards(newDueCards)
                
                // Also update IndexedDB cache (Tier 2)
                try {
                  const { getLearnerDueCardsCacheKey } = await import('@/services/downloadService')
                  const cacheKey = getLearnerDueCardsCacheKey(activeLearnerId)
                  // CACHE_TTL.SHORT = 7 days (same as used in downloadService)
                  const CACHE_TTL_SHORT = 7 * 24 * 60 * 60 * 1000
                  await localStore.setCache(cacheKey, newDueCards, CACHE_TTL_SHORT)
                  
                  if (process.env.NODE_ENV === 'development') {
                    console.log(`⚡ Optimistically added "${word}" to dueCards (${newDueCards.length} total)`)
                  }
                } catch (cacheErr) {
                  // Non-critical - IndexedDB update failed, but Zustand is updated
                  if (process.env.NODE_ENV === 'development') {
                    console.warn('⚠️ Failed to update IndexedDB cache optimistically:', cacheErr)
                  }
                }
              }
            }
            
            // 🔄 BACKGROUND SYNC: Refresh dueCards from API to get real data (Tier 3)
            // This ensures we have the correct verification_schedule_id and reconciles any differences
            // Wait 300ms to ensure database transaction has committed
            try {
              await new Promise(resolve => setTimeout(resolve, 300))
              
              const { downloadService } = await import('@/services/downloadService')
              const freshDueCards = await downloadService.refreshLearnerDueCards(activeLearnerId)
              
              // Guard: Only update if learner hasn't switched (race condition protection)
              const currentState = useAppStore.getState()
              if (currentState.activeLearner?.id === activeLearnerId) {
                if (process.env.NODE_ENV === 'development') {
                  const oldCount = currentState.dueCards.length
                  console.log(`✅ Refreshed dueCards after startForging: ${freshDueCards.length} cards (was ${oldCount}) for learner ${activeLearnerId}`)
                }
                // downloadService.refreshLearnerDueCards() already updates Zustand if activeLearner matches
                // No need to call setDueCards() here - it's handled by the service
              } else {
                if (process.env.NODE_ENV === 'development') {
                  console.log(`⏭️ Skipped dueCards refresh - learner switched from ${activeLearnerId} to ${currentState.activeLearner?.id}`)
                }
              }
            } catch (refreshErr) {
              // Non-critical - dueCards will refresh on next page visit or manual refresh
              // Don't fail loudly - word is still queued and will sync eventually
              if (process.env.NODE_ENV === 'development') {
                console.warn('⚠️ Failed to refresh dueCards after startForging (non-critical):', refreshErr)
              }
            }
          })
          .catch((err) => {
            // Don't fail loudly - word is still queued locally (eventual consistency)
            console.warn(`Failed to start smelting "${word}":`, err)
            // Word remains in queue, will retry on next sync
          })
      },

      removeFromQueue: (senseId) => {
        set(
          (state) => {
            const activeLearnerId = state.activeLearner?.id
            if (!activeLearnerId) {
              console.warn('⚠️ removeFromQueue: No activeLearner, skipping')
              return state
            }
            const newQueue = state.miningQueue.filter(q => q.senseId !== senseId)
            // Persist to IndexedDB (fire and forget) - learner-scoped cache key
            localStore.setCache(getMiningQueueCacheKey(activeLearnerId), newQueue, MINING_QUEUE_TTL)
              .catch(err => console.warn('Failed to persist mining queue:', err))
            return { miningQueue: newQueue }
          },
          false,
          'removeFromQueue'
        )
      },

      clearQueue: () => {
        const state = get()
        const activeLearnerId = state.activeLearner?.id
        if (!activeLearnerId) {
          console.warn('⚠️ clearQueue: No activeLearner, skipping')
          return
        }
        set({ miningQueue: [] }, false, 'clearQueue')
        // Persist empty queue to IndexedDB - learner-scoped cache key
        localStore.setCache(getMiningQueueCacheKey(activeLearnerId), [], MINING_QUEUE_TTL)
          .catch(err => console.warn('Failed to persist mining queue:', err))
      },

      isInQueue: (senseId: string): boolean => {
        const state = useAppStore.getState()
        return state.miningQueue.some(q => q.senseId === senseId)
      },

        mineAllQueued: () => {
        const state = get()
        const activeLearnerId = state.activeLearner?.id
        if (!activeLearnerId) {
          console.warn('⚠️ mineAllQueued: No activeLearner, skipping')
          return
        }
        const senseIds = state.miningQueue.map(q => q.senseId)
        if (senseIds.length > 0) {
          state.mineSenses(senseIds)
          set({ miningQueue: [] }, false, 'mineAllQueued:clearQueue')
          // Persist empty queue to IndexedDB - learner-scoped cache key
          localStore.setCache(getMiningQueueCacheKey(activeLearnerId), [], MINING_QUEUE_TTL)
            .catch(err => console.warn('Failed to persist mining queue:', err))
        }
      },

      hydrateMiningQueue: async () => {
        try {
          const state = get()
          const activeLearnerId = state.activeLearner?.id
          if (!activeLearnerId) {
            console.warn('⚠️ hydrateMiningQueue: No activeLearner, skipping')
            return
          }

          // ✅ STEP 1: Load Local Queue from IndexedDB (preserve unsynced additions)
          // Use learner-scoped cache key to prevent data bleeding between learners
          const cachedQueue = await localStore.getCache<QueuedSense[]>(getMiningQueueCacheKey(activeLearnerId))
          const localQueue = cachedQueue || []
          console.log(`📦 Local queue loaded: ${localQueue.length} items for learner ${activeLearnerId}`)

          // ✅ STEP 2: Fetch Backend Progress (source of truth)
          try {
            const { progressApi } = await import('@/services/progressApi')
            const backendProgress = await progressApi.getUserProgress(activeLearnerId)
            
            if (backendProgress?.progress && backendProgress.progress.length > 0) {
              // Save ALL progress to IndexedDB for the Mine page to use (learner-scoped)
              // Use importProgress for bulk insert (more efficient)
              await localStore.importProgress(activeLearnerId, backendProgress.progress)
              console.log(`💾 Saved ${backendProgress.progress.length} progress items to IndexedDB for learner ${activeLearnerId}`)
              
              // Create a map of backend statuses for quick lookup
              const backendStatusMap = new Map<string, string>()
              backendProgress.progress.forEach((p: any) => {
                backendStatusMap.set(p.sense_id, p.status)
              })

              // ✅ STEP 3: CLEANUP - Remove words from local queue that backend says are done
              const cleanedLocalQueue = localQueue.filter(item => {
                const backendStatus = backendStatusMap.get(item.senseId)
                // Remove if backend says it's 'solid', 'mastered', or 'verified'
                if (backendStatus === 'solid' || backendStatus === 'mastered' || backendStatus === 'verified') {
                  console.log(`🧹 Removing "${item.word}" from queue (backend status: ${backendStatus})`)
                  return false
                }
                return true
              })
              const removedCount = localQueue.length - cleanedLocalQueue.length
              if (removedCount > 0) {
                console.log(`🧹 Cleaned up ${removedCount} completed words from local queue`)
              }

              // ✅ STEP 4: MERGE - Add backend 'hollow' words that aren't in local queue
              const localQueueSenseIds = new Set(cleanedLocalQueue.map(item => item.senseId))
              const hollowItems = backendProgress.progress.filter((p: any) => 
                (p.status === 'pending' || p.status === 'learning' || p.status === 'hollow') &&
                !localQueueSenseIds.has(p.sense_id) // Only add if not already in local queue
              )

              const newBackendItems: QueuedSense[] = hollowItems.map((p: any) => ({
                senseId: p.sense_id,
                word: p.word || p.sense_id.split('.')[0], // fallback to sense_id prefix
                addedAt: Date.now(),
              }))
              // ✅ STEP 5: Combine cleaned local queue + new backend items
              const mergedQueue = [...cleanedLocalQueue, ...newBackendItems]
              
              // Update store and learner cache and IndexedDB - learner-scoped cache key
              set(
                (s) => {
                  let learnerCache = s.learnerCache
                  const existing = s.learnerCache[activeLearnerId] || {
                    miningQueue: s.miningQueue,
                    emojiProgress: s.emojiProgress || new Map<string, string>(),
                    emojiSRSLevels: s.emojiSRSLevels || new Map<string, string>(), // Always a Map (never null)
                    progress: s.progress,
                    dueCards: s.dueCards || [],
                    timestamp: 0,
                  }

                  learnerCache = {
                    ...s.learnerCache,
                    [activeLearnerId]: {
                      ...existing,
                      miningQueue: mergedQueue,
                      timestamp: Date.now(),
                    },
                  }

                  return {
                    miningQueue: mergedQueue,
                    learnerCache,
                  }
                },
                false,
                'hydrateMiningQueue:merged',
              )
              localStore.setCache(getMiningQueueCacheKey(activeLearnerId), mergedQueue, MINING_QUEUE_TTL)
                .catch(err => console.warn('Failed to persist mining queue:', err))
              
              console.log(`⛏️ Hydrated mining queue: ${mergedQueue.length} items (${cleanedLocalQueue.length} local after cleanup + ${newBackendItems.length} from backend)`)
              return
            }
          } catch (backendErr) {
            console.warn('Failed to sync mining queue from backend, using local cache only:', backendErr)
          }
          
          // ✅ FALLBACK: If backend sync fails, use local queue as-is
          if (localQueue.length > 0) {
            set(
              (s) => {
                let learnerCache = s.learnerCache
                const existing = s.learnerCache[activeLearnerId] || {
                  miningQueue: s.miningQueue,
                  emojiProgress: s.emojiProgress || new Map<string, string>(),
                  emojiSRSLevels: s.emojiSRSLevels || new Map<string, string>(), // Always a Map (never null)
                  progress: s.progress,
                  dueCards: s.dueCards || [],
                  timestamp: 0,
                }

                learnerCache = {
                  ...s.learnerCache,
                  [activeLearnerId]: {
                    ...existing,
                    miningQueue: localQueue,
                    timestamp: Date.now(),
                  },
                }

                return {
                  miningQueue: localQueue,
                  learnerCache,
                }
              },
              false,
              'hydrateMiningQueue:localOnly',
            )
            console.log(`⛏️ Using local mining queue only: ${localQueue.length} items (backend sync failed)`)
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

      // Verification Actions
      completeVerification: (results) => {
        const state = get()
        const activeLearnerId = state.activeLearner?.id
        if (!activeLearnerId) {
          console.warn('⚠️ completeVerification: No activeLearner, skipping')
          return
        }

        // Filter only correct answers (incorrect answers stay in queue)
        const correctResults = results.filter(r => r.isCorrect)
        if (correctResults.length === 0) {
          console.log('ℹ️ completeVerification: No correct answers to process')
          return
        }

        // Get current state
        const currentProgress = state.emojiProgress || new Map()
        const currentSRSLevels = state.emojiSRSLevels || new Map()
        const currentStats = state.progress
        const currentQueue = state.miningQueue
        const currentDueCards = state.dueCards || []

        // 1. OPTIMISTIC UPDATE (Instant)
        const newProgress = new Map(currentProgress)
        const newSRSLevels = new Map(currentSRSLevels)
        const correctCount = correctResults.length

        // Collect all correct sense IDs to remove from queue and dueCards
        const correctSenseIds = new Set(correctResults.map(r => r.senseId))

        correctResults.forEach(({ senseId }) => {
          // Update progress: hollow → solid
          newProgress.set(senseId, 'solid')
          
          // Update SRS: learning → familiar (simple rule per Gemini feedback)
          newSRSLevels.set(senseId, 'familiar')
        })

        // Remove all correct answers from queue in a single atomic operation
        const newQueue = currentQueue.filter(q => !correctSenseIds.has(q.senseId))

        // Remove verified words from dueCards list so they disappear from UI immediately
        // Keep card if its learning_point_id is NOT in the correct answers list
        const newDueCards = currentDueCards.filter(card => 
          !card.learning_point_id || !correctSenseIds.has(card.learning_point_id)
        )

        // Update stats
        const newStats = {
          ...currentStats,
          hollow_count: Math.max(0, (currentStats.hollow_count || 0) - correctCount),
          solid_count: (currentStats.solid_count || 0) + correctCount,
        }

        // Apply ALL updates to store in a single set() call (atomic)
        set(
          (s) => {
            // Sync learnerCache snapshot for this learner so instant-switch shows the updated state
            let learnerCache = s.learnerCache
            if (activeLearnerId) {
              const existing = s.learnerCache[activeLearnerId] || {
                miningQueue: newQueue,
                emojiProgress: newProgress,
                emojiSRSLevels: newSRSLevels,
                progress: newStats,
                dueCards: newDueCards,
                timestamp: 0,
              }

              learnerCache = {
                ...s.learnerCache,
                [activeLearnerId]: {
                  ...existing,
                  miningQueue: newQueue,
                  emojiProgress: newProgress,
                  emojiSRSLevels: newSRSLevels,
                  progress: newStats,
                  dueCards: newDueCards,
                  timestamp: Date.now(),
                },
              }
            }

            return {
              emojiProgress: newProgress,
              emojiSRSLevels: newSRSLevels,
              progress: newStats,
              miningQueue: newQueue, // Update queue atomically
              dueCards: newDueCards, // Remove verified words from dueCards
              learnerCache,
            }
          },
          false,
          'completeVerification:optimistic',
        )

        // Persist queue to IndexedDB (fire and forget) - learner-scoped cache key
        localStore.setCache(getMiningQueueCacheKey(activeLearnerId), newQueue, MINING_QUEUE_TTL)
          .catch(err => console.warn('Failed to persist mining queue:', err))

        // 2. PERSISTENCE (IndexedDB - Non-blocking)
        correctResults.forEach(({ senseId }) => {
          localStore.saveProgress(
            activeLearnerId,
            senseId,
            'solid',
            { masteryLevel: 'familiar' }
          ).catch(err => console.warn(`Failed to save progress for ${senseId}:`, err))
        })

        // Update collectedWords
        correctResults.forEach(({ senseId }) => {
          const currentCollected = get().collectedWords || []
          const index = currentCollected.findIndex(w => w.sense_id === senseId)
          
          if (index >= 0) {
            const updated = [...currentCollected]
            updated[index] = {
              ...updated[index],
              status: 'solid',
              masteryLevel: 'familiar',
              // Preserve collectedAt timestamp (don't overwrite)
              // masteredAt will be set when status becomes 'mastered'
            }
            set({ collectedWords: updated }, false, 'completeVerification:updateCollection')
            
            // Save to IndexedDB
            localStore.saveCollectedWord(activeLearnerId, updated[index])
              .catch(err => console.warn(`Failed to save collected word ${senseId}:`, err))
            
            // Update learnerCache snapshot
            const currentCache = get().learnerCache[activeLearnerId]
            if (currentCache) {
              set((s) => ({
                learnerCache: {
                  ...s.learnerCache,
                  [activeLearnerId]: {
                    ...currentCache,
                    collectedWords: updated,
                  }
                }
              }), false, 'completeVerification:updateCache')
            }
          }
        })

        // 3. SRS SYNC (Background - Fire-and-Forget)
        // Look up verification schedule info and submit to backend
        correctResults.forEach(({ senseId }) => {
          // Fire-and-forget: Don't await, don't block UI
          progressApi.getVerificationScheduleInfo(senseId, activeLearnerId)
            .then(scheduleInfo => {
              if (!scheduleInfo) {
                console.warn(`⚠️ No verification schedule found for ${senseId}, skipping backend sync`)
                return
              }

              // Submit to backend for SRS processing
              // Use POST /api/v1/verification/review to trigger SRS algorithm
              // This ensures next review is scheduled and mastery level is updated
              const { authenticatedPost } = require('@/lib/api-client')
              authenticatedPost(`/api/v1/verification/review`, {
                learning_progress_id: scheduleInfo.learning_progress_id,
                performance_rating: 2, // GOOD rating (default for correct answer in emoji MCQ)
                response_time_ms: 5000, // Default response time (TODO: Track actual time in EmojiMCQSession)
              }).catch(err => {
                console.warn(`Failed to sync verification for ${senseId}:`, err)
              })
            })
            .catch(err => {
              console.warn(`Failed to get verification schedule info for ${senseId}:`, err)
            })
        })

        // 4. UPDATE BACKEND PROGRESS STATUS (Background - Fire-and-Forget)
        // This ensures the backend knows the word is 'verified' so it doesn't reappear in queue on refresh
        // CRITICAL: Without this, hydrateMiningQueue will see backend status as 'hollow' and add words back
        if (correctResults.length > 0) {
          const { authenticatedPost } = require('@/lib/api-client')
          authenticatedPost('/api/v1/sync', {
            actions: correctResults.map(({ senseId }) => ({
              type: 'UPDATE_PROGRESS',
              sense_id: senseId,
              timestamp: Date.now(), // Required: client timestamp in ms since epoch (for conflict resolution)
              payload: {
                status: 'verified' // Backend uses 'verified' for solid state (not 'solid')
              }
            }))
          }).catch(err => {
            console.warn('Failed to sync progress status to backend:', err)
          })
        }

        console.log(`✅ Verified ${correctCount} words: ${correctResults.map(r => r.senseId).join(', ')}`)
      },

      // Reset (for logout)
      reset: () =>
        set(
          {
            user: null,
            children: [],
            childrenSummaries: [],
            learnersSummaries: [],
            selectedChildId: null,
            learners: [],
            activeLearner: null,
            learnerCache: {},
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
            emojiVocabulary: null,
            emojiProgress: new Map<string, string>(), // Always a Map (never null) for consistent pipeline
            emojiSRSLevels: new Map<string, string>(), // Always a Map (never null) for consistent pipeline
            emojiMasteredWords: null,
            emojiStats: null,
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
export const selectLearnersSummaries = (state: AppState) => state.learnersSummaries
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

// Learners Selectors (Multi-Profile System)
export const selectLearners = (state: AppState) => state.learners
export const selectActiveLearner = (state: AppState) => state.activeLearner
export const selectParentLearner = (state: AppState) => 
  state.learners.find(l => l.is_parent_profile) || null
export const selectChildLearners = (state: AppState) => 
  state.learners.filter(l => !l.is_parent_profile)

// Emoji Pack Data Selectors
export const selectEmojiVocabulary = (state: AppState) => state.emojiVocabulary
export const selectEmojiProgress = (state: AppState) => state.emojiProgress
export const selectEmojiMasteredWords = (state: AppState) => state.emojiMasteredWords
export const selectEmojiStats = (state: AppState) => state.emojiStats

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

