'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Lock } from 'lucide-react'
import { packLoader } from '@/lib/pack-loader'
import { VocabularyPack } from '@/lib/pack-types'
import { useAppStore, selectActivePack } from '@/stores/useAppStore'

interface PackSelectorModalProps {
  onClose: () => void
}

export function PackSelectorModal({ onClose }: PackSelectorModalProps) {
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
          name_zh: '台灣教育部 7000 字',
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
    setActivePack({
      id: pack.id,
      name: pack.name_zh || pack.name,
      word_count: pack.word_count,
      emoji: pack.emoji
    })
    setMineDataLoaded(false)
    onClose()
  }
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md overflow-hidden shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-6 py-4 border-b border-white/10">
            <h2 className="text-xl font-bold text-white">選擇詞彙包</h2>
            <p className="text-sm text-slate-400 mt-1">選擇你想要學習的詞彙</p>
          </div>
          
          <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
              </div>
            ) : (
              packs.map((pack) => {
                const isActive = activePack?.id === pack.id
                const isLegacy = pack.id === 'legacy' // MVP: Disable legacy pack
                
                return (
                  <button
                    key={pack.id}
                    onClick={() => {
                      // MVP: Prevent legacy pack selection
                      if (isLegacy) return
                      handleSelectPack(pack)
                    }}
                    disabled={isLegacy}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                      isLegacy
                        ? 'opacity-50 cursor-not-allowed bg-slate-800/30 border-slate-700'
                        : isActive
                        ? 'bg-cyan-500/20 border-cyan-500 shadow-lg shadow-cyan-500/20'
                        : 'bg-slate-800/50 border-slate-700 hover:border-slate-500'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-3xl">{pack.emoji}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-white truncate">
                            {pack.name_zh}
                          </h3>
                          {isActive && (
                            <span className="px-2 py-0.5 text-xs bg-cyan-500 text-white rounded-full">
                              使用中
                            </span>
                          )}
                          {isLegacy && (
                            <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-slate-700 text-slate-400 rounded-full border border-slate-600">
                              <Lock className="w-3 h-3" />
                              即將推出
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-400 mt-0.5">
                          {pack.name}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {pack.word_count.toLocaleString()} 單字
                        </p>
                      </div>
                    </div>
                  </button>
                )
              })
            )}
          </div>
          
          <div className="px-6 py-4 border-t border-white/10 bg-slate-800/50">
            <button
              onClick={onClose}
              className="w-full py-3 text-slate-400 hover:text-white transition-colors font-medium"
            >
              取消
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default PackSelectorModal


