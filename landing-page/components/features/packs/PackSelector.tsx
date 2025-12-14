'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore, selectActivePack } from '@/stores/useAppStore'
import { packLoader } from '@/lib/pack-loader'
import { VocabularyPack } from '@/lib/pack-types'

interface PackSelectorProps {
  onPackChange?: (packId: string) => void
}

/**
 * Pack Selector - Switch between vocabulary packs
 * 
 * Shows current pack and allows switching.
 * For MVP: Toggle between "Legacy" (old vocab) and "Emoji Core"
 */
export function PackSelector({ onPackChange }: PackSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [packs, setPacks] = useState<VocabularyPack[]>([])
  const activePack = useAppStore(selectActivePack)
  const setActivePack = useAppStore((s) => s.setActivePack)

  // Load available packs and auto-select emoji_core for MVP
  useEffect(() => {
    const loadPacks = async () => {
      const packIds = packLoader.getAvailablePacks()
      const loadedPacks: VocabularyPack[] = []
      
      for (const id of packIds) {
        const meta = await packLoader.getPackMetadata(id)
        if (meta) loadedPacks.push(meta)
      }
      
      // Add "legacy" option for old vocabulary
      loadedPacks.unshift({
        id: 'legacy',
        name: 'Legacy Vocabulary',
        name_zh: '傳統詞彙',
        description: 'Original vocabulary database',
        description_zh: '原始詞彙資料庫',
        emoji: '📚',
        difficulty: 3,
        word_count: 10000,
        categories: ['all'],
        is_free: true,
        sort_order: 0,
      })
      
      setPacks(loadedPacks)
      
      // Auto-select emoji_core for MVP if no pack is selected
      if (!activePack) {
        const emojiPack = loadedPacks.find(p => p.id === 'emoji_core')
        if (emojiPack) {
          console.log('🎯 Auto-selecting emoji_core pack for MVP')
          setActivePack({
            id: emojiPack.id,
            name: emojiPack.name,
            word_count: emojiPack.word_count
          })
          // Trigger the pack change callback to load emoji vocab
          onPackChange?.(emojiPack.id)
        }
      }
    }
    loadPacks()
  }, [activePack, setActivePack, onPackChange])

  const handleSelectPack = (pack: VocabularyPack) => {
    setActivePack({
      id: pack.id,
      name: pack.name,
      word_count: pack.word_count
    })
    setIsOpen(false)
    onPackChange?.(pack.id)
  }

  const currentPack = packs.find(p => p.id === activePack?.id) || packs[0]

  return (
    <div className="relative">
      {/* Current Pack Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-600 rounded-xl transition-colors"
      >
        <span className="text-xl">{currentPack?.emoji || '📦'}</span>
        <div className="text-left">
          <div className="text-sm font-medium text-white">
            {currentPack?.name_zh || '選擇詞彙包'}
          </div>
          <div className="text-xs text-slate-400">
            {currentPack?.word_count?.toLocaleString() || 0} 單字
          </div>
        </div>
        <svg 
          className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div 
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Pack List */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 z-50 bg-slate-800 border border-slate-600 rounded-xl shadow-xl overflow-hidden min-w-[280px]"
            >
              <div className="p-2 border-b border-slate-700">
                <p className="text-xs text-slate-400 px-2">選擇詞彙包</p>
              </div>
              
              <div className="max-h-[300px] overflow-y-auto">
                {packs.map((pack) => (
                  <button
                    key={pack.id}
                    onClick={() => handleSelectPack(pack)}
                    className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-700/50 transition-colors ${
                      activePack?.id === pack.id ? 'bg-cyan-500/10 border-l-2 border-cyan-400' : ''
                    }`}
                  >
                    <span className="text-2xl">{pack.emoji}</span>
                    <div className="flex-1 text-left">
                      <div className="font-medium text-white">{pack.name_zh}</div>
                      <div className="text-xs text-slate-400">{pack.name}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-cyan-400">
                          {pack.word_count.toLocaleString()} 單字
                        </span>
                        {pack.id === 'emoji_core' && (
                          <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] rounded-full">
                            推薦
                          </span>
                        )}
                        {pack.id === 'legacy' && (
                          <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-[10px] rounded-full">
                            進階
                          </span>
                        )}
                      </div>
                    </div>
                    {activePack?.id === pack.id && (
                      <span className="text-cyan-400">✓</span>
                    )}
                  </button>
                ))}
              </div>
              
              <div className="p-3 border-t border-slate-700 bg-slate-800/50">
                <p className="text-xs text-slate-500 text-center">
                  💡 推薦初學者使用「表情基礎」包
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PackSelector

