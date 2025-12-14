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

import { useAppStore } from '@/stores/useAppStore'
import { downloadService } from './downloadService'
import { localStore } from '@/lib/local-store'
import { vocabularyLoader } from '@/lib/vocabularyLoader'

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
    if (profile) {
      store.setUser(profile)
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Loaded user profile')
      }
    } else {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: No cached profile found')
      }
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
    // Step 4: Load Progress
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[4])
    try {
      const progressData = await localStore.getAllProgress()
      if (progressData && progressData.length > 0) {
        // Calculate stats
        const stats = {
          total_discovered: progressData.length,
          solid_count: progressData.filter(p => p.status === 'solid').length,
          hollow_count: progressData.filter(p => p.status === 'hollow').length,
          raw_count: progressData.filter(p => p.status === 'raw').length,
        }
        store.setProgress(stats)
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ Bootstrap: Loaded progress stats')
        }
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to load progress:', error)
      }
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
    try {
      const currencies = await downloadService.getCurrencies()
      if (currencies) {
        store.setCurrencies(currencies)
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ Bootstrap: Loaded currencies')
        }
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to load currencies:', error)
      }
    }

    // ============================================
    // Step 8: Load Rooms (for Build page)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[8])
    try {
      const rooms = await downloadService.getRooms()
      if (rooms) {
        store.setRooms(rooms)
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ Bootstrap: Loaded rooms')
        }
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to load rooms:', error)
      }
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
      await packLoader.loadPack('emoji_core')
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Bootstrap: Emoji pack loaded successfully')
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
    // Step 10: Prepare Mining Area (Starter Pack)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[10])
    if (process.env.NODE_ENV === 'development') {
      console.log('⛏️ Bootstrap: Preparing mining area...')
    }
    
    try {
      // Check if emoji pack is active (default for MVP)
      const activePack = store.activePack
      const isEmojiPack = activePack?.id === 'emoji_core'
      
      if (isEmojiPack) {
        // 🎯 Load emoji vocabulary for MVP
        if (process.env.NODE_ENV === 'development') {
          console.log('🎯 Bootstrap: Loading emoji vocabulary (MVP mode)')
        }
        
        const { packLoader } = await import('@/lib/pack-loader')
        const emojiVocab = await packLoader.getStarterItems('emoji_core', 50)
        
        const emojiBlocks = emojiVocab.map(item => ({
          sense_id: item.sense_id,
          word: item.word,
          definition_preview: item.definition_zh,
          tier: item.difficulty,
          base_xp: 10 * item.difficulty,
          connection_count: 0,
          total_value: 100,
          status: 'raw' as const,
          rank: item.difficulty,
          emoji: item.emoji,
        }))
        
        store.setMineBlocks(emojiBlocks)
        store.setMineDataLoaded(true)
        
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${emojiBlocks.length} emoji words`)
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
        const localProgress = await localStore.getAllProgress()
        if (localProgress.length > 0) {
          localProgress.forEach(p => {
            progressMap.set(p.senseId, p.status)
          })
          if (process.env.NODE_ENV === 'development') {
            console.log(`📦 Bootstrap: Loaded ${progressMap.size} progress items from IndexedDB (instant)`)
          }
        }
        
        // THEN: Try to fetch fresh progress from backend (parallel, non-blocking for UI)
        try {
          const progressData = await Promise.race([
            progressApi.getUserProgress(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 5000))
          ]) as any
          
          if (progressData?.progress) {
            // Update progressMap with fresh data from backend
            progressData.progress.forEach((p: any) => {
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
            Promise.all(progressData.progress.map(async (p: any) => {
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
            })).catch(err => console.warn('Failed to save progress to IndexedDB:', err))
          }
        } catch (err) {
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ Bootstrap: Backend progress timeout, using IndexedDB cache')
          }
          // Already have IndexedDB data from progressMap - no action needed
        }
        
        // Build starter pack from user's progress (not random!)
        if (process.env.NODE_ENV === 'development') {
          console.log('🎲 Bootstrap: Building starter pack from user progress...')
        }
        
        // First, try to load cached starter pack IDs
        const cachedIds = await localStore.getCache<string[]>('starter_pack_ids')
        let blocks: any[] = []
        
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
          
          for (const senseId of cachedIds) {
            const detail = await vocabulary.getBlockDetail(senseId)
            if (detail) {
              // Check progress status from progressMap (O(1) lookup)
              const progressStatus = progressMap.get(senseId)
              let status: 'raw' | 'hollow' | 'solid' = 'raw'
              if (progressStatus) {
                status = progressStatus as 'raw' | 'hollow' | 'solid'
              }
              
              blocks.push({
                sense_id: detail.sense_id,
                word: detail.word,
                definition_preview: (detail.definition_en || '').slice(0, 100),
                tier: detail.tier,
                base_xp: detail.base_xp,
                connection_count: detail.connection_count,
                total_value: detail.total_value,
                status,
                rank: detail.rank,
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
          for (const [senseId, status] of progressMap.entries()) {
            const detail = await vocabulary.getBlockDetail(senseId)
            if (detail) {
              blocks.push({
                sense_id: detail.sense_id,
                word: detail.word,
                definition_preview: (detail.definition_en || '').slice(0, 100),
                tier: detail.tier,
                base_xp: detail.base_xp,
                connection_count: detail.connection_count,
                total_value: detail.total_value,
                status: status as 'raw' | 'hollow' | 'solid',
                rank: detail.rank,
              })
            }
          }
          
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
          for (const senseId of hollowSenseIds) {
            const detail = await vocabulary.getBlockDetail(senseId)
            if (detail) {
              hollowItems.push({
                senseId,
                word: detail.word,
                addedAt: Date.now()
              })
            }
          }
          
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
    // Step 11: Load Due Cards (for Verification page)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[11])
    if (process.env.NODE_ENV === 'development') {
      console.log('📋 Bootstrap: Loading due cards...')
    }
    
    try {
      const dueCards = await downloadService.getDueCards()
      if (dueCards && dueCards.length > 0) {
        store.setDueCards(dueCards)
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${dueCards.length} due cards`)
        }
      }
    } catch (dueCardsError) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to load due cards (non-critical):', dueCardsError)
      }
    }

    // ============================================
    // Step 12: Load Leaderboard (for Ranking page)
    // ============================================
    updateProgress(BOOTSTRAP_STEPS[12])
    if (process.env.NODE_ENV === 'development') {
      console.log('🏆 Bootstrap: Loading leaderboard...')
    }
    
    try {
      const { leaderboardsApi } = await import('@/services/gamificationApi')
      const [entries, userRank] = await Promise.all([
        leaderboardsApi.getGlobal('weekly', 50, 'xp'),
        leaderboardsApi.getRank('weekly', 'xp')
      ])
      
      if (entries && entries.length > 0) {
        store.setLeaderboardData({
          entries,
          userRank,
          period: 'weekly',
          metric: 'xp'
        })
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ Bootstrap: Loaded ${entries.length} leaderboard entries`)
        }
      }
    } catch (leaderboardError) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Bootstrap: Failed to load leaderboard (non-critical):', leaderboardError)
      }
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
    
    // CRITICAL: Check if profile was loaded successfully
    // If profile is undefined (API failed), we DON'T redirect to onboarding
    // because that treats "server down" as "new user"
    if (!profile) {
      console.error('⚠️ Bootstrap: Profile not loaded (API failed), cannot determine redirect')
      throw new Error('Failed to load user profile. Server may be unavailable.')
    }
    
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

