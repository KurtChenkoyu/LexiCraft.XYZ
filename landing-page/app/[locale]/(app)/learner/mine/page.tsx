'use client'

import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { useTranslations } from 'next-intl'
import { useRouter, useParams } from 'next/navigation'
import { vocabulary } from '@/lib/vocabulary'
import { progressApi, UserProgressResponse, BlockProgress } from '@/services/progressApi'
import { localStore } from '@/lib/local-store'
import { bundleCacheService } from '@/services/bundleCacheService'
import { useAuth } from '@/contexts/AuthContext'
import { useAppStore, selectProgress, selectMineBlocks, selectMineDataLoaded, selectActiveLearner, selectEmojiVocabulary, selectEmojiProgress } from '@/stores/useAppStore'
import { Block, UserStats } from '@/types/mine'
import { Spinner } from '@/components/ui'
import { MineHeader, BlockList, MineGraphG6, SearchModal } from '@/components/features/mine'
import { WordGrid } from '@/components/features/mining'
import { EmojiWordDetail } from '@/components/features/mining/EmojiWordDetail'
import { EmojiMineGrid } from '@/components/features/emoji/EmojiMineGrid'
import { BlockDetail } from '@/types/mine'
// Pack selection is now in the global top bar (LearnerTopBar)
import { packLoader } from '@/lib/pack-loader'
import { selectActivePack } from '@/stores/useAppStore'

type ViewMode = 'list' | 'graph' | 'grid'

const STARTER_PACK_CACHE_KEY = 'starter_pack_ids'
const STARTER_PACK_TTL = 30 * 24 * 60 * 60 * 1000 // 30 days

/**
 * Load starter pack from IndexedDB or generate new one
 * Following Last War caching approach - IndexedDB is the single cache
 */
async function loadOrGenerateStarterPack(skipCheck = false, backendProgress?: any[]): Promise<Block[]> {
  const isDev = process.env.NODE_ENV === 'development'
  if (isDev) console.log('🎲 loadOrGenerateStarterPack: Starting...', skipCheck ? '(skip check)' : '', 'backendProgress:', backendProgress?.length || 0)
  
  // If caller already ensured readiness, skip the check
  if (!skipCheck) {
    const isLoaded = await vocabulary.isLoaded()
    if (isDev) console.log('🎲 Vocabulary loaded?', isLoaded)
    
    if (!isLoaded) {
      if (isDev) console.warn('⚠️ Vocabulary not loaded yet, returning empty array')
      return []
    }
  }

  // PRIORITY 1: Use backend progress words (synced across browsers!)
  // This ensures Chrome and Cursor see the SAME words
  if (backendProgress && backendProgress.length > 0) {
    if (isDev) console.log('🔄 Building starter pack from backend progress:', backendProgress.length, 'items')
    
    const blocks: Block[] = []
    const addedSenseIds = new Set<string>()
    
    // Add all backend progress items first
    for (const p of backendProgress) {
      if (addedSenseIds.has(p.sense_id)) continue
      const detail = await vocabulary.getBlockDetail(p.sense_id)
      if (detail) {
        blocks.push({
          sense_id: detail.sense_id,
          word: detail.word,
          definition_preview: (detail.definition_en || '').slice(0, 100),
          rank: detail.rank || detail.tier,  // Use rank (new) or fallback to tier (legacy)
          base_xp: detail.base_xp,
          connection_count: detail.connection_count,
          total_value: detail.total_value,
          status: p.status === 'verified' || p.status === 'mastered' ? 'solid' : 
                  p.status === 'pending' || p.status === 'learning' ? 'hollow' : 'raw',
          rank: detail.rank,
        })
        addedSenseIds.add(p.sense_id)
      }
    }
    
    // Pad with random words to reach 50 total
    if (blocks.length < 50) {
      const additionalBlocks = await vocabulary.getStarterPack(50 - blocks.length)
      for (const block of additionalBlocks) {
        if (!addedSenseIds.has(block.sense_id)) {
          blocks.push(block)
          addedSenseIds.add(block.sense_id)
        }
      }
    }
    
    // Save to IndexedDB (sync across refreshes)
    try {
      const senseIds = blocks.map(b => b.sense_id)
      await localStore.setCache(STARTER_PACK_CACHE_KEY, senseIds, STARTER_PACK_TTL)
      if (isDev) console.log('✅ Saved synced starter pack to IndexedDB:', blocks.length, 'blocks')
    } catch (err) {
      if (isDev) console.warn('Failed to save starter pack to IndexedDB:', err)
    }
    
    return blocks
  }

  // PRIORITY 2: Try to load from IndexedDB cache (Last War approach)
  try {
    const cached = await localStore.getCache<string[]>(STARTER_PACK_CACHE_KEY)
    if (isDev) console.log('🎲 Cached starter pack IDs:', cached?.length || 0)
    
    if (cached && cached.length > 0) {
      // Reconstruct blocks from saved sense IDs
      const blocks: Block[] = []
      for (const senseId of cached) {
        const detail = await vocabulary.getBlockDetail(senseId)
        if (detail) {
          blocks.push({
            sense_id: detail.sense_id,
            word: detail.word,
            definition_preview: (detail.definition_en || '').slice(0, 100),
            rank: detail.rank || detail.tier,  // Use rank (new) or fallback to tier (legacy)
            base_xp: detail.base_xp,
            connection_count: detail.connection_count,
            total_value: detail.total_value,
            status: 'raw',
            rank: detail.rank,
          })
        }
      }
      if (blocks.length > 0) {
        if (isDev) console.log('⚡ Loaded starter pack from IndexedDB:', blocks.length, 'blocks')
        return blocks
      }
    }
  } catch (err) {
    if (isDev) console.warn('Failed to load starter pack from IndexedDB:', err)
  }

  // PRIORITY 3: Generate new starter pack (first time user)
  if (isDev) console.log('🎲 Generating new starter pack...')
  let newBlocks = await vocabulary.getStarterPack(50)
  
  if (isDev) console.log('🎲 Generated blocks:', newBlocks.length)
  
  // Save to IndexedDB (Last War approach)
  try {
    const senseIds = newBlocks.map(b => b.sense_id)
    await localStore.setCache(STARTER_PACK_CACHE_KEY, senseIds, STARTER_PACK_TTL)
    if (isDev) console.log('✅ Generated and saved new starter pack to IndexedDB:', newBlocks.length, 'blocks')
  } catch (err) {
    if (isDev) console.warn('Failed to save starter pack to IndexedDB:', err)
  }
  
  return newBlocks
}

