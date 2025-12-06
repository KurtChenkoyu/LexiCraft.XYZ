'use client'

import { useEffect, useState, useMemo, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { vocabulary } from '@/lib/vocabulary'
import { progressApi, UserProgressResponse, BlockProgress } from '@/services/progressApi'
import { localStore } from '@/lib/local-store'
import { Block, UserStats } from '@/types/mine'
import { Spinner } from '@/components/ui'
import { MineHeader, BlockList, MineGraphG6, BlockDetailModal } from '@/components/features/mine'
import { BlockDetail } from '@/types/mine'

type ViewMode = 'list' | 'graph'

const STARTER_PACK_KEY = 'lexicraft_starter_pack_ids'

/**
 * Load starter pack from localStorage or generate new one
 */
function loadOrGenerateStarterPack(): Block[] {
  if (!vocabulary.isLoaded) return []

  // Try to load from localStorage
  if (typeof window !== 'undefined') {
    try {
      const saved = localStorage.getItem(STARTER_PACK_KEY)
      if (saved) {
        const senseIds: string[] = JSON.parse(saved)
        // Reconstruct blocks from saved sense IDs
        const blocks: Block[] = []
        for (const senseId of senseIds) {
          const detail = vocabulary.getBlockDetail(senseId)
          if (detail) {
            blocks.push({
              sense_id: detail.sense_id,
              word: detail.word,
              definition_preview: (detail.definition_en || '').slice(0, 100),
              tier: detail.tier,
              base_xp: detail.base_xp,
              connection_count: detail.connection_count,
              total_value: detail.total_value,
              status: 'raw',
              rank: detail.rank,
            })
          }
        }
        if (blocks.length > 0) {
          console.log('Loaded starter pack from localStorage:', blocks.length, 'blocks')
          return blocks
        }
      }
    } catch (err) {
      console.warn('Failed to load starter pack from localStorage:', err)
    }
  }

  // Generate new starter pack
  const newBlocks = vocabulary.getStarterPack(50)
  
  // Save to localStorage
  if (typeof window !== 'undefined') {
    try {
      const senseIds = newBlocks.map(b => b.sense_id)
      localStorage.setItem(STARTER_PACK_KEY, JSON.stringify(senseIds))
      console.log('Generated and saved new starter pack:', newBlocks.length, 'blocks')
    } catch (err) {
      console.warn('Failed to save starter pack to localStorage:', err)
    }
  }

  return newBlocks
}

export default function MinePage() {
  const t = useTranslations('mine')
  const [userProgress, setUserProgress] = useState<UserProgressResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [localBlocks, setLocalBlocks] = useState<Block[]>([])
  const [refreshKey, setRefreshKey] = useState(0)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedSenseId, setSelectedSenseId] = useState<string | null>(null)
  const [demoMode, setDemoMode] = useState(false)
  const [modalBlock, setModalBlock] = useState<BlockDetail | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Load starter pack (persisted or new)
  useEffect(() => {
    setLocalBlocks(loadOrGenerateStarterPack())
  }, [refreshKey])

  /**
   * Refresh starter pack with new random blocks
   */
  const handleRefreshSuggestions = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STARTER_PACK_KEY)
    }
    setRefreshKey(k => k + 1)
  }, [])

  // LOCAL-FIRST: Load progress from IndexedDB, then sync with server in background
  useEffect(() => {
    const loadProgress = async () => {
      try {
        setIsLoading(true)
        
        // 1. INSTANT: Load from local IndexedDB first
        const localProgress = await localStore.getAllProgress()
        
        if (localProgress.length > 0) {
          // Convert local progress to API format
          const progressData: BlockProgress[] = localProgress.map(p => ({
            sense_id: p.senseId,
            status: p.status,
            tier: p.tier,
            started_at: p.startedAt,
            mastery_level: p.masteryLevel,
          }))
          
          // Calculate stats from local data
          let solid = 0, hollow = 0
          for (const p of localProgress) {
            if (p.status === 'solid') solid++
            else if (p.status === 'hollow') hollow++
          }
          
          setUserProgress({
            progress: progressData,
            stats: {
              total_discovered: solid + hollow,
              solid_count: solid,
              hollow_count: hollow,
              raw_count: localBlocks.length - solid - hollow,
            }
          })
          setIsLoading(false)
        } else {
          // No local data, show empty state immediately
          setUserProgress({
            progress: [],
            stats: { total_discovered: 0, solid_count: 0, hollow_count: 0, raw_count: localBlocks.length }
          })
          setIsLoading(false)
        }
        
        // 2. BACKGROUND: Try to sync with server (non-blocking)
        progressApi.getUserProgress()
          .then(serverProgress => {
            if (serverProgress.progress.length > 0) {
              // Import server progress into local store
              localStore.importProgress(serverProgress.progress)
              setUserProgress(serverProgress)
            }
          })
          .catch(err => {
            // Silent fail - we have local data
            console.debug('Background sync failed (offline mode):', err.message)
          })
          
      } catch (err: any) {
        console.error('Failed to load progress:', err)
        setUserProgress({
          progress: [],
          stats: { total_discovered: 0, solid_count: 0, hollow_count: 0, raw_count: 0 }
        })
        setIsLoading(false)
      }
    }

    loadProgress()
  }, [localBlocks.length])

  // Enrich blocks with user progress status
  const enrichedBlocks = useMemo(() => {
    if (!userProgress) return localBlocks

    // Create progress lookup map
    const progressMap = new Map<string, BlockProgress>()
    for (const p of userProgress.progress) {
      progressMap.set(p.sense_id, p)
    }

    // Enrich blocks with status
    return localBlocks.map(block => {
      const progress = progressMap.get(block.sense_id)
      if (!progress) {
        return { ...block, status: 'raw' as const }
      }

      // Map backend status to block status
      let status: 'raw' | 'hollow' | 'solid' = 'raw'
      if (progress.status === 'verified' || progress.status === 'mastered' || progress.status === 'solid') {
        status = 'solid'
      } else if (progress.status === 'learning' || progress.status === 'pending' || progress.status === 'hollow') {
        status = 'hollow'
      }

      return { ...block, status }
    })
  }, [localBlocks, userProgress])

  // Calculate user stats
  const userStats: UserStats = useMemo(() => {
    if (userProgress?.stats) {
      return userProgress.stats
    }

    // Calculate from enriched blocks
    let solid = 0, hollow = 0, raw = 0
    for (const block of enrichedBlocks) {
      if (block.status === 'solid') solid++
      else if (block.status === 'hollow') hollow++
      else raw++
    }

    return {
      total_discovered: solid + hollow,
      solid_count: solid,
      hollow_count: hollow,
      raw_count: raw,
    }
  }, [userProgress, enrichedBlocks])

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
  const handleGraphNodeSelect = useCallback((nodeId: string) => {
    console.log('🔥 handleGraphNodeSelect called with:', nodeId)
    
    // Handle both formats: sense_id (e.g., "drop.v.01") and word_pos (e.g., "drop_verb")
    let blockDetail: BlockDetail | null = null
    let senseId: string | null = null
    
    if (nodeId.includes('_') && !nodeId.includes('.')) {
      // Cytoscape format: word_pos (e.g., "total_v", "just_r")
      const parts = nodeId.split('_')
      const pos = parts.pop() // Last part is POS
      const word = parts.join('_') // Handle words with underscores
      
      console.log('Looking up word:', word, 'pos:', pos)
      
      // Try to find any sense for this word
      const allSenses = vocabulary.getAllSenses()
      
      // Find senses that match this word
      const matchingSenses = Object.values(allSenses).filter((sense: any) => 
        sense.word?.toLowerCase() === word?.toLowerCase()
      )
      
      console.log('Found senses for word:', matchingSenses.length)
      
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
          senseId = matchedSense.id
          console.log('Matched sense:', senseId)
          blockDetail = vocabulary.getBlockDetail(senseId)
        }
      }
    } else {
      // Direct sense_id format (e.g., "drop.v.01")
      senseId = nodeId
      blockDetail = vocabulary.getBlockDetail(nodeId)
    }
    
    console.log('Block detail:', blockDetail ? 'found' : 'NOT FOUND')
    
    if (blockDetail) {
      setSelectedSenseId(senseId)
      setModalBlock(blockDetail)
      setIsModalOpen(true)
    } else {
      // Show a simple info for now
      const [word] = nodeId.split('_')
      alert(`詞彙: ${word}\n\n(詳細資料載入中...)`)
    }
  }, [])

  // Handle start forging directly from graph (without opening modal)
  const handleStartForging = useCallback((nodeId: string) => {
    console.log('🔥 handleStartForging called with:', nodeId)
    
    // Parse word_pos format (e.g., "drop_verb")
    const parts = nodeId.split('_')
    const pos = parts.pop()
    const word = parts.join('_')
    
    // Find the sense_id for this word
    const allSenses = vocabulary.getAllSenses()
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
    
    const matchingSenses = Object.values(allSenses).filter((sense: any) => 
      sense.word?.toLowerCase() === word?.toLowerCase()
    )
    
    const matchingPosValues = posMap[pos || ''] || [pos]
    const matchedSense = matchingSenses.find((s: any) => 
      matchingPosValues.some(p => s.pos === p || s.pos?.toLowerCase() === p)
    ) || matchingSenses[0]
    
    if (matchedSense) {
      const senseId = (matchedSense as any).id
      console.log('Starting forging for sense:', senseId)
      
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

  // Check if vocabulary is loaded
  if (!vocabulary.isLoaded) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <div className="bg-amber-500/20 border border-amber-500/50 rounded-xl p-8">
            <p className="text-amber-800 text-lg">
              詞彙資料尚未載入。請先執行 export_vocabulary_json.py 腳本。
            </p>
          </div>
        </div>
      </main>
    )
  }

  // Show loading only while fetching user progress
  if (isLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" className="text-cyan-600 mb-4" />
          <p className="text-gray-600 text-lg">載入進度中...</p>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20">
        <div className="max-w-6xl mx-auto px-4 text-center">
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
      </main>
    )
  }

  const isGraphView = viewMode === 'graph'

  return (
    <main className={`min-h-screen ${isGraphView ? 'bg-slate-900' : 'bg-gradient-to-br from-slate-50 to-slate-100'} pt-20 pb-20`}>
      <div className={isGraphView ? 'max-w-full px-4' : 'max-w-6xl mx-auto px-4 sm:px-6 lg:px-8'}>
        {/* Header with view toggle */}
        <div className="mb-6 flex items-center justify-between">
        <MineHeader
            mode="starter"
            userStats={userStats}
            onRefreshSuggestions={viewMode === 'list' ? handleRefreshSuggestions : undefined}
          />
        </div>

        {/* View toggle */}
        <div className="flex justify-center mb-6 gap-4">
          <div className={`inline-flex rounded-xl p-1 ${isGraphView ? 'bg-slate-800' : 'bg-white shadow-lg'}`}>
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
              🕸️ 詞彙網絡
            </button>
          </div>
          
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
        {viewMode === 'list' ? (
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

      {/* Block Detail Modal */}
      {isModalOpen && (
        <BlockDetailModal
          blockDetail={modalBlock}
          isLoading={false}
          onClose={() => {
            setIsModalOpen(false)
            setModalBlock(null)
            setSelectedSenseId(null)
          }}
          onStatusChange={(senseId, status) => {
            // Update progress in local state
            setUserProgress(prev => {
              if (!prev) return null
              const existingIndex = prev.progress.findIndex(p => p.sense_id === senseId)
              if (existingIndex >= 0) {
                const updated = [...prev.progress]
                updated[existingIndex] = { ...updated[existingIndex], status }
                return { ...prev, progress: updated }
              } else {
                return {
                  ...prev,
                  progress: [...prev.progress, { sense_id: senseId, status }]
                }
              }
            })
          }}
        />
      )}
    </main>
  )
}
