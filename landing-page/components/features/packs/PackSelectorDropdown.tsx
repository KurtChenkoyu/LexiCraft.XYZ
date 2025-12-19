'use client'

import React, { useEffect, useState } from 'react'
import { Lock } from 'lucide-react'
import { packLoader } from '@/lib/pack-loader'
import { VocabularyPack } from '@/lib/pack-types'
import { useAppStore, selectActivePack, selectActiveLearner } from '@/stores/useAppStore'

interface PackSelectorDropdownProps {
  onClose: () => void
}

/**
 * PackSelectorDropdown - Compact dropdown for switching packs
 * 
 * Positioned absolutely below the trigger button in the top bar.
 */
export function PackSelectorDropdown({ onClose }: PackSelectorDropdownProps) {
  const activePack = useAppStore(selectActivePack)
  const activeLearner = useAppStore(selectActiveLearner)
  const setActivePack = useAppStore((state) => state.setActivePack)
  const setMineDataLoaded = useAppStore((state) => state.setMineDataLoaded)
  const setEmojiVocabulary = useAppStore((state) => state.setEmojiVocabulary)
  const setEmojiProgress = useAppStore((state) => state.setEmojiProgress)
  const setEmojiMasteredWords = useAppStore((state) => state.setEmojiMasteredWords)
  const setEmojiStats = useAppStore((state) => state.setEmojiStats)
  
  const [packs, setPacks] = useState<VocabularyPack[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const loadPacks = async () => {
      setLoading(true)
      try {
        const packIds = packLoader.getAvailablePacks()
        const loadedPacks: VocabularyPack[] = []
        
        for (const packId of packIds) {
          const meta = await packLoader.getPackMetadata(packId)
          if (meta) {
            loadedPacks.push(meta)
          }
        }
        
        // Add legacy vocabulary option
        loadedPacks.push({
          id: 'legacy',
          name: 'Taiwan MOE 7000',
          name_zh: '教育部 7000 字',
          description: 'Full Taiwan Ministry of Education vocabulary',
          description_zh: '完整台灣教育部七千字詞彙庫',
          emoji: '📚',
          difficulty: 3,
          word_count: 10470,
          categories: ['academic'],
          is_free: true,
          sort_order: 99,
        })
        
        setPacks(loadedPacks)
      } catch (error) {
        console.error('Failed to load packs:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadPacks()
  }, [])
  
  const handleSelectPack = async (pack: VocabularyPack) => {
    // 1. Save preference to active learner profile (if selected)
    // TODO: Save to backend when player profile API is ready
    
    // 2. Clear pack-specific cached data
    // (For now, just log which learner is switching, if available)
    if (activeLearner) {
      console.log(`🔄 Switching pack for learner ${activeLearner.display_name}: ${pack.id}`)
    } else {
      console.log(`🔄 Switching pack (no active learner set): ${pack.id}`)
    }
    
    // 3. Clear emoji state if switching FROM emoji pack
    if (activePack?.id === 'emoji_core' && pack.id !== 'emoji_core') {
      setEmojiVocabulary(null)
      setEmojiProgress(null)
      setEmojiMasteredWords(null)
      setEmojiStats(null)
      console.log('🧹 Cleared emoji pack state (switching to legacy)')
    }
    
    // 4. Update active pack (triggers re-render)
    setActivePack({
      id: pack.id,
      name: pack.name_zh || pack.name,
      word_count: pack.word_count
    })
    
    // 5. Mark mine data as not loaded (forces reload)
    setMineDataLoaded(false)
    
    // 6. Clear vocabulary cache if switching to/from emoji pack
    if (activePack?.id === 'emoji_core' || pack.id === 'emoji_core') {
      // Clear emoji pack cache
      try {
        await packLoader.clearCache()
      } catch (error) {
        console.warn('Failed to clear pack cache:', error)
      }
    }
    
    onClose()
  }
  
  return (
    <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-56 bg-slate-800 rounded-xl border border-white/10 shadow-2xl overflow-hidden z-50">
      {/* Header */}
      <div className="px-3 py-2 border-b border-white/10 bg-slate-900/50">
        <span className="text-xs font-medium text-slate-400">選擇詞彙包</span>
      </div>
      
      {/* Pack List */}
      <div className="py-1">
        {loading ? (
          <div className="flex items-center justify-center py-4">
            <div className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
          </div>
        ) : (
          packs.map((pack) => {
            const isActive = activePack?.id === pack.id
            const isLegacy = pack.id === 'legacy' // MVP: Disable legacy pack
            const isLocked = !pack.is_free && pack.id !== 'emoji_core' && pack.id !== 'legacy' // Future: check if user has access
            
            return (
              <button
                key={pack.id}
                onClick={() => {
                  // MVP: Prevent legacy pack selection
                  if (isLegacy) return
                  if (!isLocked) handleSelectPack(pack)
                }}
                disabled={isLocked || isLegacy}
                className={`w-full px-3 py-2.5 flex items-center gap-2.5 text-left transition-colors ${
                  isLegacy
                    ? 'opacity-50 cursor-not-allowed'
                    : isLocked
                    ? 'opacity-50 cursor-not-allowed'
                    : isActive
                    ? 'bg-cyan-500/20 text-cyan-400'
                    : 'hover:bg-white/5 text-slate-300'
                }`}
              >
                <span className="text-lg">{pack.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium text-sm truncate">
                      {pack.name_zh}
                    </span>
                    {isActive && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-cyan-500 text-white rounded">
                        ✓
                      </span>
                    )}
                    {isLegacy && (
                      <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 bg-slate-700 text-slate-400 rounded border border-slate-600">
                        <Lock className="w-3 h-3" />
                        即將推出
                      </span>
                    )}
                    {isLocked && !isLegacy && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-slate-600 text-slate-400 rounded">
                        🔒
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-500">
                    {pack.word_count.toLocaleString()} 字
                  </span>
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}

export default PackSelectorDropdown