export default function MinePage() {
  const t = useTranslations('mine')
  const router = useRouter()
  const params = useParams()
  const locale = (params.locale as string) || 'en'
  const { session } = useAuth()
  
  // ⚡ Read from Zustand (instant, persists across navigation!)
  const progressFromStore = useAppStore(selectProgress)
  const mineBlocksFromStore = useAppStore(selectMineBlocks)
  const mineDataLoaded = useAppStore(selectMineDataLoaded)
  const hydrateMiningQueue = useAppStore((state) => state.hydrateMiningQueue)
  const setMineBlocks = useAppStore((state) => state.setMineBlocks)
  const setMineDataLoaded = useAppStore((state) => state.setMineDataLoaded)
  const addToQueue = useAppStore((state) => state.addToQueue)
  
  // 📦 Active pack - determines which vocabulary to show
  const activePack = useAppStore(selectActivePack)
  const isEmojiPack = activePack?.id === 'emoji_core'
  const activeLearner = useAppStore(selectActiveLearner)
  
  // ⚡ Read emoji data from Zustand (pre-loaded by Bootstrap)
  const emojiVocabulary = useAppStore(selectEmojiVocabulary)
  const emojiProgress = useAppStore(selectEmojiProgress)
  const miningQueue = useAppStore((state) => state.miningQueue)
  
  const [userProgress, setUserProgress] = useState<UserProgressResponse | null>(null)
  const [isLoading, setIsLoading] = useState(!mineDataLoaded) // Start as false if already loaded!
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [demoMode, setDemoMode] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [selectedWordId, setSelectedWordId] = useState<string | null>(null)
  
  // ⚡ Check if Bootstrap has loaded the Mine data
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  
  // Use blocks from Zustand store (persists across navigation)
  const localBlocks = mineBlocksFromStore
  
  // Find the selected block for detail view (must be after localBlocks is defined)
  const selectedBlock = selectedWordId 
    ? localBlocks.find(b => b.sense_id === selectedWordId) || null 
    : null
  const setLocalBlocks = useCallback((blocks: Block[]) => {
    setMineBlocks(blocks)
  }, [setMineBlocks])
  
  // Phase 5: Layer navigation state
  const [currentLayer, setCurrentLayer] = useState<{
    senses: string[]
    layerIndex: number
    parentSense: string | null
  }>({
    senses: mineBlocksFromStore.length > 0 ? mineBlocksFromStore.map((b: Block) => b.sense_id) : [],
    layerIndex: 0,
    parentSense: null
  })

  // 📦 Load emoji pack vocabulary when activePack changes to emoji_core
  // Triggered by activePack changes from PackSelector
  const emojiPackLoaded = useRef(false)
  useEffect(() => {
    // Only load if emoji pack is selected and hasn't been loaded yet this session
    const hasEmojiBlocks = localBlocks.some(b => b.emoji)
    const shouldLoadEmoji = isEmojiPack && isBootstrapped && !hasEmojiBlocks && !emojiPackLoaded.current
    
    console.log('📦 Emoji pack check:', { isEmojiPack, isBootstrapped, hasEmojiBlocks, shouldLoadEmoji })
    
    if (shouldLoadEmoji) {
      emojiPackLoaded.current = true
      const loadEmojiPack = async () => {
        console.log('🎯 Mine: Loading emoji pack vocabulary')
        setIsLoading(true)
        try {
          const vocab = await packLoader.getStarterItems('emoji_core', 50)
          const emojiBlocks: Block[] = vocab.map(item => ({
            sense_id: item.sense_id,
            word: item.word,
            definition_preview: item.definition_zh,
            rank: item.difficulty,  // Changed from tier to rank
            base_xp: 10 * item.difficulty,
            connection_count: 0,
            total_value: 100,
            status: 'raw' as const,
            rank: item.difficulty,
            emoji: item.emoji,
          }))
          setLocalBlocks(emojiBlocks)
          setCurrentLayer({
            senses: emojiBlocks.map(b => b.sense_id),
            layerIndex: 0,
            parentSense: null
          })
          console.log('✅ Loaded emoji pack:', emojiBlocks.length, 'words')
        } catch (error) {
          console.error('Failed to load emoji pack:', error)
        } finally {
          setIsLoading(false)
        }
      }
      loadEmojiPack()
    }
  }, [isEmojiPack, isBootstrapped, localBlocks, setLocalBlocks])

  // 🎯 Enrich blocks with emoji data if missing (when using cached blocks)
  useEffect(() => {
    if (!isEmojiPack || localBlocks.length === 0) return
    
    // Check if any blocks are missing emoji
    const missingEmoji = localBlocks.some(b => !b.emoji)
    if (!missingEmoji) return
    
    const enrichWithEmoji = async () => {
      try {
        const packData = await packLoader.loadPack('emoji_core')
        if (!packData) return
        
        // Create lookup map
        const emojiMap = new Map<string, string>()
        const translationMap = new Map<string, string>()
        packData.vocabulary.forEach(item => {
          emojiMap.set(item.sense_id, item.emoji)
          translationMap.set(item.sense_id, item.definition_zh)
        })
        
        // Enrich blocks with emoji
        const enrichedBlocks = localBlocks.map(block => ({
          ...block,
          emoji: block.emoji || emojiMap.get(block.sense_id) || '📝',
          definition_preview: block.definition_preview || translationMap.get(block.sense_id) || '',
        }))
        
        setLocalBlocks(enrichedBlocks)
        console.log('✅ Enriched blocks with emoji data')
      } catch (error) {
        console.warn('Failed to enrich blocks with emoji:', error)
      }
    }
    
    enrichWithEmoji()
  }, [isEmojiPack, localBlocks, setLocalBlocks])

  // Load starter pack from IndexedDB (persisted or new)
  // ⚡ SKIP if already loaded by Bootstrap (instant rendering!)
  useEffect(() => {
    let mounted = true
    const isDev = process.env.NODE_ENV === 'development'
    
    // ⚡ FAST PATH 1: Already bootstrapped and data is in Zustand
    if (isBootstrapped && mineDataLoaded && mineBlocksFromStore.length > 0) {
      if (isDev) console.log('⚡ Mine: Using Bootstrap data (instant!)')
      setIsLoading(false)
      // Update currentLayer if it's empty but we have blocks
      if (currentLayer.senses.length === 0) {
        setCurrentLayer({
          senses: mineBlocksFromStore.map((b: Block) => b.sense_id),
          layerIndex: 0,
          parentSense: null
        })
      }
      return
    }
    
    // ⚡ FAST PATH 2: Data in Zustand but bootstrap flag may not be set yet
    if (mineDataLoaded && mineBlocksFromStore.length > 0) {
      if (isDev) console.log('⚡ Mine: Using Zustand data (tab switch)')
      setIsLoading(false)
      if (currentLayer.senses.length === 0) {
        setCurrentLayer({
          senses: mineBlocksFromStore.map((b: Block) => b.sense_id),
          layerIndex: 0,
          parentSense: null
        })
      }
      return
    }
    
    // ⚡ FAST PATH 3: Bootstrap is in progress - wait for it
    if (!isBootstrapped) {
      if (isDev) console.log('⏳ Mine: Waiting for Bootstrap to complete...')
      // The loading screen is visible, so just return and let Bootstrap do its thing
      // When Bootstrap completes, this effect will re-run due to isBootstrapped change
      return
    }
    
    // Only hydrate mining queue if Bootstrap somehow didn't
    if (!mineDataLoaded) {
      hydrateMiningQueue()
    }
    
    async function loadStarter() {
      // Ensure vocabulary is ready (main thread handles everything now)
      const { vocabularyLoader } = await import('@/lib/vocabularyLoader')
      
      const isDev = process.env.NODE_ENV === 'development'
      try {
        if (isDev) console.log('⏳ Ensuring vocabulary is ready...')
        const result = await vocabularyLoader.ensureReady()
        if (isDev) console.log(`✅ Vocabulary ready: ${result.count} senses (${result.source})`)
      } catch (error) {
        console.error('❌ Failed to load vocabulary:', error)
        window.location.href = '/start'
        return
      }
      
      if (!mounted) return
      
      // SYNC FIRST: Fetch backend progress to build synced starter pack (with timeout)
      let backendProgress: any[] = []
      try {
        const { progressApi } = await import('@/services/progressApi')
        
        // Add timeout to prevent blocking (3s - if API is slow, use IndexedDB fallback)
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Progress fetch timeout')), 3000)
        )
        
        const progressData = await Promise.race([
          progressApi.getUserProgress(),
          timeoutPromise
        ]) as any
        
        if (progressData?.progress) {
          backendProgress = progressData.progress
          if (isDev) console.log('🔄 Fetched backend progress:', backendProgress.length, 'items')
          
          // Save progress to IndexedDB in background (don't block)
          Promise.all(backendProgress.map(async (p: any) => {
            let status: 'raw' | 'hollow' | 'solid' = 'raw'
            if (p.status === 'verified' || p.status === 'mastered' || p.status === 'solid') {
              status = 'solid'
            } else if (p.status === 'pending' || p.status === 'learning' || p.status === 'hollow') {
              status = 'hollow'
            }
            await localStore.saveProgress(p.sense_id, status, {
              rank: p.rank || p.tier,  // Use rank (new) or fallback to tier (legacy)
              startedAt: p.started_at,
              masteryLevel: p.mastery_level,
            })
          })).catch(err => console.warn('Failed to save progress:', err))
        }
      } catch (err) {
        if (isDev) console.warn('⚠️ Could not fetch backend progress (timeout or error):', err)
        
        // FALLBACK: Try loading from IndexedDB (might have been synced by hydrateMiningQueue)
        try {
          const localProgressMap = activeLearner?.id 
            ? await localStore.getAllProgress(activeLearner.id)
            : new Map<string, string>()
          if (localProgressMap.size > 0) {
            // Convert Map to array format expected by loadOrGenerateStarterPack
            // Note: getAllProgress returns Map<senseId, status>, we need to get full details
            backendProgress = []
            for (const [senseId, status] of localProgressMap.entries()) {
              const fullProgress = activeLearner?.id 
                ? await localStore.getProgress(activeLearner.id, senseId)
                : undefined
              backendProgress.push({
                sense_id: senseId,
                status: status as 'raw' | 'hollow' | 'solid' | 'mastered',
                rank: fullProgress?.rank || fullProgress?.tier,  // Use rank (new) or fallback to tier (legacy)
                started_at: fullProgress?.startedAt?.toString(),
                mastery_level: fullProgress?.masteryLevel,
              })
            }
            if (isDev) console.log('🔄 Using cached IndexedDB progress:', backendProgress.length, 'items')
          }
        } catch (cacheErr) {
          if (isDev) console.warn('⚠️ Could not load IndexedDB progress:', cacheErr)
        }
      }
      
      // Now vocabulary is guaranteed ready - load starter pack with backend progress
      if (isDev) console.log('🎲 Loading starter pack...')
      const blocks = await loadOrGenerateStarterPack(true, backendProgress) // Pass backend progress!
      if (!mounted) return
      
      if (blocks.length === 0) {
        if (isDev) console.warn('⚠️ Starter pack is empty, trying again...')
        // Retry once more
        const retryBlocks = await loadOrGenerateStarterPack(false, backendProgress)
        if (retryBlocks.length > 0) {
          setLocalBlocks(retryBlocks)
          setCurrentLayer({
            senses: retryBlocks.map(b => b.sense_id),
            layerIndex: 0,
            parentSense: null
          })
          setMineDataLoaded(true)
        }
        return
      }
      
      console.log('🎯 Setting localBlocks:', blocks.length)
      setLocalBlocks(blocks)
      
      const senseIds = blocks.map(b => b.sense_id)
      console.log('🎯 Setting currentLayer.senses:', senseIds.length, 'first 3:', senseIds.slice(0, 3))
      
      // Initialize Layer 0 with starter pack
      setCurrentLayer({
        senses: senseIds,
        layerIndex: 0,
        parentSense: null
      })
      
      setMineDataLoaded(true)
    }
    
    loadStarter()
    
    return () => { mounted = false }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, isBootstrapped, mineDataLoaded, mineBlocksFromStore.length]) // Re-run when Bootstrap completes

  /**
   * Refresh starter pack with new random blocks
   */
  const handleRefreshSuggestions = useCallback(async () => {
    // Clear from IndexedDB (Last War approach)
    // Setting to empty array will cause regeneration on next load
    try {
      await localStore.setCache(STARTER_PACK_CACHE_KEY, [], STARTER_PACK_TTL)
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Failed to clear starter pack from IndexedDB:', err)
      }
    }
    setRefreshKey(k => k + 1)
  }, [])

  /**
   * Phase 5: Handle drill down into layer 1 (1-hop connections)
   */
  const handleDrillDown = useCallback(async (senseId: string) => {
    if (process.env.NODE_ENV === 'development') console.log('Drilling down into:', senseId)
    const connections = await vocabulary.getConnections(senseId)
    const hop1Senses = connections.map(c => c.sense_id)
    setCurrentLayer({
      senses: hop1Senses,
      layerIndex: currentLayer.layerIndex + 1,
      parentSense: senseId
    })
  }, [currentLayer.layerIndex])

  /**
   * Phase 5: Handle back navigation
   */
  const handleBackLayer = useCallback(() => {
    // For now, reload Layer 0
    // TODO: Track layer history for proper back navigation
    loadOrGenerateStarterPack().then(blocks => {
      setCurrentLayer({
        senses: blocks.map(b => b.sense_id),
        layerIndex: 0,
        parentSense: null
      })
    })
  }, [])

  // ⚡ Load progress from IndexedDB (synced from backend by hydrateMiningQueue)
  // This runs after hydrateMiningQueue saves backend progress to IndexedDB
  const progressLoadedRef = useRef(false)
  
  useEffect(() => {
    // Skip if no blocks loaded yet or already loaded progress
    if (localBlocks.length === 0) return
    if (progressLoadedRef.current) return // Skip on re-renders
    
    const loadProgress = async () => {
      try {
        // Don't set isLoading here - it causes flash on tab switch
        
        // Load progress from IndexedDB (populated by hydrateMiningQueue from backend)
        const localProgressMap = activeLearner?.id 
          ? await localStore.getAllProgress(activeLearner.id)
          : new Map<string, string>()
        
        if (localProgressMap.size > 0) {
          // Convert Map to BlockProgress array format
          // Note: getAllProgress returns Map<senseId, status>, we need to get full details
          const progressData: BlockProgress[] = []
          for (const [senseId, status] of localProgressMap.entries()) {
            // Try to get full progress details if available
            const fullProgress = activeLearner?.id 
              ? await localStore.getProgress(activeLearner.id, senseId)
              : undefined
            progressData.push({
              sense_id: senseId,
              status: status as 'raw' | 'hollow' | 'solid' | 'mastered',
              tier: fullProgress?.tier,
              started_at: fullProgress?.startedAt?.toString(),
              mastery_level: fullProgress?.masteryLevel,
            })
          }
          
          // Calculate stats from progress data
          const hollow = progressData.filter(p => p.status === 'hollow').length
          const solid = progressData.filter(p => p.status === 'solid').length
          
          setUserProgress({
            progress: progressData,
            stats: {
              total_discovered: hollow + solid,
              solid_count: solid,
              hollow_count: hollow,
              raw_count: Math.max(0, localBlocks.length - hollow - solid),
            }
          })
          progressLoadedRef.current = true
          console.log(`📊 Loaded progress from IndexedDB: ${hollow} hollow, ${solid} solid`)
        } else if (!progressLoadedRef.current) {
          // No progress yet - show all as raw
          setUserProgress({
            progress: [],
            stats: { 
              total_discovered: 0, 
              solid_count: 0, 
              hollow_count: 0, 
              raw_count: localBlocks.length 
            }
          })
        }
        
        setIsLoading(false)
      } catch (err: any) {
        console.error('Failed to load progress:', err)
        setIsLoading(false)
      }
    }

    // Load once
    loadProgress()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localBlocks.length]) // Run once when blocks are loaded

  // BACKGROUND: Pre-cache verification bundles for all inventory blocks
  // This enables instant MCQ loading when user verifies any word
  useEffect(() => {
    if (localBlocks.length > 0) {
      const senseIds = localBlocks.map(b => b.sense_id)
      bundleCacheService.preCacheBundles(senseIds, session?.access_token)
    }
  }, [localBlocks, session?.access_token])

  // Enrich blocks with user progress status (including queue items as "hollow")
  const enrichedBlocks = useMemo(() => {
    // Create progress lookup map
    const progressMap = new Map<string, BlockProgress>()
    if (userProgress?.progress) {
      for (const p of userProgress.progress) {
        progressMap.set(p.sense_id, p)
      }
    }
    
    // Create queue lookup set
    const queuedSenseIds = new Set(miningQueue.map(q => q.senseId))

    // Enrich blocks with status
    return localBlocks.map(block => {
      const progress = progressMap.get(block.sense_id)
      
      // Check backend progress first
      if (progress) {
        let status: 'raw' | 'hollow' | 'solid' = 'raw'
        if (progress.status === 'verified' || progress.status === 'mastered' || progress.status === 'solid') {
          status = 'solid'
        } else if (progress.status === 'learning' || progress.status === 'pending' || progress.status === 'hollow') {
          status = 'hollow'
        }
        return { ...block, status }
      }
      
      // If in queue but not in backend progress, mark as hollow (forging)
      if (queuedSenseIds.has(block.sense_id)) {
        return { ...block, status: 'hollow' as const }
      }

      return { ...block, status: 'raw' as const }
    })
  }, [localBlocks, userProgress, miningQueue])
  
  // Calculate user stats from enrichedBlocks (which already includes queue items as hollow)
  const userStats: UserStats = useMemo(() => {
    // Always calculate from enrichedBlocks since they already account for:
    // 1. Backend progress (solid/hollow/raw status)
    // 2. Queue items (marked as hollow)
    let solid = 0, hollow = 0, raw = 0
    
    for (const block of enrichedBlocks) {
      if (block.status === 'solid') solid++
      else if (block.status === 'hollow') hollow++
      else raw++
    }

    // Debug log only in dev
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
      console.log(`📊 userStats: solid=${solid}, hollow=${hollow}, raw=${raw}, total=${enrichedBlocks.length}, queue=${miningQueue.length}`)
    }

    return {
      total_discovered: solid + hollow,
      solid_count: solid,
      hollow_count: hollow,
      raw_count: raw,
    }
  }, [enrichedBlocks, miningQueue.length])

  // Build user progress map for graph (MUST be before conditional returns)
  const userProgressMap = useMemo(() => {
    const map: Record<string, 'raw' | 'hollow' | 'solid'> = {}
    if (userProgress) {
      for (const p of userProgress.progress) {
        if (p.status === 'verified' || p.status === 'mastered' || p.status === 'solid') {
          map[p.sense_id] = 'solid'
        } else if (p.status === 'learning' || p.status === 'pending' || p.status === 'hollow') {
          map[p.sense_id] = 'hollow'
        }
      }
    }
    return map
  }, [userProgress])

  // Handle node selection from graph (MUST be before conditional returns)
  const handleGraphNodeSelect = useCallback(async (nodeId: string) => {
    const isDev = process.env.NODE_ENV === 'development'
    if (isDev) console.log('🔥 handleGraphNodeSelect called with:', nodeId)
    
    // Handle both formats: sense_id (e.g., "drop.v.01") and word_pos (e.g., "drop_verb")
    let senseId: string | null = null
    
    if (nodeId.includes('_') && !nodeId.includes('.')) {
      // Cytoscape format: word_pos (e.g., "total_v", "just_r")
      const parts = nodeId.split('_')
      const pos = parts.pop() // Last part is POS
      const word = parts.join('_') // Handle words with underscores
      
      if (isDev) console.log('Looking up word:', word, 'pos:', pos)
      
      // Try to find senses for this word
      const matchingSenses = await vocabulary.getSensesForWord(word || '')
      
      if (isDev) console.log('Found senses for word:', matchingSenses.length)
      
      if (matchingSenses.length > 0) {
        // Try to match by POS, or just use the first one
        const posMap: Record<string, string[]> = {
          'n': ['n', 'noun'],
          'v': ['v', 'verb'],
          'a': ['a', 'adj', 'adjective', 's'],
          's': ['s', 'satellite', 'adj', 'adjective'],
          'r': ['r', 'adv', 'adverb'],
        }
        
        const matchingPosValues = posMap[pos || ''] || [pos]
        const matchedSense = matchingSenses.find((s: any) => 
          matchingPosValues.some(p => s.pos === p || s.pos?.toLowerCase() === p)
        ) || matchingSenses[0]
        
        if (matchedSense && matchedSense.id) {
          senseId = matchedSense.id as string
          if (isDev) console.log('Matched sense:', senseId)
        }
      }
    } else {
      // Direct sense_id format (e.g., "drop.v.01")
      senseId = nodeId
    }
    
    if (isDev) console.log('Sense ID:', senseId ? 'found' : 'NOT FOUND')
    
    if (senseId) {
      // Navigate to word detail page
      router.push(`/${locale}/learner/word/${encodeURIComponent(senseId)}`)
    } else {
      // Show a simple info for now
      const [word] = nodeId.split('_')
      alert(`詞彙: ${word}\n\n(詳細資料載入中...)`)
    }
  }, [locale, router])

  // Handle start forging directly from graph (without opening modal)
  const handleStartForging = useCallback(async (nodeId: string) => {
    const isDev = process.env.NODE_ENV === 'development'
    if (isDev) console.log('🔥 handleStartForging called with:', nodeId)
    
    // Parse word_pos format (e.g., "drop_verb")
    const parts = nodeId.split('_')
    const pos = parts.pop()
    const word = parts.join('_')
    
    // Find the sense_id for this word
    const matchingSenses = await vocabulary.getSensesForWord(word || '')
    const posMap: Record<string, string[]> = {
      'n': ['n', 'noun'],
      'v': ['v', 'verb'],
      'a': ['a', 'adj', 'adjective', 's'],
      's': ['s', 'satellite', 'adj', 'adjective'],
      'r': ['r', 'adv', 'adverb'],
      'noun': ['n', 'noun'],
      'verb': ['v', 'verb'],
      'adj': ['a', 'adj', 'adjective'],
      'adv': ['r', 'adv', 'adverb'],
    }
    
    const matchingPosValues = posMap[pos || ''] || [pos]
    const matchedSense = matchingSenses.find((s: any) => 
      matchingPosValues.some(p => s.pos === p || s.pos?.toLowerCase() === p)
    ) || matchingSenses[0]
    
    if (matchedSense) {
      const senseId = (matchedSense as any).id
      if (isDev) console.log('Starting forging for sense:', senseId)
      
      // Update local progress immediately (optimistic update)
      setUserProgress(prev => {
        if (!prev) {
          return {
            progress: [{ sense_id: senseId, status: 'hollow' }],
            stats: { total_discovered: 1, solid_count: 0, hollow_count: 1, raw_count: 0 }
          }
        }
        const existingIndex = prev.progress.findIndex(p => p.sense_id === senseId)
        if (existingIndex >= 0) {
          const updated = [...prev.progress]
          updated[existingIndex] = { ...updated[existingIndex], status: 'hollow' }
          return { ...prev, progress: updated }
        } else {
          return {
            ...prev,
            progress: [...prev.progress, { sense_id: senseId, status: 'hollow' }]
          }
        }
      })
      
      // TODO: Call API to persist the forging start
      // progressApi.startForging(senseId)
    }
  }, [])

  // Vocabulary loading is handled by VocabularyLoadingIndicator in app layout
  // No need to check here - vocabulary will be ready when user accesses this page

  // Show loading only while fetching user progress
  if (isLoading) {
    return (
      <div className="min-h-full bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" className="text-cyan-600 mb-4" />
          <p className="text-gray-600 text-lg">載入進度中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-full bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="max-w-6xl mx-auto text-center">
          <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-8">
            <p className="text-red-800 text-lg">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-6 py-2 bg-red-100 hover:bg-red-200 rounded-lg text-red-800 transition-colors"
            >
              重試
            </button>
          </div>
        </div>
      </div>
    )
  }

  const isGraphView = viewMode === 'graph'

  // NOTE: This page is inside learner/layout.tsx which provides:
  // - game-container (fixed viewport, overflow-hidden)
  // - main wrapper with pt-16 pb-20 px-4 overflow-y-auto
  // So we DON'T add our own <main> or padding here.

  // Emoji Mode: Show EmojiMineGrid instead of regular mine page
  if (isEmojiPack) {
    // Convert selected word to Block format for EmojiWordDetail
    const selectedEmojiWord = selectedWordId && emojiVocabulary
      ? emojiVocabulary.find(w => w.sense_id === selectedWordId)
      : null
    
    const selectedEmojiBlock = selectedEmojiWord ? {
      sense_id: selectedEmojiWord.sense_id,
      word: selectedEmojiWord.word,
      definition_preview: selectedEmojiWord.definition_zh,
      tier: selectedEmojiWord.difficulty,  // Parameter name kept as tier for API compatibility
      base_xp: 10 * selectedEmojiWord.difficulty,
      connection_count: 0,
      total_value: 100,
      // FIX: Check both emojiProgress AND miningQueue for status
      status: (() => {
        const progressStatus = emojiProgress?.get(selectedEmojiWord.sense_id)
        if (progressStatus === 'solid' || progressStatus === 'mastered') return 'solid'
        if (progressStatus === 'hollow' || progressStatus === 'learning' || progressStatus === 'pending') return 'hollow'
        // Fallback: Check if in mining queue (optimistic update)
        const isInQueue = miningQueue.some(q => q.senseId === selectedEmojiWord.sense_id)
        return isInQueue ? 'hollow' : 'raw'
      })() as 'raw' | 'hollow' | 'solid',
      rank: selectedEmojiWord.difficulty,
      emoji: selectedEmojiWord.emoji,
      translation: selectedEmojiWord.definition_zh,
      category: selectedEmojiWord.category,
      difficulty: selectedEmojiWord.difficulty,
    } : null
    
    return (
      <div className="min-h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="max-w-7xl mx-auto py-6">
          <EmojiMineGrid 
            onWordClick={(id) => setSelectedWordId(id)}
          />
        </div>
        
        {/* Word Detail Modal (Emoji Pack) */}
        <EmojiWordDetail
          block={selectedEmojiBlock}
          isOpen={!!selectedWordId}
          onClose={() => setSelectedWordId(null)}
          onAddToSmelting={(senseId, word) => {
            addToQueue(senseId, word) // This function ALREADY handles all the complex cache stuff
            setSelectedWordId(null) // Close modal after adding
          }}
          onStartQuiz={(senseId) => {
            setSelectedWordId(null)
            router.push(`/${locale}/learner/verification`) // Simple navigation for MVP
          }}
        />
      </div>
    )
  }
  // NOTE: This page is inside learner/layout.tsx which provides:
  // - game-container (fixed viewport, overflow-hidden)
  // - main wrapper with pt-16 pb-20 px-4 overflow-y-auto
  // So we DON'T add our own <main> or padding here.

  return (
    <div className={`min-h-full ${isGraphView ? 'bg-slate-900' : 'bg-gradient-to-br from-slate-50 to-slate-100'}`}>
      <div className={isGraphView ? 'max-w-full' : 'max-w-6xl mx-auto'}>
        {/* Header with stats */}
        <MineHeader
          mode="starter"
          userStats={userStats}
          onRefreshSuggestions={viewMode === 'list' ? handleRefreshSuggestions : undefined}
        />

        {/* View toggle */}
        <div className="flex justify-center mb-6 gap-4">
          <div className={`inline-flex rounded-xl p-1 ${isGraphView ? 'bg-slate-800' : 'bg-white shadow-lg'}`}>
            <button
              onClick={() => setViewMode('grid')}
              className={`px-5 py-2.5 rounded-lg font-medium transition-all ${
                viewMode === 'grid'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
              title="網格挖礦模式"
            >
              ⛏️ 網格
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-5 py-2.5 rounded-lg font-medium transition-all ${
                viewMode === 'list'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              📋 列表
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`px-5 py-2.5 rounded-lg font-medium transition-all ${
                viewMode === 'graph'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
              title="互動式詞彙網絡圖"
            >
              🕸️ 網絡
            </button>
          </div>
          
          {/* Search Button */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors font-medium"
          >
            🔍 搜尋單字
          </button>
          
          {/* Demo mode toggle (only in graph view) */}
          {isGraphView && (
            <button
              onClick={() => setDemoMode(!demoMode)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                demoMode
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {demoMode ? '🎮 Demo ON' : '🎮 Demo'}
            </button>
          )}
        </div>

        {/* Content based on view mode */}
        {viewMode === 'grid' ? (
          <WordGrid
            senseIds={currentLayer.senses}
            // Use emoji pack mode based on active pack
            blocks={isEmojiPack ? localBlocks : undefined}
            isEmojiMode={isEmojiPack}
            onWordClick={(id) => setSelectedWordId(id)}
          />
        ) : viewMode === 'list' ? (
          <BlockList blocks={enrichedBlocks} />
        ) : (
          <div className="rounded-xl overflow-hidden shadow-2xl">
            <MineGraphG6
              userProgress={userProgressMap}
              onNodeSelect={handleGraphNodeSelect}
              onStartForging={handleStartForging}
              demoMode={demoMode}
            />
          </div>
        )}
      </div>

      {/* Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        userProgress={userProgressMap}
        onSelectWord={(senseId) => {
          // 1. Add to current layer (search history - word persists in grid)
          const isNewWord = !currentLayer.senses.includes(senseId)
          if (isNewWord) {
            const newSenses = [...currentLayer.senses, senseId]
            setCurrentLayer(prev => ({
              ...prev,
              senses: newSenses
            }))
            // Persist to IndexedDB so it survives refresh
            localStore.setCache(STARTER_PACK_CACHE_KEY, newSenses, STARTER_PACK_TTL)
              .catch(err => console.warn('Failed to persist search result to grid:', err))
          }
          
          // 2. Navigate to word detail page
          setIsSearchOpen(false)
          router.push(`/${locale}/learner/word/${encodeURIComponent(senseId)}`)
        }}
      />
      
      {/* Word Detail Modal (Emoji Pack) */}
      <EmojiWordDetail
        block={selectedBlock}
        isOpen={!!selectedWordId}
        onClose={() => setSelectedWordId(null)}
        onAddToSmelting={(senseId, word) => {
          addToQueue(senseId, word) // This function ALREADY handles all the complex cache stuff
          setSelectedWordId(null) // Close modal after adding
        }}
        onStartQuiz={(senseId) => {
          setSelectedWordId(null)
          router.push(`/${locale}/learner/verification`) // Simple navigation for MVP
        }}
      />
    </div>
  )
}
