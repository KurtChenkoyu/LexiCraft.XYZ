/**
 * CACHING STRATEGY (IMMUTABLE - DO NOT CHANGE):
 * 
 * This file follows the "Last War" caching approach:
 * - Bootstrap runs at /start BEFORE routing
 * - Loads ALL critical data from IndexedDB → Zustand
 * - Shows progress bar to user (hides the "Time Tax")
 * - After bootstrap, app renders instantly (no spinners)
 * 
 * See: .cursorrules - "Caching & Bootstrap Strategy"
 */

/**
 * Bootstrap Service
 * 
 * The "Loading Screen" that runs at /start.
 * Pre-loads all critical data before the user enters the app.
 * 
 * Flow:
 * 1. User logs in → redirected to /start
 * 2. Bootstrap runs (loads IndexedDB → Zustand)
 * 3. Shows progress bar (0% → 100%)
 * 4. Redirects to appropriate home page
 * 5. Rest of app renders instantly from Zustand
 */

import { useAppStore, type LearnerProfile } from '@/stores/useAppStore'
import { downloadService, getLearnerMineBlocksKey } from './downloadService'
import { localStore } from '@/lib/local-store'
import { vocabularyLoader } from '@/lib/vocabularyLoader'

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
import { progressApi, type UserProgressResponse, type BlockProgress } from '@/services/progressApi'
import { type Block } from '@/types/mine'

// ============================================
// Types
// ============================================

export interface BootstrapProgress {
  step: string
  completed: number
  total: number
  percentage: number
}

export type BootstrapCallback = (progress: BootstrapProgress) => void

interface BootstrapResult {
  success: boolean
  error?: string
  redirectTo?: string
}

// ============================================
// Helpers
// ============================================

/**
 * Build a per-learner snapshot from IndexedDB and write it into learnerCache.
 * Optionally also hydrates top-level state if this learner is currently active.
 *
 * This keeps ALL learners \"alive\" in memory while only projecting one learner
 * into the active view at a time.
 */
