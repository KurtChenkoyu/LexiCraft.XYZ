'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { type ItemConfig } from './FurnitureItem'
import { ITEM_CONFIGS, getBonusIcon, getBonusColor } from './itemConfig'

export interface UpgradeCost {
  energy: number
  essence: number
  blocks: number
}

export interface UserCurrencies {
  energy: number
  essence: number
  blocks: number
}

export interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
  onUpgrade: () => Promise<void>
  itemConfig: ItemConfig
  currentLevel: number
  nextLevel: number
  currentEmoji: string
  nextEmoji: string
  upgradeCost: UpgradeCost
  userCurrencies: UserCurrencies
  isUpgrading?: boolean
  onViewDetail?: (level: number) => void
}

// Upgrade costs by level (L0→L1, L1→L2, etc.)
const LEVEL_COSTS: UpgradeCost[] = [
  { energy: 0, essence: 0, blocks: 0 },     // L0→L1 (Free starter)
  { energy: 5, essence: 2, blocks: 0 },     // L1→L2
  { energy: 15, essence: 5, blocks: 1 },    // L2→L3
  { energy: 30, essence: 10, blocks: 3 },   // L3→L4
  { energy: 50, essence: 20, blocks: 5 },   // L4→L5
]

export function UpgradeModal({
  isOpen,
  onClose,
  onUpgrade,
  itemConfig,
  currentLevel,
  nextLevel,
  currentEmoji,
  nextEmoji,
  upgradeCost,
  userCurrencies,
  isUpgrading = false,
  onViewDetail,
}: UpgradeModalProps) {
  const [upgradeSuccess, setUpgradeSuccess] = useState(false)
  const [showAllLevels, setShowAllLevels] = useState(false)
  const [detailLevel, setDetailLevel] = useState<number | null>(null)
  
  // Get item full config for descriptions and bonuses
  const fullConfig = ITEM_CONFIGS[itemConfig.code]

  const canAfford = {
    energy: userCurrencies.energy >= upgradeCost.energy,
    essence: userCurrencies.essence >= upgradeCost.essence,
    blocks: userCurrencies.blocks >= upgradeCost.blocks,
  }
  const canUpgrade = canAfford.energy && canAfford.essence && canAfford.blocks

  const handleUpgrade = async () => {
    if (!canUpgrade || isUpgrading) return
    
    // Instant optimistic UI feedback
    setUpgradeSuccess(true)
    
    try {
      await onUpgrade()
      // Success - close after brief celebration
      setTimeout(() => {
        setUpgradeSuccess(false)
        onClose()
      }, 1200)
    } catch (error) {
      console.error('Upgrade failed:', error)
      setUpgradeSuccess(false)
    }
  }

  const costItems = [
    { icon: '⚡', label: '能量', cost: upgradeCost.energy, have: userCurrencies.energy, canAfford: canAfford.energy, color: 'text-yellow-400' },
    { icon: '💧', label: '精華', cost: upgradeCost.essence, have: userCurrencies.essence, canAfford: canAfford.essence, color: 'text-cyan-400' },
    { icon: '🧱', label: '磚塊', cost: upgradeCost.blocks, have: userCurrencies.blocks, canAfford: canAfford.blocks, color: 'text-orange-400' },
  ]

  // Only show costs that are > 0
  const activeCosts = costItems.filter(c => c.cost > 0)

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/70 z-40 backdrop-blur-sm"
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
              className="bg-gradient-to-b from-gray-800 to-gray-900 rounded-3xl p-6 max-w-sm w-full border border-gray-600 shadow-2xl pointer-events-auto overflow-hidden"
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Success state - BIG celebration */}
              {upgradeSuccess ? (
                <motion.div
                  className="text-center py-6"
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                >
                  {/* Confetti background */}
                  <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    {[...Array(20)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="absolute w-3 h-3 rounded-full"
                        style={{
                          left: `${Math.random() * 100}%`,
                          top: -10,
                          backgroundColor: ['#fbbf24', '#34d399', '#60a5fa', '#f472b6'][i % 4],
                        }}
                        animate={{
                          y: [0, 400],
                          x: [0, (Math.random() - 0.5) * 100],
                          rotate: [0, 360],
                          opacity: [1, 0],
                        }}
                        transition={{
                          duration: 1.5,
                          delay: i * 0.05,
                          ease: 'easeOut',
                        }}
                      />
                    ))}
                  </div>
                  
                  <motion.div
                    className="text-8xl mb-4 drop-shadow-2xl"
                    animate={{ 
                      scale: [1, 1.3, 1],
                      rotate: [0, -10, 10, 0],
                    }}
                    transition={{ duration: 0.6 }}
                  >
                    {nextEmoji}
                  </motion.div>
                  <motion.h3 
                    className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400 mb-2"
                    animate={{ scale: [0.8, 1.1, 1] }}
                  >
                    升級成功！
                  </motion.h3>
                  <p className="text-gray-300 text-lg">
                    {itemConfig.name_zh || itemConfig.name_en} <span className="text-green-400 font-bold">Lv.{nextLevel}</span>
                  </p>
                </motion.div>
              ) : (
                <>
                  {/* Header with item name */}
                  <div className="text-center mb-4">
                    <p className="text-gray-400 text-sm mb-1">升級物品</p>
                    <h2 className="text-2xl font-bold text-white">
                      {itemConfig.name_zh || itemConfig.name_en}
                    </h2>
                  </div>

                  {/* BIG Level comparison - more visual impact */}
                  <div className="flex items-center justify-center gap-3 mb-4 py-4 bg-gray-800/50 rounded-2xl">
                    {/* Current */}
                    <div className="text-center">
                      <motion.div 
                        className="text-5xl mb-1 grayscale-[30%] opacity-70"
                        animate={{ scale: [1, 0.95, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      >
                        {currentEmoji}
                      </motion.div>
                      <p className="text-sm text-gray-500 font-medium">Lv.{currentLevel}</p>
                    </div>

                    {/* Arrow with glow */}
                    <motion.div
                      className="text-4xl"
                      animate={{ x: [0, 8, 0], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                    >
                      <span className="text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">→</span>
                    </motion.div>

                    {/* Next - highlighted */}
                    <div className="text-center relative">
                      <motion.div
                        className="text-6xl mb-1 drop-shadow-[0_0_20px_rgba(52,211,153,0.4)]"
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      >
                        {nextEmoji}
                      </motion.div>
                      <p className="text-sm text-green-400 font-bold">Lv.{nextLevel}</p>
                      {/* Glow ring */}
                      <motion.div
                        className="absolute inset-0 -m-2 rounded-full border-2 border-green-400/30"
                        animate={{ scale: [1, 1.2], opacity: [0.5, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      />
                    </div>
                  </div>

                  {/* Cost breakdown - compact */}
                  {activeCosts.length > 0 ? (
                    <div className="bg-gray-800/30 rounded-xl p-3 mb-3">
                      <div className="flex items-center justify-center gap-4">
                        {activeCosts.map((item) => (
                          <div
                            key={item.label}
                            className={`flex items-center gap-1.5 ${item.canAfford ? '' : 'text-red-400'}`}
                          >
                            <span className="text-lg">{item.icon}</span>
                            <span className={`font-bold ${item.canAfford ? item.color : 'text-red-400'}`}>
                              {item.cost}
                            </span>
                            {item.canAfford ? (
                              <span className="text-green-400 text-sm">✓</span>
                            ) : (
                              <span className="text-red-400 text-xs">({item.have})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-green-900/20 rounded-xl p-3 mb-3 text-center">
                      <span className="text-green-400 font-medium">🎁 免費升級！</span>
                    </div>
                  )}

                  {/* Level Roadmap - collapsible with detail view */}
                  <div className="mb-4">
                    <button
                      onClick={() => {
                        setShowAllLevels(!showAllLevels)
                        setDetailLevel(null)
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 bg-gray-800/30 rounded-xl text-sm text-gray-400 hover:bg-gray-800/50 transition-colors"
                    >
                      <span>📊 查看所有等級</span>
                      <motion.span
                        animate={{ rotate: showAllLevels ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        ▼
                      </motion.span>
                    </button>
                    
                    <AnimatePresence>
                      {showAllLevels && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-2 p-3 bg-gray-800/20 rounded-xl space-y-2 max-h-64 overflow-y-auto">
                            {itemConfig.emoji_levels.map((emoji, idx) => {
                              const levelCost = LEVEL_COSTS[idx] || LEVEL_COSTS[LEVEL_COSTS.length - 1]
                              const isCurrentLevel = idx === currentLevel
                              const isPastLevel = idx < currentLevel
                              const isNextLevel = idx === nextLevel
                              const isSelected = detailLevel === idx
                              const levelDetail = fullConfig?.levels[idx]
                              
                              return (
                                <div key={idx}>
                                  {/* Level row - clickable */}
                                  <button
                                    onClick={() => setDetailLevel(isSelected ? null : idx)}
                                    className={`w-full flex items-center justify-between px-2 py-2 rounded-lg transition-all ${
                                      isSelected ? 'bg-purple-900/40 border border-purple-500/40' :
                                      isCurrentLevel ? 'bg-blue-900/30 border border-blue-500/30' :
                                      isNextLevel ? 'bg-green-900/30 border border-green-500/30' :
                                      isPastLevel ? 'opacity-60 hover:opacity-80' : 'hover:bg-gray-800/40'
                                    }`}
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className="text-2xl">{emoji}</span>
                                      <div className="text-left">
                                        <span className={`text-sm font-medium ${
                                          isCurrentLevel ? 'text-blue-400' :
                                          isNextLevel ? 'text-green-400' :
                                          'text-gray-400'
                                        }`}>
                                          Lv.{idx}
                                          {isCurrentLevel && <span className="ml-1 text-xs">(目前)</span>}
                                          {isNextLevel && <span className="ml-1 text-xs">(下一級)</span>}
                                        </span>
                                        {levelDetail?.name_zh && (
                                          <p className="text-xs text-gray-500">{levelDetail.name_zh}</p>
                                        )}
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-center gap-2">
                                      {idx > 0 && !isPastLevel && (
                                        <div className="flex items-center gap-1.5 text-xs">
                                          {levelCost.energy > 0 && <span className="text-yellow-400">⚡{levelCost.energy}</span>}
                                          {levelCost.essence > 0 && <span className="text-cyan-400">💧{levelCost.essence}</span>}
                                          {levelCost.blocks > 0 && <span className="text-orange-400">🧱{levelCost.blocks}</span>}
                                          {levelCost.energy === 0 && levelCost.essence === 0 && levelCost.blocks === 0 && (
                                            <span className="text-green-400">免費</span>
                                          )}
                                        </div>
                                      )}
                                      {isPastLevel && (
                                        <span className="text-green-400 text-sm">✓</span>
                                      )}
                                      <span className={`text-xs transition-transform ${isSelected ? 'rotate-90' : ''}`}>
                                        →
                                      </span>
                                    </div>
                                  </button>
                                  
                                  {/* Detail panel - expands on click */}
                                  <AnimatePresence>
                                    {isSelected && levelDetail && (
                                      <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.15 }}
                                        className="overflow-hidden"
                                      >
                                        <div className="mt-1 p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
                                          {/* Big emoji */}
                                          <div className="text-center mb-2">
                                            <span className="text-5xl">{emoji}</span>
                                          </div>
                                          
                                          {/* Name */}
                                          <h4 className="text-center font-bold text-white mb-1">
                                            {levelDetail.name_zh || levelDetail.name_en}
                                          </h4>
                                          <p className="text-center text-xs text-gray-500 mb-2">
                                            {levelDetail.name_en}
                                          </p>
                                          
                                          {/* Description */}
                                          <p className="text-sm text-gray-300 text-center mb-2">
                                            {levelDetail.description_zh}
                                          </p>
                                          <p className="text-xs text-gray-500 italic text-center mb-3">
                                            {levelDetail.description_en}
                                          </p>
                                          
                                          {/* Bonus */}
                                          {levelDetail.bonus && (
                                            <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 rounded-lg p-2 text-center border border-yellow-600/20">
                                              <span className="text-sm text-gray-300">等級加成: </span>
                                              <span className={`font-bold ${getBonusColor(levelDetail.bonus.type)}`}>
                                                {getBonusIcon(levelDetail.bonus.type)} +{levelDetail.bonus.value.toFixed(1)}%
                                              </span>
                                            </div>
                                          )}
                                        </div>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              )
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Buttons */}
                  <div className="flex gap-3">
                    <button
                      onClick={onClose}
                      className="flex-1 px-4 py-3 rounded-xl bg-gray-700/50 text-gray-300 hover:bg-gray-700 transition-colors font-medium"
                      disabled={isUpgrading}
                    >
                      稍後再說
                    </button>
                    <motion.button
                      onClick={handleUpgrade}
                      disabled={!canUpgrade || isUpgrading}
                      className={`flex-1 px-4 py-3 rounded-xl font-bold transition-all ${
                        canUpgrade
                          ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg shadow-green-500/25 hover:shadow-green-500/40'
                          : 'bg-gray-700 text-gray-400'
                      }`}
                      whileHover={canUpgrade ? { scale: 1.02, y: -1 } : {}}
                      whileTap={canUpgrade ? { scale: 0.98 } : {}}
                    >
                      {isUpgrading ? (
                        <span className="flex items-center justify-center gap-2">
                          <motion.span
                            animate={{ rotate: 360 }}
                            transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                          >
                            ⚡
                          </motion.span>
                          升級中
                        </span>
                      ) : canUpgrade ? (
                        <span className="flex items-center justify-center gap-1">
                          <span>✨</span> 立即升級
                        </span>
                      ) : (
                        '需要更多資源'
                      )}
                    </motion.button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default UpgradeModal
