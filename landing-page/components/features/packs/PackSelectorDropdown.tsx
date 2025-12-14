'use client'

import React, { useEffect, useState } from 'react'
import { packLoader } from '@/lib/pack-loader'
import { VocabularyPack } from '@/lib/pack-types'
import { useAppStore, selectActivePack } from '@/stores/useAppStore'

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
  const setActivePack = useAppStore((state) => state.setActivePack)
  const setMineDataLoaded = useAppStore((state) => state.setMineDataLoaded)
  
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
  
  const handleSelectPack = (pack: VocabularyPack) => {
    setActivePack(pack)
    setMineDataLoaded(false)
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
            
            return (
              <button
                key={pack.id}
                onClick={() => handleSelectPack(pack)}
                className={`w-full px-3 py-2.5 flex items-center gap-2.5 text-left transition-colors ${
                  isActive
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


