'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ITEM_CONFIGS, getBonusIcon, getBonusColor, type ItemFullConfig } from './itemConfig'
import { type ItemConfig } from './FurnitureItem'

// Level upgrade costs (same as in UpgradeModal)
const LEVEL_COSTS = [
  { energy: 0, essence: 0, blocks: 0 },
  { energy: 5, essence: 2, blocks: 0 },
  { energy: 15, essence: 5, blocks: 1 },
  { energy: 30, essence: 10, blocks: 3 },
  { energy: 50, essence: 20, blocks: 5 },
]

export interface ItemDetailModalProps {
  isOpen: boolean
  onClose: () => void
  itemConfig: ItemConfig
  currentLevel: number
  onSelectLevel?: (level: number) => void
}

export function ItemDetailModal({
  isOpen,
  onClose,
  itemConfig,
  currentLevel,
  onSelectLevel,
}: ItemDetailModalProps) {
  const [selectedPreviewLevel, setSelectedPreviewLevel] = useState(currentLevel)
  
  const fullConfig = ITEM_CONFIGS[itemConfig.code]
  if (!fullConfig) return null
  
  const selectedLevelDetail = fullConfig.levels[selectedPreviewLevel]
  const selectedEmoji = itemConfig.emoji_levels[Math.min(selectedPreviewLevel, itemConfig.emoji_levels.length - 1)]
  const selectedCost = LEVEL_COSTS[selectedPreviewLevel] || LEVEL_COSTS[LEVEL_COSTS.length - 1]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/80 z-40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-gradient-to-b from-gray-800 to-gray-900 rounded-3xl max-w-lg w-full max-h-[90vh] overflow-hidden border border-gray-600 shadow-2xl pointer-events-auto"
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header with close button */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
                <h2 className="text-xl font-bold text-white">
                  {fullConfig.name_zh}
                </h2>
                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-full bg-gray-700/50 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-600 transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* Scrollable content */}
              <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-6">
                {/* Big emoji display */}
                <div className="text-center mb-6">
                  <motion.div
                    key={selectedPreviewLevel}
                    className="text-9xl mb-4 drop-shadow-2xl"
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300 }}
                  >
                    {selectedEmoji}
                  </motion.div>
                  
                  <motion.div
                    key={`name-${selectedPreviewLevel}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <h3 className="text-2xl font-bold text-white mb-1">
                      {selectedLevelDetail?.name_zh || selectedLevelDetail?.name_en}
                    </h3>
                    <p className="text-gray-400 text-sm">
                      {selectedLevelDetail?.name_en}
                    </p>
                    <p className={`text-lg font-medium mt-2 ${
                      selectedPreviewLevel <= currentLevel ? 'text-green-400' : 'text-gray-500'
                    }`}>
                      Lv.{selectedPreviewLevel}
                      {selectedPreviewLevel === currentLevel && ' (目前)'}
                      {selectedPreviewLevel < currentLevel && ' ✓'}
                    </p>
                  </motion.div>
                </div>

                {/* Description */}
                <div className="bg-gray-800/50 rounded-xl p-4 mb-6">
                  <motion.div
                    key={`desc-${selectedPreviewLevel}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <p className="text-gray-200 mb-2">
                      {selectedLevelDetail?.description_zh}
                    </p>
                    <p className="text-gray-400 text-sm italic">
                      {selectedLevelDetail?.description_en}
                    </p>
                  </motion.div>
                </div>

                {/* Bonus display */}
                {selectedLevelDetail?.bonus && (
                  <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 rounded-xl p-4 mb-6 border border-yellow-600/30">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">等級加成</span>
                      <span className={`text-xl font-bold ${getBonusColor(selectedLevelDetail.bonus.type)}`}>
                        {getBonusIcon(selectedLevelDetail.bonus.type)} +{selectedLevelDetail.bonus.value.toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">
                      {selectedLevelDetail.bonus.type === 'sparks' && '火花獲得加成'}
                      {selectedLevelDetail.bonus.type === 'energy' && '能量獲得加成'}
                      {selectedLevelDetail.bonus.type === 'essence' && '精華獲得加成'}
                      {selectedLevelDetail.bonus.type === 'blocks' && '磚塊獲得加成'}
                    </p>
                  </div>
                )}

                {/* Cost for this level */}
                {selectedPreviewLevel > 0 && selectedPreviewLevel > currentLevel && (
                  <div className="bg-gray-800/30 rounded-xl p-4 mb-6">
                    <p className="text-sm text-gray-400 mb-2">升級至此等級所需</p>
                    <div className="flex items-center justify-center gap-4">
                      {selectedCost.energy > 0 && (
                        <span className="text-yellow-400 font-medium">⚡{selectedCost.energy}</span>
                      )}
                      {selectedCost.essence > 0 && (
                        <span className="text-cyan-400 font-medium">💧{selectedCost.essence}</span>
                      )}
                      {selectedCost.blocks > 0 && (
                        <span className="text-orange-400 font-medium">🧱{selectedCost.blocks}</span>
                      )}
                      {selectedCost.energy === 0 && selectedCost.essence === 0 && selectedCost.blocks === 0 && (
                        <span className="text-green-400 font-medium">🎁 免費</span>
                      )}
                    </div>
                  </div>
                )}

                {/* Level selector */}
                <div className="mb-4">
                  <p className="text-sm text-gray-400 mb-3">所有等級預覽</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {itemConfig.emoji_levels.map((emoji, idx) => {
                      const isPast = idx < currentLevel
                      const isCurrent = idx === currentLevel
                      const isSelected = idx === selectedPreviewLevel
                      
                      return (
                        <motion.button
                          key={idx}
                          onClick={() => setSelectedPreviewLevel(idx)}
                          className={`w-14 h-14 rounded-xl flex flex-col items-center justify-center transition-all ${
                            isSelected ? 'ring-2 ring-yellow-400 ring-offset-2 ring-offset-gray-900' : ''
                          } ${
                            isPast ? 'bg-green-900/30 border border-green-500/30' :
                            isCurrent ? 'bg-blue-900/30 border border-blue-500/30' :
                            'bg-gray-800/50 border border-gray-700'
                          }`}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <span className="text-2xl">{emoji}</span>
                          <span className={`text-[10px] font-medium ${
                            isPast ? 'text-green-400' :
                            isCurrent ? 'text-blue-400' :
                            'text-gray-500'
                          }`}>
                            Lv.{idx}
                          </span>
                        </motion.button>
                      )
                    })}
                  </div>
                </div>

                {/* Item general description */}
                <div className="text-center text-gray-500 text-sm border-t border-gray-700 pt-4">
                  <p>{fullConfig.description_zh}</p>
                  <p className="text-xs mt-1 italic">{fullConfig.description_en}</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default ItemDetailModal