export async function buildLearnerSnapshotFromIndexedDB(learnerId: string) {
  if (!learnerId) return

  const storeState = useAppStore.getState()

  // 1) Load progress + SRS levels from IndexedDB (learner-scoped)
  const progressMap = await localStore.getAllProgress(learnerId)
  const srsLevelsMap = await localStore.getSRSLevels(learnerId)

  // 2) Compute aggregate progress stats (per learner, all packs)
  const solidCount = Array.from(progressMap.values()).filter(
    (s) => s === 'solid' || s === 'mastered' || s === 'verified',
  ).length
  const hollowCount = Array.from(progressMap.values()).filter(
    (s) => s === 'hollow' || s === 'learning' || s === 'pending',
  ).length

  const progressStats = {
    total_discovered: solidCount + hollowCount,
    solid_count: solidCount,
    hollow_count: hollowCount,
    raw_count: 0, // Will be derived by views when needed
  }

  // 3) Compute emoji-only progress snapshot if emoji pack is active
  // Always initialize as empty Maps (not null) for consistent pipeline
  let emojiProgressMap: Map<string, string> = new Map<string, string>()
  let emojiSRSMap: Map<string, string> = new Map<string, string>()
  let emojiMasteredWords: any[] = []
  let emojiStats: {
    totalWords: number
    collectedWords: number
    masteredWords: number
    learningWords: number
  } | null = null

  if (storeState.activePack?.id === 'emoji_core') {
    try {
      const { packLoader } = await import('@/lib/pack-loader')
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

        // Calculate emoji stats + mastered list
        const mastered = packData.vocabulary.filter((word) => {
          const status = emojiProgressMap.get(word.sense_id)
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
        console.warn('⚠️ Failed to build emoji snapshot from IndexedDB (non-critical):', error)
      }
    }
  }

  // 4) Load collectedWords from IndexedDB
  let collectedWords: import('@/stores/useAppStore').CollectedWord[] = await localStore.getCollectedWords(learnerId)

  // If empty, build from progressMap (backward compatibility)
  if (collectedWords.length === 0 && progressMap.size > 0 && storeState.activePack?.id === 'emoji_core') {
    try {
      const { packLoader } = await import('@/lib/pack-loader')
      const packData = await packLoader.loadPack('emoji_core')
      
      if (packData) {
        const emojiSenseIds = new Set(packData.vocabulary.map(w => w.sense_id))
        const built: import('@/stores/useAppStore').CollectedWord[] = []
        
        progressMap.forEach((status, senseId) => {
          if (status !== 'raw' && emojiSenseIds.has(senseId)) {
            const wordData = packData.vocabulary.find(w => w.sense_id === senseId)
            if (wordData) {
              const masteryLevel = srsLevelsMap.get(senseId) || 'learning'
              built.push({
                ...wordData,
                collectedAt: Date.now(),  // Will be updated from backend if available
                status: status as 'hollow' | 'solid' | 'mastered',
                masteryLevel: masteryLevel as 'learning' | 'familiar' | 'known' | 'mastered' | 'burned'
              })
            }
          }
        })
        
        // Save to IndexedDB for future loads
        await localStore.importCollectedWords(learnerId, built)
        collectedWords = built
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Failed to build collectedWords from progressMap (non-critical):', error)
      }
    }
  }

  // 5) Write into learnerCache and optionally hydrate active view
  useAppStore.setState((prev) => {
    const existing = prev.learnerCache[learnerId]
    const isActive = prev.activeLearner?.id === learnerId

    const nextCacheEntry = {
      miningQueue: existing?.miningQueue ?? [],
      emojiProgress: emojiProgressMap, // Always a Map (never null) from above
      emojiSRSLevels: emojiSRSMap, // Always a Map (never null) from above
      progress: progressStats,
      dueCards: existing?.dueCards ?? [],
      collectedWords: collectedWords,
      currencies: existing?.currencies ?? null,
      rooms: existing?.rooms ?? [],
      timestamp: Date.now(),
    }

    const learnerCache = {
      ...prev.learnerCache,
      [learnerId]: nextCacheEntry,
    }

    if (!isActive) {
      return {
        learnerCache,
      }
    }

    // If this learner is active, also project snapshot into top-level slices
    // Ensure Maps are always Maps (never null) for consistent pipeline
    return {
      learnerCache,
      progress: progressStats,
      emojiProgress: emojiProgressMap, // Always a Map (never null) from above
      emojiSRSLevels: emojiSRSMap, // Always a Map (never null) from above
      emojiMasteredWords: emojiMasteredWords.length > 0 ? emojiMasteredWords : prev.emojiMasteredWords,
      emojiStats: emojiStats ?? prev.emojiStats,
      collectedWords: collectedWords,
    }
  })
}

// ============================================
// Bootstrap Steps
// ============================================

const BOOTSTRAP_STEPS = [
  'Loading profile...',
  'Loading children...',
  'Loading children summaries...',
  'Loading wallet...',
  'Loading progress...',
  'Loading achievements...',
  'Loading goals...',
  'Loading currencies...',
  'Loading rooms...',
  'Loading vocabulary...',
  'Preparing mining area...',
  'Loading due cards...',       // For Verification page
  'Loading leaderboard...',     // For Ranking page
  'Preloading pages...',        // Preload page JS bundles
  'Finalizing...',
]

// ============================================
// Bootstrap Function
// ============================================

/**
 * Bootstrap the application
 * 
 * Call this at /start before routing to home page.
 * Returns redirect path based on user role.
 * 
 * @param userId - The authenticated user ID
 * @param onProgress - Optional callback for progress updates
 * @returns Promise with redirect path or error
 */
export async function bootstrapApp(
  userId: string,
  onProgress?: BootstrapCallback
): Promise<BootstrapResult> {
  const store = useAppStore.getState()
  
  let currentStep = 0
  const totalSteps = BOOTSTRAP_STEPS.length

  const updateProgress = (step: string) => {
    currentStep++
    const progress: BootstrapProgress = {
      step,
      completed: currentStep,
      total: totalSteps,
      percentage: Math.round((currentStep / totalSteps) * 100),
    }
    onProgress?.(progress)
  }

  try {
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 Bootstrap: Starting app initialization...')
    }

    // ============================================
    // Step 1: Load User Profile
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[0])
    const profile = await downloadService.getProfile()
    
    // FAIL FAST: Cannot proceed without user identity
    // This prevents wasting time loading vocabulary, rooms, etc. if profile is missing
    if (!profile) {
      console.error('⚠️ Bootstrap: Critical - Profile not loaded')
      throw new Error('Failed to load user profile. Please check your connection.')
    }

    store.setUser(profile)
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ Bootstrap: Loaded user profile')
    }

    // ============================================
    // Step 2: Load Children (if parent)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[1])
    const children = await downloadService.getChildren()
    if (children && children.length > 0) {
      store.setChildren(children)
      // Auto-select first child if none selected
      const savedChildId = typeof window !== 'undefined' 
        ? localStorage.getItem('lexicraft_selected_child') 
        : null
      const validChild = savedChildId && children.find(c => c.id === savedChildId)
      store.setSelectedChild(validChild ? savedChildId : children[0].id)
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Loaded children')
      }
    } else {
      store.setChildren([])
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: No children (learner account)')
      }
    }

    // ============================================
    // Step 2b: Load Children Summaries (if parent)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[2])
    if (children && children.length > 0) {
      try {
        if (process.env.NODE_ENV === 'development') {
          console.log(`📊 Bootstrap: Loading summaries for ${children.length} children...`)
        }
        const childrenSummaries = await downloadService.getChildrenSummaries()
        if (process.env.NODE_ENV === 'development') {
          console.log(`📊 Bootstrap: Got ${childrenSummaries?.length || 0} children summaries from service`)
          console.log(`📊 Bootstrap: Data =`, childrenSummaries)
        }
        
        if (childrenSummaries && childrenSummaries.length > 0) {
          store.setChildrenSummaries(childrenSummaries)
          if (process.env.NODE_ENV === 'development') {
            console.log(`✅ Bootstrap: Called store.setChildrenSummaries with ${childrenSummaries.length} items`)
            // Verify it was set
            const verify = useAppStore.getState().childrenSummaries
            console.log(`✅ Bootstrap: Store now has ${verify.length} children summaries`)
          }
        } else {
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: Children summaries returned empty array')
          }
          // Set empty array so UI knows we tried
          store.setChildrenSummaries([])
        }
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('❌ Bootstrap: Failed to load children summaries:', error)
        }
        // Set empty array on error so UI shows appropriate message
        store.setChildrenSummaries([])
      }
    } else {
      if (process.env.NODE_ENV === 'development') {
        console.log('⏭️  Bootstrap: Skipping children summaries (no children or not parent)')
      }
    }

      // Step 2c: Load Learners Summaries (NEW - learner-scoped XP)
      // CRITICAL: This must run for ALL users (not just those with children) because it includes the parent's own profile
      try {
        if (process.env.NODE_ENV === 'development') {
          console.log('📊 Bootstrap: Loading learners summaries (learner-scoped)...')
        }
        // Force refresh on bootstrap to ensure we get fresh data
        const learnersSummaries = await downloadService.getLearnersSummaries(true)
      if (process.env.NODE_ENV === 'development') {
        console.log(`📊 Bootstrap: Got ${learnersSummaries?.length || 0} learners summaries from service`)
      }
      
      if (learnersSummaries && learnersSummaries.length > 0) {
        // Normalize data to ensure weekly_xp and monthly_xp are present (backward compatibility)
        const normalizedSummaries = learnersSummaries.map(s => ({
          ...s,
          weekly_xp: s.weekly_xp ?? 0,
          monthly_xp: s.monthly_xp ?? 0,
        }))
        store.setLearnersSummaries(normalizedSummaries)
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${learnersSummaries.length} learners summaries`)
          // Verify it was set
          const verify = useAppStore.getState().learnersSummaries
          console.log(`✅ Bootstrap: Store now has ${verify.length} learners summaries`)
        }
      } else {
        if (process.env.NODE_ENV === 'development') {
          console.warn('⚠️ Bootstrap: Learners summaries returned empty array')
        }
        store.setLearnersSummaries([])
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Bootstrap: Failed to load learners summaries:', error)
      }
      store.setLearnersSummaries([])
    }

    // ============================================
    // Step 2c: Load Learners (Multi-Profile System - NEW)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[2]) // Reuse step index, will update later
    
    // Try to load learners with timeout protection
    let learners: LearnerProfile[] | undefined
    try {
      // Add explicit timeout wrapper (10s) to prevent hanging
      learners = await Promise.race([
        downloadService.getLearners(),
        new Promise<undefined>((_, reject) =>
          setTimeout(() => reject(new Error('getLearners timeout')), 20000)
        )
      ])
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: getLearners timed out or failed:', error)
      }
      learners = undefined
    }
    
    // If still no learners, try expired cache directly (double fallback)
    if (!learners || learners.length === 0) {
      try {
        const expiredCache = await localStore.getCacheIgnoreExpiry<LearnerProfile[]>('learners')
        if (expiredCache && expiredCache.length > 0) {
          learners = expiredCache
          console.log(`✅ Bootstrap: Using expired cache for learners (${expiredCache.length} learners)`)
          // Re-cache it (refresh TTL)
          await localStore.setCache('learners', expiredCache, 30 * 24 * 60 * 60 * 1000) // CACHE_TTL.MEDIUM
        }
      } catch (cacheError) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('⚠️ Bootstrap: Failed to check expired cache:', cacheError)
        }
      }
    }
    
    if (learners && learners.length > 0) {
      store.setLearners(learners)
      
      // Auto-select parent's learner profile as default
      const parentLearner = learners.find((l: LearnerProfile) => l.is_parent_profile)
      if (parentLearner) {
        store.setActiveLearner(parentLearner)
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${learners.length} learners, set activeLearner to parent`)
        }
      } else {
        // Fallback: use first learner
        store.setActiveLearner(learners[0])
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${learners.length} learners, set activeLearner to first learner`)
        }
      }
    } else {
      // No learners found (first-time user or all fallbacks failed)
      store.setLearners([])
      if (process.env.NODE_ENV === 'development') {
        console.log('⚠️ Bootstrap: No learners found - user may need onboarding')
      }
    }

    // ============================================
    // Step 2d: Build Initial learnerCache Snapshots from IndexedDB (IMMEDIATE)
    // ============================================
    // Build snapshots immediately so activeLearner has data instantly
    // This is fast (~10ms per learner) and doesn't block bootstrap
    // CRITICAL: This enables instant learner switching (switchLearner checks learnerCache first)
    if (learners && learners.length > 0) {
      try {
        // Build snapshots for all learners in parallel (fast, IndexedDB only)
        await Promise.all(
          learners.map(learner => 
            buildLearnerSnapshotFromIndexedDB(learner.id).catch(error => {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`⚠️ Bootstrap: Failed to build initial snapshot for ${learner.display_name}:`, error)
              }
              // Don't throw - continue with other learners
            })
          )
        )
        
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Built initial learnerCache snapshots from IndexedDB for ${learners.length} learners`)
        }
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('⚠️ Bootstrap: Failed to build initial snapshots (non-critical):', error)
        }
        // Don't throw - bootstrap can continue without snapshots
      }
    }

    // Pre-load dueCards for all learners in background (non-blocking)
    // This ensures IndexedDB cache is populated for instant switching
    if (learners && learners.length > 0) {
      Promise.allSettled(
        learners.map(learner => 
          downloadService.getLearnerDueCards(learner.id).catch(() => [])
        )
      ).then(results => {
        const loadedCount = results.filter(r => r.status === 'fulfilled' && r.value && r.value.length > 0).length
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Pre-loaded dueCards for ${loadedCount}/${learners.length} learners`)
        }
      })
      // Don't await - this is non-blocking background pre-load
    }

    // ============================================
    // Step 3: Load Wallet/Balance
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[3])
    // Balance is fetched per-child, so we'll load learner profile instead
    const learnerProfile = await downloadService.getLearnerProfile()
    if (learnerProfile) {
      store.setLearnerProfile(learnerProfile)
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Loaded learner profile')
      }
    }

    // ============================================
    // Step 4: Sync Progress from API (Background, Non-Blocking)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[4])
    // Start API sync in background - don't block bootstrap
    // Snapshots were already built from IndexedDB in Step 2d, so activeLearner has data
    try {
      const allLearners = store.learners
      if (allLearners.length > 0) {
        // Sync progress for ALL learners in parallel (background, non-blocking)
        Promise.allSettled(
          allLearners.map(learner => 
            Promise.race([
              downloadService.syncProgress(learner.id),
              new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 60000))
            ])
            .then(() => {
              // After sync completes, rebuild snapshot from fresh IndexedDB data
              return buildLearnerSnapshotFromIndexedDB(learner.id)
            })
            .catch(error => {
              // Timeout or error - keep existing snapshot from IndexedDB
              if (process.env.NODE_ENV === 'development') {
                console.warn(`⚠️ Bootstrap: Failed to sync progress for ${learner.display_name}:`, error)
              }
              // Don't throw - keep existing snapshot
            })
          )
        ).then(results => {
          const successCount = results.filter(r => r.status === 'fulfilled').length
          if (process.env.NODE_ENV === 'development') {
            console.log(`✅ Bootstrap: Background progress sync complete (${successCount}/${allLearners.length} learners)`)
          }
        })
        // Don't await - this is background sync, bootstrap continues immediately
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to start background progress sync (non-critical):', error)
      }
      // Don't throw - bootstrap continues with IndexedDB snapshots
    }

    // ============================================
    // Step 5: Load Achievements
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[5])
    const achievements = await downloadService.getAchievements()
    if (achievements) {
      store.setAchievements(achievements)
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Loaded achievements')
      }
    }

    // ============================================
    // Step 6: Load Goals
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[6])
    const goals = await downloadService.getGoals()
    if (goals) {
      store.setGoals(goals)
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Loaded goals')
      }
    }

    // ============================================
    // Step 7: Load Currencies (for Build page)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[7])
    if (process.env.NODE_ENV === 'development') {
      console.log('🧪 Bootstrap: Skipping currencies load for Build MVP')
    }

    // ============================================
    // Step 8: Load Rooms (for Build page)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[8])
    if (process.env.NODE_ENV === 'development') {
      console.log('🧪 Bootstrap: Skipping rooms load for Build MVP')
    }

    // ============================================
    // Step 9: Load Vocabulary (Conditional based on active pack)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[9])
    
    // Check active pack FIRST to decide which vocabulary to load
    const activePackForVocab = store.activePack
    const isEmojiPackActive = activePackForVocab?.id === 'emoji_core'
    
    if (isEmojiPackActive) {
      // 🎯 MVP Mode: Skip legacy vocabulary loading entirely
      // The emoji pack is self-contained in its JSON file
      if (process.env.NODE_ENV === 'development') {
        console.log('🎯 Bootstrap: Skipping legacy vocabulary (emoji pack active)')
        console.log('✅ Bootstrap: Using emoji pack (200 words) instead of legacy (10k+)')
      }
      
      // Pre-load the emoji pack into memory for instant access
      const { packLoader } = await import('@/lib/pack-loader')
      const packData = await packLoader.loadPack('emoji_core')
      if (packData && packData.vocabulary) {
        store.setEmojiVocabulary(packData.vocabulary)
        // Also cache in IndexedDB for offline access
        await localStore.setCache('emoji_vocabulary', packData.vocabulary, 30 * 24 * 60 * 60 * 1000)
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded emoji vocabulary (${packData.vocabulary.length} words) into Zustand`)
        }
      }
    } else {
      // Legacy Mode: Load full Taiwan MOE vocabulary
      if (process.env.NODE_ENV === 'development') {
        console.log('⏳ Bootstrap: Ensuring legacy vocabulary is ready...')
      }

      // Subscribe to progress updates for UI
      const unsubscribe = vocabularyLoader.onStatusChange((status) => {
        if (process.env.NODE_ENV === 'development') {
          switch (status.state) {
            case 'checking':
              console.log('🔍 Bootstrap: Checking vocabulary cache...')
              break
            case 'downloading':
              console.log(`📥 Bootstrap: Downloading vocabulary... ${status.progress}%`)
              break
            case 'parsing':
              console.log('⚙️ Bootstrap: Parsing vocabulary data...')
              break
            case 'inserting':
              console.log(`💾 Bootstrap: Storing vocabulary... ${status.current}/${status.total}`)
              break
            case 'cached':
              console.log(`✅ Bootstrap: Vocabulary cached (${status.count} senses)`)
              break
            case 'complete':
              console.log(`✅ Bootstrap: Vocabulary ready (${status.count} senses)`)
              break
            case 'error':
              console.error(`❌ Bootstrap: Vocabulary error - ${status.error}`)
              break
          }
        }
      })

      try {
        const vocabResult = await vocabularyLoader.ensureReady()
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Vocabulary confirmed (${vocabResult.source}, ${vocabResult.count} senses)`)
        }
      } catch (vocabError) {
        unsubscribe()
        console.error('❌ Bootstrap: Vocabulary failed to load:', vocabError)
        throw new Error(`Vocabulary failed to load: ${vocabError instanceof Error ? vocabError.message : 'Unknown error'}`)
      } finally {
        unsubscribe()
      }
    }

    // ============================================
    // Step 9b: Calculate Emoji Stats (if emoji pack active)
    // ============================================
    if (store.activePack?.id === 'emoji_core' && store.emojiVocabulary && store.emojiProgress) {
      if (process.env.NODE_ENV === 'development') {
        console.log('🎯 Bootstrap: Calculating emoji stats...')
      }
      try {
        const emojiVocab = store.emojiVocabulary
        const emojiProgressMap = store.emojiProgress
        
        // Pre-filter mastered words
        const masteredWords = emojiVocab.filter(word => {
          const status = emojiProgressMap.get(word.sense_id)
          return status === 'solid' || status === 'mastered'
        })
        store.setEmojiMasteredWords(masteredWords)
        
        // Calculate stats
        const totalWords = emojiVocab.length
        const collectedWords = emojiProgressMap.size
        const masteredWordsCount = masteredWords.length
        const learningWordsCount = Array.from(emojiProgressMap.values())
          .filter(s => s === 'hollow' || s === 'learning').length
        
        store.setEmojiStats({
          totalWords,
          collectedWords,
          masteredWords: masteredWordsCount,
          learningWords: learningWordsCount
        })
        
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Calculated emoji stats (${masteredWordsCount} mastered, ${learningWordsCount} learning)`)
        }
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('⚠️ Bootstrap: Failed to calculate emoji stats (non-critical):', error)
        }
      }
    }

    // ============================================
    // Verify Emoji Vocabulary is Loaded (before Step 10)
    // ============================================
    if (store.activePack?.id === 'emoji_core' && !store.emojiVocabulary) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: emojiVocabulary not loaded in Step 9, attempting to load now...')
      }
      const { packLoader } = await import('@/lib/pack-loader')
      const packData = await packLoader.loadPack('emoji_core')
      if (packData && packData.vocabulary) {
        store.setEmojiVocabulary(packData.vocabulary)
        await localStore.setCache('emoji_vocabulary', packData.vocabulary, 30 * 24 * 60 * 60 * 1000)
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ Bootstrap: Loaded emoji vocabulary (fallback)')
        }
      }
    }

    // ============================================
    // Steps 10-12: Parallel Page Data Loading
    // ============================================
    // Capture activeLearnerId at start (race condition protection)
    const activeLearnerId = store.activeLearner?.id

    // Run all page data loading in parallel (they're independent)
    updateProgress('Preloading pages...') // Combined step message

    const [mineResult, dueCardsResult, leaderboardResult] = await Promise.all([
      // Step 10: Prepare mining area (now parallelized internally)
      (async () => {
        try {
          // Verify learner hasn't changed before proceeding
          if (useAppStore.getState().activeLearner?.id !== activeLearnerId) {
            return { success: false, reason: 'learner_switched' }
    }

    // ============================================
    // Step 10: Prepare Mining Area (Starter Pack)
    // ============================================
    if (process.env.NODE_ENV === 'development') {
      console.log('⛏️ Bootstrap: Preparing mining area...')
    }
    
      // Check if emoji pack is active (default for MVP)
      const activePack = store.activePack
      const isEmojiPack = activePack?.id === 'emoji_core'
      
      if (isEmojiPack) {
            // ⚡ FAST PATH: Check Zustand first
            const existingBlocks = store.mineBlocks
            if (existingBlocks && existingBlocks.length > 0 && existingBlocks.some(b => b.emoji)) {
              store.setMineDataLoaded(true)
        if (process.env.NODE_ENV === 'development') {
                console.log(`⚡ Bootstrap: Mine already has ${existingBlocks.length} emoji blocks in Zustand`)
              }
            } else {
              // Check IndexedDB cache (learner-scoped)
              const currentLearnerId = store.activeLearner?.id
              if (currentLearnerId) {
                const cachedBlocks = await localStore.getCache<Block[]>(
                  getLearnerMineBlocksKey(currentLearnerId)
                )
                if (cachedBlocks && cachedBlocks.length > 0) {
                  store.setMineBlocks(cachedBlocks)
                  store.setMineDataLoaded(true)
                  if (process.env.NODE_ENV === 'development') {
                    console.log(`⚡ Bootstrap: Loaded ${cachedBlocks.length} emoji blocks from IndexedDB cache`)
                  }
                } else {
                  // Build blocks with status from emojiProgress
                  if (process.env.NODE_ENV === 'development') {
                    console.log('🎯 Bootstrap: Building emoji blocks from vocabulary...')
        }
        
        const { packLoader } = await import('@/lib/pack-loader')
        const emojiVocab = await packLoader.getStarterItems('emoji_core', 50)
                  const emojiProgress = store.emojiProgress || new Map<string, string>()
        
        const emojiBlocks = emojiVocab.map(item => ({
          sense_id: item.sense_id,
          word: item.word,
          definition_preview: item.definition_zh,
          rank: item.difficulty,  // Changed from tier to rank
          base_xp: 10 * item.difficulty,
          connection_count: 0,
          total_value: 100,
          status: (emojiProgress?.get(item.sense_id) || 'raw') as 'raw' | 'hollow' | 'solid',
          emoji: item.emoji,
        }))
        
        store.setMineBlocks(emojiBlocks)
        store.setMineDataLoaded(true)
                  
                  // Cache to IndexedDB (learner-scoped)
                  if (currentLearnerId) {
                    await localStore.setCache(
                      getLearnerMineBlocksKey(currentLearnerId),
                      emojiBlocks,
                      30 * 24 * 60 * 60 * 1000 // 30 days TTL
                    )
                  }
        
        if (process.env.NODE_ENV === 'development') {
                    console.log(`✅ Bootstrap: Built and cached ${emojiBlocks.length} emoji blocks`)
                  }
                }
              } else {
                // No active learner - build blocks without caching
                if (process.env.NODE_ENV === 'development') {
                  console.log('🎯 Bootstrap: Building emoji blocks (no active learner)')
                }
                
                const { packLoader } = await import('@/lib/pack-loader')
                const emojiVocab = await packLoader.getStarterItems('emoji_core', 50)
                const emojiProgress = store.emojiProgress || new Map<string, string>()
                
                const emojiBlocks = emojiVocab.map(item => ({
                  sense_id: item.sense_id,
                  word: item.word,
                  definition_preview: item.definition_zh,
                  rank: item.difficulty,  // Changed from tier to rank
                  base_xp: 10 * item.difficulty,
                  connection_count: 0,
                  total_value: 100,
                  status: (emojiProgress?.get(item.sense_id) || 'raw') as 'raw' | 'hollow' | 'solid',
                  emoji: item.emoji,
                }))
                
                store.setMineBlocks(emojiBlocks)
                store.setMineDataLoaded(true)
                
                if (process.env.NODE_ENV === 'development') {
                  console.log(`✅ Bootstrap: Built ${emojiBlocks.length} emoji blocks (not cached - no active learner)`)
                }
              }
        }
      } else {
        // Legacy vocabulary flow
        const existingBlocks = store.mineBlocks
        if (existingBlocks && existingBlocks.length > 0) {
          if (process.env.NODE_ENV === 'development') {
            console.log(`⚡ Bootstrap: Mine already has ${existingBlocks.length} blocks`)
          }
        } else {
          // Need to generate starter pack
          const { vocabulary } = await import('@/lib/vocabulary')
          const { progressApi } = await import('@/services/progressApi')
        
        // FIRST: Always load from IndexedDB (instant, offline-first)
        // This ensures we have progress data even if API times out
        // Note: We use a Map for O(1) lookup when building blocks
        let progressMap = new Map<string, string>() // senseId -> status
              const currentLearnerId = store.activeLearner?.id
              if (currentLearnerId) {
                const localProgressMap = await localStore.getAllProgress(currentLearnerId)
          if (localProgressMap.size > 0) {
            progressMap = localProgressMap
            if (process.env.NODE_ENV === 'development') {
              console.log(`📦 Bootstrap: Loaded ${progressMap.size} progress items from IndexedDB (instant)`)
            }
          }
          
          // THEN: Try to fetch fresh progress from backend (parallel, non-blocking for UI)
          try {
            const progressData = await Promise.race([
                    progressApi.getUserProgress(currentLearnerId),
              new Promise<null>((_, reject) => setTimeout(() => reject(new Error('timeout')), 60000))
            ]) as UserProgressResponse | null
            
            if (progressData?.progress) {
              // Update progressMap with fresh data from backend
              progressData.progress.forEach((p: BlockProgress) => {
                let status: 'raw' | 'hollow' | 'solid' = 'raw'
                if (p.status === 'verified' || p.status === 'mastered' || p.status === 'solid') {
                  status = 'solid'
                } else if (p.status === 'pending' || p.status === 'learning' || p.status === 'hollow') {
                  status = 'hollow'
                }
                progressMap.set(p.sense_id, status)
              })
              if (process.env.NODE_ENV === 'development') {
                console.log(`📊 Bootstrap: Got ${progressData.progress.length} fresh progress items from backend`)
              }
              
              // Save to IndexedDB for offline access (background, don't block)
              // Note: importProgress handles bulk insert more efficiently
                    localStore.importProgress(currentLearnerId, progressData.progress)
                .catch(err => console.warn('Failed to save progress to IndexedDB:', err))
            }
          } catch (err) {
            if (process.env.NODE_ENV === 'development') {
              console.warn('⚠️ Bootstrap: Backend progress timeout, using IndexedDB cache')
            }
            // Already have IndexedDB data from progressMap - no action needed
          }
        } else {
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: No activeLearner, using empty progressMap')
          }
        }
        
        // Build starter pack from user's progress (not random!)
        if (process.env.NODE_ENV === 'development') {
          console.log('🎲 Bootstrap: Building starter pack from user progress...')
        }
        
        // First, try to load cached starter pack IDs
        const cachedIds = await localStore.getCache<string[]>('starter_pack_ids')
        let blocks: Block[] = []
        
        // Check if cached IDs need to be invalidated
        // If we have progress words that aren't in cached IDs, regenerate
        const progressSenseIds = new Set(progressMap.keys())
        const cachedIdsSet = new Set(cachedIds || [])
        const hasUnmatchedProgress = progressMap.size > 0 && 
          Array.from(progressSenseIds).some(id => !cachedIdsSet.has(id))
        
        if (cachedIds && cachedIds.length > 0 && !hasUnmatchedProgress) {
          // Rebuild from cached IDs (ensures consistency)
          if (process.env.NODE_ENV === 'development') {
            console.log(`📦 Bootstrap: Rebuilding from ${cachedIds.length} cached IDs (progressMap has ${progressMap.size} items)`)
          }
          
                // ✅ Parallelize with error handling
                const detailPromises = cachedIds.map(senseId => 
                  vocabulary.getBlockDetail(senseId).catch(err => {
                    if (process.env.NODE_ENV === 'development') {
                      console.warn(`Failed to load block detail for ${senseId}:`, err)
                    }
                    return null
                  })
                )
                const detailResults = await Promise.allSettled(detailPromises)
                for (const result of detailResults) {
                  if (result.status === 'fulfilled' && result.value) {
                    const detail = result.value
              // Check progress status from progressMap (O(1) lookup)
                    const progressStatus = progressMap.get(detail.sense_id)
              let status: 'raw' | 'hollow' | 'solid' = 'raw'
              if (progressStatus) {
                status = progressStatus as 'raw' | 'hollow' | 'solid'
              }
              
              blocks.push({
                sense_id: detail.sense_id,
                word: detail.word,
                definition_preview: (detail.definition_en || '').slice(0, 100),
                rank: detail.rank,  // Use rank (word complexity)
                base_xp: detail.base_xp,
                connection_count: detail.connection_count,
                total_value: detail.total_value,
                status,
              })
            }
          }
        } else if (hasUnmatchedProgress) {
          // Progress words don't match cached IDs - invalidate cache
          if (process.env.NODE_ENV === 'development') {
            console.log(`⚠️ Bootstrap: Cached starter pack doesn't include user progress - regenerating`)
          }
          await localStore.setCache('starter_pack_ids', null, 0) // Invalidate
        }
        
        // If no cached IDs or blocks couldn't be built, generate fresh but include user's progress words
        if (blocks.length === 0) {
          if (process.env.NODE_ENV === 'development') {
            console.log('🎲 Bootstrap: No cached starter pack, generating from progress...')
          }
          
          // Start with user's progress words (from progressMap)
                // ✅ Parallelize with error handling
                const progressEntries = Array.from(progressMap.entries())
                const progressDetailPromises = progressEntries.map(
                  ([senseId]) => vocabulary.getBlockDetail(senseId).catch(err => {
                    if (process.env.NODE_ENV === 'development') {
                      console.warn(`Failed to load progress block detail for ${senseId}:`, err)
                    }
                    return null
                  })
                )
                const progressResults = await Promise.allSettled(progressDetailPromises)
                // Match details with status from progressMap
                progressResults.forEach((result, index) => {
                  if (result.status === 'fulfilled' && result.value) {
                    const [senseId, status] = progressEntries[index]
                    const detail = result.value
              blocks.push({
                sense_id: detail.sense_id,
                word: detail.word,
                definition_preview: (detail.definition_en || '').slice(0, 100),
                rank: detail.rank,  // Use rank (word complexity)
                base_xp: detail.base_xp,
                connection_count: detail.connection_count,
                total_value: detail.total_value,
                status: status as 'raw' | 'hollow' | 'solid',
              })
            }
                })
          
          // If we don't have enough blocks, add some random ones
          if (blocks.length < 50) {
            const randomBlocks = await vocabulary.getStarterPack(50 - blocks.length)
            blocks.push(...randomBlocks)
          }
          
          // Save IDs for next time
          const blockIds = blocks.map(b => b.sense_id)
          await localStore.setCache('starter_pack_ids', blockIds, 30 * 24 * 60 * 60 * 1000)
        }
        
        if (blocks.length > 0) {
          // Save to Zustand
          store.setMineBlocks(blocks)
          store.setMineDataLoaded(true)
          
          if (process.env.NODE_ENV === 'development') {
            const hollowCount = blocks.filter(b => b.status === 'hollow').length
            const solidCount = blocks.filter(b => b.status === 'solid').length
            console.log(`✅ Bootstrap: Mine prepared with ${blocks.length} blocks (${hollowCount} hollow, ${solidCount} solid)`)
          }
        }
        
        // Hydrate mining queue from progressMap (hollow items)
        const hollowSenseIds = Array.from(progressMap.entries())
          .filter(([_, status]) => status === 'hollow')
          .map(([senseId, _]) => senseId)
        
        if (hollowSenseIds.length > 0) {
          const hollowItems: { senseId: string; word: string; addedAt: number }[] = []
          
          // Get words for the queued items
                // ✅ Parallelize with error handling
                const queueDetailPromises = hollowSenseIds.map(senseId => 
                  vocabulary.getBlockDetail(senseId).catch(err => {
                    if (process.env.NODE_ENV === 'development') {
                      console.warn(`Failed to load queue block detail for ${senseId}:`, err)
                    }
                    return null
                  })
                )
                const queueResults = await Promise.allSettled(queueDetailPromises)
                // Build queue items
                queueResults.forEach((result, index) => {
                  if (result.status === 'fulfilled' && result.value) {
                    const detail = result.value
                    const senseId = hollowSenseIds[index]
              hollowItems.push({
                senseId,
                word: detail.word,
                addedAt: Date.now()
              })
            }
                })
          
          // Save to Zustand
          const currentQueue = useAppStore.getState().miningQueue
          if (currentQueue.length === 0 && hollowItems.length > 0) {
            // Only set if queue is empty
            useAppStore.setState({ miningQueue: hollowItems })
            await localStore.setCache('mining_queue', hollowItems, 30 * 24 * 60 * 60 * 1000)
            if (process.env.NODE_ENV === 'development') {
              console.log(`⚡ Bootstrap: Mining queue hydrated with ${hollowItems.length} items`)
            }
          }
        }
        }
          }
          
          // Verify again before updating Zustand
          if (useAppStore.getState().activeLearner?.id !== activeLearnerId) {
            return { success: false, reason: 'learner_switched' }
          }
          
          return { success: true }
        } catch (err) {
    if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: Failed to prepare mine (non-critical):', err)
    }
          return { success: false }
        }
      })(),
    
      // Step 11: Load due cards
      (async () => {
    try {
          // Use captured activeLearnerId (may be null if no learner)
      if (activeLearnerId) {
            // Verify learner hasn't changed
            if (useAppStore.getState().activeLearner?.id !== activeLearnerId) {
              return { success: false, reason: 'learner_switched' }
            }
            
        const dueCards = await downloadService.getLearnerDueCards(activeLearnerId)
            
            // Verify again before updating Zustand
            if (useAppStore.getState().activeLearner?.id !== activeLearnerId) {
              return { success: false, reason: 'learner_switched' }
            }
            
        if (dueCards && dueCards.length > 0) {
          store.setDueCards(dueCards)
          if (process.env.NODE_ENV === 'development') {
            console.log(
              `✅ Bootstrap: Loaded ${dueCards.length} due cards for learner ${activeLearnerId}`,
            )
          }
        } else if (process.env.NODE_ENV === 'development') {
          console.log('ℹ️ Bootstrap: No due cards found for active learner (initial state)')
        }
      } else if (process.env.NODE_ENV === 'development') {
        console.log('ℹ️ Bootstrap: Skipping due cards load (no active learner)')
      }
          return { success: true }
        } catch (err) {
      if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: Failed to load due cards (non-critical):', err)
          }
          return { success: false }
        }
      })(),
      
      // Step 12: Load leaderboard (doesn't need activeLearner)
      (async () => {
    try {
      const { leaderboardsApi } = await import('@/services/gamificationApi')
      const [entries, userRank] = await Promise.all([
        leaderboardsApi.getGlobal('weekly', 50, 'xp'),
        leaderboardsApi.getRank('weekly', 'xp')
      ])
      if (entries && entries.length > 0) {
            store.setLeaderboardData({ entries, userRank, period: 'weekly', metric: 'xp' })
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${entries.length} leaderboard entries`)
        }
      }
          return { success: true }
        } catch (err) {
      if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: Failed to load leaderboard (non-critical):', err)
          }
          return { success: false }
        }
      })(),
    ])

    // Update progress for each step
    updateProgress(BOOTSTRAP_STEPS[10])
    updateProgress(BOOTSTRAP_STEPS[11])
    updateProgress(BOOTSTRAP_STEPS[12])
    if (process.env.NODE_ENV === 'development') {
      console.log('⛏️ Bootstrap: Preparing mining area...')
    }
    
    try {
      // Check if emoji pack is active (default for MVP)
      const activePack = store.activePack
      const isEmojiPack = activePack?.id === 'emoji_core'
      
      if (isEmojiPack) {
        // ⚡ FAST PATH: Check Zustand first
        const existingBlocks = store.mineBlocks
        if (existingBlocks && existingBlocks.length > 0 && existingBlocks.some(b => b.emoji)) {
          store.setMineDataLoaded(true)
          if (process.env.NODE_ENV === 'development') {
            console.log(`⚡ Bootstrap: Mine already has ${existingBlocks.length} emoji blocks in Zustand`)
          }
        } else {
          // Check IndexedDB cache (learner-scoped)
          const activeLearnerId = store.activeLearner?.id
          if (activeLearnerId) {
            const cachedBlocks = await localStore.getCache<Block[]>(
              getLearnerMineBlocksKey(activeLearnerId)
            )
            if (cachedBlocks && cachedBlocks.length > 0) {
              store.setMineBlocks(cachedBlocks)
              store.setMineDataLoaded(true)
              if (process.env.NODE_ENV === 'development') {
                console.log(`⚡ Bootstrap: Loaded ${cachedBlocks.length} emoji blocks from IndexedDB cache`)
              }
            } else {
              // Build blocks with status from emojiProgress
              if (process.env.NODE_ENV === 'development') {
                console.log('🎯 Bootstrap: Building emoji blocks from vocabulary...')
              }
              
              const { packLoader } = await import('@/lib/pack-loader')
              const emojiVocab = await packLoader.getStarterItems('emoji_core', 50)
              const emojiProgress = store.emojiProgress || new Map<string, string>()
              
              const emojiBlocks = emojiVocab.map(item => ({
                sense_id: item.sense_id,
                word: item.word,
                definition_preview: item.definition_zh,
                rank: item.difficulty,  // Changed from tier to rank
                base_xp: 10 * item.difficulty,
                connection_count: 0,
                total_value: 100,
                status: (emojiProgress?.get(item.sense_id) || 'raw') as 'raw' | 'hollow' | 'solid',
                emoji: item.emoji,
              }))
              
              store.setMineBlocks(emojiBlocks)
              store.setMineDataLoaded(true)
              
              // Cache to IndexedDB (learner-scoped)
              if (activeLearnerId) {
                await localStore.setCache(
                  getLearnerMineBlocksKey(activeLearnerId),
                  emojiBlocks,
                  30 * 24 * 60 * 60 * 1000 // 30 days TTL
                )
              }
              
              if (process.env.NODE_ENV === 'development') {
                console.log(`✅ Bootstrap: Built and cached ${emojiBlocks.length} emoji blocks`)
              }
            }
          } else {
            // No active learner - build blocks without caching
            if (process.env.NODE_ENV === 'development') {
              console.log('🎯 Bootstrap: Building emoji blocks (no active learner)')
            }
            
            const { packLoader } = await import('@/lib/pack-loader')
            const emojiVocab = await packLoader.getStarterItems('emoji_core', 50)
            const emojiProgress = store.emojiProgress || new Map<string, string>()
            
            const emojiBlocks = emojiVocab.map(item => ({
              sense_id: item.sense_id,
              word: item.word,
              definition_preview: item.definition_zh,
              rank: item.difficulty,  // Changed from tier to rank
              base_xp: 10 * item.difficulty,
              connection_count: 0,
              total_value: 100,
              status: (emojiProgress?.get(item.sense_id) || 'raw') as 'raw' | 'hollow' | 'solid',
              emoji: item.emoji,
            }))
            
            store.setMineBlocks(emojiBlocks)
            store.setMineDataLoaded(true)
            
            if (process.env.NODE_ENV === 'development') {
              console.log(`✅ Bootstrap: Built ${emojiBlocks.length} emoji blocks (not cached - no active learner)`)
            }
          }
        }
      } else {
        // Legacy vocabulary flow
        const existingBlocks = store.mineBlocks
        if (existingBlocks && existingBlocks.length > 0) {
          if (process.env.NODE_ENV === 'development') {
            console.log(`⚡ Bootstrap: Mine already has ${existingBlocks.length} blocks`)
          }
        } else {
          // Need to generate starter pack
          const { vocabulary } = await import('@/lib/vocabulary')
          const { progressApi } = await import('@/services/progressApi')
        
        // FIRST: Always load from IndexedDB (instant, offline-first)
        // This ensures we have progress data even if API times out
        // Note: We use a Map for O(1) lookup when building blocks
        let progressMap = new Map<string, string>() // senseId -> status
        const activeLearnerId = store.activeLearner?.id
        if (activeLearnerId) {
          const localProgressMap = await localStore.getAllProgress(activeLearnerId)
          if (localProgressMap.size > 0) {
            progressMap = localProgressMap
            if (process.env.NODE_ENV === 'development') {
              console.log(`📦 Bootstrap: Loaded ${progressMap.size} progress items from IndexedDB (instant)`)
            }
          }
          
          // THEN: Try to fetch fresh progress from backend (parallel, non-blocking for UI)
          try {
            const progressData = await Promise.race([
              progressApi.getUserProgress(activeLearnerId),
              new Promise<null>((_, reject) => setTimeout(() => reject(new Error('timeout')), 60000))
            ]) as UserProgressResponse | null
            
            if (progressData?.progress) {
              // Update progressMap with fresh data from backend
              progressData.progress.forEach((p: BlockProgress) => {
                let status: 'raw' | 'hollow' | 'solid' = 'raw'
                if (p.status === 'verified' || p.status === 'mastered' || p.status === 'solid') {
                  status = 'solid'
                } else if (p.status === 'pending' || p.status === 'learning' || p.status === 'hollow') {
                  status = 'hollow'
                }
                progressMap.set(p.sense_id, status)
              })
              if (process.env.NODE_ENV === 'development') {
                console.log(`📊 Bootstrap: Got ${progressData.progress.length} fresh progress items from backend`)
              }
              
              // Save to IndexedDB for offline access (background, don't block)
              // Note: importProgress handles bulk insert more efficiently
              localStore.importProgress(activeLearnerId, progressData.progress)
                .catch(err => console.warn('Failed to save progress to IndexedDB:', err))
            }
          } catch (err) {
            if (process.env.NODE_ENV === 'development') {
              console.warn('⚠️ Bootstrap: Backend progress timeout, using IndexedDB cache')
            }
            // Already have IndexedDB data from progressMap - no action needed
          }
        } else {
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: No activeLearner, using empty progressMap')
          }
        }
        
        // Build starter pack from user's progress (not random!)
        if (process.env.NODE_ENV === 'development') {
          console.log('🎲 Bootstrap: Building starter pack from user progress...')
        }
        
        // First, try to load cached starter pack IDs
        const cachedIds = await localStore.getCache<string[]>('starter_pack_ids')
        let blocks: Block[] = []
        
        // Check if cached IDs need to be invalidated
        // If we have progress words that aren't in cached IDs, regenerate
        const progressSenseIds = new Set(progressMap.keys())
        const cachedIdsSet = new Set(cachedIds || [])
        const hasUnmatchedProgress = progressMap.size > 0 && 
          Array.from(progressSenseIds).some(id => !cachedIdsSet.has(id))
        
        if (cachedIds && cachedIds.length > 0 && !hasUnmatchedProgress) {
          // Rebuild from cached IDs (ensures consistency)
          if (process.env.NODE_ENV === 'development') {
            console.log(`📦 Bootstrap: Rebuilding from ${cachedIds.length} cached IDs (progressMap has ${progressMap.size} items)`)
          }
          
          // ✅ Parallelize with error handling
          const detailPromises = cachedIds.map(senseId => 
            vocabulary.getBlockDetail(senseId).catch(err => {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`Failed to load block detail for ${senseId}:`, err)
              }
              return null
            })
          )
          const detailResults = await Promise.allSettled(detailPromises)
          for (const result of detailResults) {
            if (result.status === 'fulfilled' && result.value) {
              const detail = result.value
              // Check progress status from progressMap (O(1) lookup)
              const progressStatus = progressMap.get(detail.sense_id)
              let status: 'raw' | 'hollow' | 'solid' = 'raw'
              if (progressStatus) {
                status = progressStatus as 'raw' | 'hollow' | 'solid'
              }
              
              blocks.push({
                sense_id: detail.sense_id,
                word: detail.word,
                definition_preview: (detail.definition_en || '').slice(0, 100),
                rank: detail.rank,  // Use rank (word complexity)
                base_xp: detail.base_xp,
                connection_count: detail.connection_count,
                total_value: detail.total_value,
                status,
              })
            }
          }
        } else if (hasUnmatchedProgress) {
          // Progress words don't match cached IDs - invalidate cache
          if (process.env.NODE_ENV === 'development') {
            console.log(`⚠️ Bootstrap: Cached starter pack doesn't include user progress - regenerating`)
          }
          await localStore.setCache('starter_pack_ids', null, 0) // Invalidate
        }
        
        // If no cached IDs or blocks couldn't be built, generate fresh but include user's progress words
        if (blocks.length === 0) {
          if (process.env.NODE_ENV === 'development') {
            console.log('🎲 Bootstrap: No cached starter pack, generating from progress...')
          }
          
          // Start with user's progress words (from progressMap)
          // ✅ Parallelize with error handling
          const progressEntries = Array.from(progressMap.entries())
          const progressDetailPromises = progressEntries.map(
            ([senseId]) => vocabulary.getBlockDetail(senseId).catch(err => {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`Failed to load progress block detail for ${senseId}:`, err)
              }
              return null
            })
          )
          const progressResults = await Promise.allSettled(progressDetailPromises)
          // Match details with status from progressMap
          progressResults.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value) {
              const [senseId, status] = progressEntries[index]
              const detail = result.value
              blocks.push({
                sense_id: detail.sense_id,
                word: detail.word,
                definition_preview: (detail.definition_en || '').slice(0, 100),
                rank: detail.rank,  // Use rank (word complexity)
                base_xp: detail.base_xp,
                connection_count: detail.connection_count,
                total_value: detail.total_value,
                status: status as 'raw' | 'hollow' | 'solid',
              })
            }
          })
          
          // If we don't have enough blocks, add some random ones
          if (blocks.length < 50) {
            const randomBlocks = await vocabulary.getStarterPack(50 - blocks.length)
            blocks.push(...randomBlocks)
          }
          
          // Save IDs for next time
          const blockIds = blocks.map(b => b.sense_id)
          await localStore.setCache('starter_pack_ids', blockIds, 30 * 24 * 60 * 60 * 1000)
        }
        
        if (blocks.length > 0) {
          // Save to Zustand
          store.setMineBlocks(blocks)
          store.setMineDataLoaded(true)
          
          if (process.env.NODE_ENV === 'development') {
            const hollowCount = blocks.filter(b => b.status === 'hollow').length
            const solidCount = blocks.filter(b => b.status === 'solid').length
            console.log(`✅ Bootstrap: Mine prepared with ${blocks.length} blocks (${hollowCount} hollow, ${solidCount} solid)`)
          }
        }
        
        // Hydrate mining queue from progressMap (hollow items)
        const hollowSenseIds = Array.from(progressMap.entries())
          .filter(([_, status]) => status === 'hollow')
          .map(([senseId, _]) => senseId)
        
        if (hollowSenseIds.length > 0) {
          const hollowItems: { senseId: string; word: string; addedAt: number }[] = []
          
          // Get words for the queued items
          // ✅ Parallelize with error handling
          const queueDetailPromises = hollowSenseIds.map(senseId => 
            vocabulary.getBlockDetail(senseId).catch(err => {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`Failed to load queue block detail for ${senseId}:`, err)
              }
              return null
            })
          )
          const queueResults = await Promise.allSettled(queueDetailPromises)
          // Build queue items
          queueResults.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value) {
              const detail = result.value
              const senseId = hollowSenseIds[index]
              hollowItems.push({
                senseId,
                word: detail.word,
                addedAt: Date.now()
              })
            }
          })
          
          // Save to Zustand
          const currentQueue = useAppStore.getState().miningQueue
          if (currentQueue.length === 0 && hollowItems.length > 0) {
            // Only set if queue is empty
            useAppStore.setState({ miningQueue: hollowItems })
            await localStore.setCache('mining_queue', hollowItems, 30 * 24 * 60 * 60 * 1000)
            if (process.env.NODE_ENV === 'development') {
              console.log(`⚡ Bootstrap: Mining queue hydrated with ${hollowItems.length} items`)
            }
          }
        }
        }
      } // End of legacy vocabulary flow
    } catch (mineError) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to prepare mine (non-critical):', mineError)
      }
      // Non-critical error - mine page can regenerate on demand
    }


    // ============================================
    // Step 13: Preload Page Bundles (JS Code Splitting)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[13])
    if (process.env.NODE_ENV === 'development') {
      console.log('📦 Bootstrap: Preloading page bundles...')
    }
    
    // Preload all learner page routes using Next.js prefetch
    // This downloads the JS bundles before user navigates, eliminating first-visit delay
    try {
      // Use link prefetch hints to trigger Next.js route preloading
      const pagesToPrefetch = [
        '/learner/mine',
        '/learner/build',
        '/learner/verification',
        '/learner/leaderboards',
        '/learner/profile',
        '/learner/family',
      ]
      
      // Create prefetch links that trigger Next.js to load page bundles
      if (typeof window !== 'undefined') {
        const prefetchPromises = pagesToPrefetch.map(async (href) => {
          // Use Next.js internal prefetch by creating link elements with rel="prefetch"
          const link = document.createElement('link')
          link.rel = 'prefetch'
          link.href = href
          link.as = 'document'
          document.head.appendChild(link)
          
          // Also try to fetch the RSC payload (React Server Components)
          try {
            // Get current locale from URL
            const locale = window.location.pathname.split('/')[1] || 'zh-TW'
            await fetch(`/${locale}${href}`, { 
              method: 'HEAD',
              headers: { 
                'RSC': '1',
                'Next-Router-Prefetch': '1'
              }
            }).catch(() => {})
          } catch {
            // Ignore - prefetch is best effort
          }
        })
        await Promise.all(prefetchPromises)
      }
      
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Page bundles preloaded')
      }
    } catch (e) {
      // Non-critical - pages will just load on first visit
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Page bundle preload failed (non-critical):', e)
      }
    }

    // ============================================
    // Step 14: Finalize
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[14])
    store.setBootstrapped(true)
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ Bootstrap: Complete!')
    }

    // ============================================
    // Determine Redirect Path
    // ============================================
    
    // Profile is guaranteed to exist here (fail-fast in Step 1)
    const roles = profile.roles || []
    const isParent = roles.includes('parent')
    const isLearner = roles.includes('learner')

    // Only redirect to onboarding if we have a profile but it's incomplete
    let redirectTo = '/onboarding'
    if (isLearner) {
      redirectTo = '/learner/home'
    } else if (isParent) {
      redirectTo = '/parent/dashboard'
    } else if (!profile.age || roles.length === 0) {
      // Profile exists but incomplete → onboarding
      redirectTo = '/onboarding'
    } else {
      // Profile exists but no roles → likely a data issue, default to onboarding
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ User has profile but no roles, redirecting to onboarding')
      }
      redirectTo = '/onboarding'
    }

    // ============================================
    // Trigger Background Sync (after redirect)
    // ============================================
    setTimeout(() => {
      if (process.env.NODE_ENV === 'development') {
        console.log('🔄 Bootstrap: Triggering background sync...')
      }
      store.setIsSyncing(true)
      downloadService
        .downloadAllUserData(userId)
        .then(() => {
          if (process.env.NODE_ENV === 'development') {
            console.log('✅ Background sync complete')
          }
          store.setIsSyncing(false)
        })
        .catch((error) => {
          console.error('❌ Background sync failed:', error)
          store.setIsSyncing(false)
        })
    }, 1000)

    // ============================================
    // Lazy Audio Preloading (Background, Non-Blocking)
    // ============================================
    if (store.activePack?.id === 'emoji_core' && store.emojiVocabulary) {
      setTimeout(() => {
        try {
          const { audioService } = require('@/lib/audio-service')
          const words = store.emojiVocabulary!.map(w => w.word)
          
          // Preload ALL words (default voice only = ~2.1MB)
          // Browser handles concurrent requests safely, no race conditions
          audioService.preloadWords(words, 'emoji')
            .then(() => {
              if (process.env.NODE_ENV === 'development') {
                console.log(`🎵 Background: Preloaded ${words.length} audio files`)
              }
            })
            .catch((err: unknown) => {
              // Non-critical - audio will load on-demand if preload fails
              if (process.env.NODE_ENV === 'development') {
                console.warn('Audio preload failed (non-critical):', err)
              }
            })
        } catch (err: unknown) {
          // Non-critical - audio will load on-demand if preload fails
          if (process.env.NODE_ENV === 'development') {
            console.warn('Audio preload setup failed (non-critical):', err)
          }
        }
      }, 1000) // Wait 1s after bootstrap to not interfere with critical loading
    }

    return { success: true, redirectTo }
  } catch (error) {
    console.error('❌ Bootstrap failed:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    store.setBootstrapError(errorMessage)
    return { success: false, error: errorMessage }
  }
}

/**
 * Reset bootstrap state (for logout)
 */
export async function resetBootstrap(): Promise<void> {
  const store = useAppStore.getState()
  
  // Clear Zustand store
  store.reset()
  
  // Clear IndexedDB
  await downloadService.clearAll()
  
  // Clear tiny localStorage preferences
  if (typeof window !== 'undefined') {
    localStorage.removeItem('lexicraft_selected_child')
    localStorage.removeItem('lexicraft_role_preference')
  }
  
  if (process.env.NODE_ENV === 'development') {
    console.log('🧹 Bootstrap: Reset complete')
  }
}

