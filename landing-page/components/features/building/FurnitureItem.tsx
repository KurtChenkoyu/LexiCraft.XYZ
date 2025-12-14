'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ITEM_CONFIGS, getTotalBonus, getBonusIcon, getBonusColor } from './itemConfig'

// Color schemes for different item types
const ITEM_COLOR_SCHEMES: Record<string, {
  primary: string
  secondary: string
  accent: string
  glow?: string
}[]> = {
  desk: [
    { primary: '#8B4513', secondary: '#A0522D', accent: '#D2691E' }, // L1 - Cardboard
    { primary: '#DEB887', secondary: '#D2B48C', accent: '#F5DEB3' }, // L2 - Folding
    { primary: '#8B7355', secondary: '#A08060', accent: '#C4A77D' }, // L3 - Wooden
    { primary: '#4A0E0E', secondary: '#6B1A1A', accent: '#8B0000', glow: 'rgba(139, 0, 0, 0.3)' }, // L4 - Executive
    { primary: '#1E3A5F', secondary: '#2E5A8F', accent: '#4169E1', glow: 'rgba(65, 105, 225, 0.5)' }, // L5 - Hover
  ],
  lamp: [
    { primary: '#4A4A4A', secondary: '#5A5A5A', accent: '#FFD700' }, // L1 - Bare bulb
    { primary: '#556B2F', secondary: '#6B8E23', accent: '#9ACD32' }, // L2 - Simple
    { primary: '#B8860B', secondary: '#DAA520', accent: '#FFD700' }, // L3 - Fancy
    { primary: '#4B0082', secondary: '#663399', accent: '#9370DB', glow: 'rgba(147, 112, 219, 0.4)' }, // L4 - Magic
  ],
  chair: [
    { primary: '#696969', secondary: '#808080', accent: '#A9A9A9' }, // L1 - Basic
    { primary: '#8B4513', secondary: '#A0522D', accent: '#D2691E' }, // L2 - Wood
    { primary: '#FFD700', secondary: '#FFA500', accent: '#FF8C00', glow: 'rgba(255, 215, 0, 0.3)' }, // L3 - Throne
  ],
  bookshelf: [
    { primary: '#5D4E37', secondary: '#6B5B45', accent: '#8B7355' }, // L1 - Basic
    { primary: '#704214', secondary: '#8B5A2B', accent: '#A0522D' }, // L2 - Full
    { primary: '#3C1414', secondary: '#5C2424', accent: '#8B0000' }, // L3 - Mahogany
    { primary: '#1E3A5F', secondary: '#2E4A6F', accent: '#4169E1', glow: 'rgba(65, 105, 225, 0.3)' }, // L4 - Library
  ],
  plant: [
    { primary: '#228B22', secondary: '#32CD32', accent: '#90EE90' }, // L1 - Seedling
    { primary: '#2E8B57', secondary: '#3CB371', accent: '#66CDAA' }, // L2 - Growing
    { primary: '#006400', secondary: '#008000', accent: '#00FF00' }, // L3 - Potted
    { primary: '#556B2F', secondary: '#6B8E23', accent: '#9ACD32', glow: 'rgba(154, 205, 50, 0.3)' }, // L4 - Tree
  ],
  coffee_table: [
    { primary: '#8B7355', secondary: '#A08060', accent: '#C4A77D' }, // L1 - Basic
    { primary: '#5D4E37', secondary: '#6B5B45', accent: '#8B7355' }, // L2 - Nice
    { primary: '#B8860B', secondary: '#DAA520', accent: '#FFD700', glow: 'rgba(218, 165, 32, 0.2)' }, // L3 - Fancy
  ],
  tv: [
    { primary: '#1C1C1C', secondary: '#2C2C2C', accent: '#3C3C3C' }, // L1 - Basic
    { primary: '#2F4F4F', secondary: '#3F5F5F', accent: '#4F6F6F' }, // L2 - Nice
    { primary: '#191970', secondary: '#000080', accent: '#0000CD', glow: 'rgba(0, 0, 205, 0.2)' }, // L3 - Home theater
    { primary: '#8B0000', secondary: '#B22222', accent: '#DC143C', glow: 'rgba(220, 20, 60, 0.3)' }, // L4 - Cinema
  ],
  sofa: [
    { primary: '#808080', secondary: '#909090', accent: '#A0A0A0' }, // L1 - Basic
    { primary: '#8B4513', secondary: '#A0522D', accent: '#D2691E' }, // L2 - Leather
    { primary: '#800080', secondary: '#9932CC', accent: '#BA55D3', glow: 'rgba(186, 85, 211, 0.2)' }, // L3 - Royal
    { primary: '#FFD700', secondary: '#FFA500', accent: '#FF8C00', glow: 'rgba(255, 215, 0, 0.4)' }, // L4 - Palace
  ],
}

// Default color scheme for unknown items
const DEFAULT_COLORS = [
  { primary: '#666666', secondary: '#777777', accent: '#888888' },
  { primary: '#777777', secondary: '#888888', accent: '#999999' },
  { primary: '#888888', secondary: '#999999', accent: '#AAAAAA' },
  { primary: '#999999', secondary: '#AAAAAA', accent: '#BBBBBB' },
  { primary: '#AAAAAA', secondary: '#BBBBBB', accent: '#CCCCCC' },
]

export interface ItemConfig {
  code: string
  name_en: string
  name_zh?: string
  emoji_levels: string[]
  max_level: number
}

export interface FurnitureItemProps {
  config: ItemConfig
  currentLevel: number
  size?: 'sm' | 'md' | 'lg'
  onClick?: () => void
  isSelected?: boolean
  canUpgrade?: boolean
  showLabel?: boolean
}

export function FurnitureItem({
  config,
  currentLevel,
  size = 'md',
  onClick,
  isSelected = false,
  canUpgrade = false,
  showLabel = true,
}: FurnitureItemProps) {
  const [displayedLevel, setDisplayedLevel] = useState(currentLevel)
  const [changeDirection, setChangeDirection] = useState<'up' | 'down' | null>(null)
  const [showTooltip, setShowTooltip] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Get bonus info
  const itemBonus = getTotalBonus(config.code, currentLevel)
  const itemFullConfig = ITEM_CONFIGS[config.code]
  const levelDetail = itemFullConfig?.levels[currentLevel]
  
  // Handle tap to toggle tooltip (for mobile)
  const handleTap = () => {
    // Clear any pending timeout
    if (tooltipTimeoutRef.current) {
      clearTimeout(tooltipTimeoutRef.current)
    }
    
    if (!showTooltip) {
      setShowTooltip(true)
      // Auto-hide after 3 seconds
      tooltipTimeoutRef.current = setTimeout(() => {
        setShowTooltip(false)
      }, 3000)
    } else {
      setShowTooltip(false)
    }
    
    // Still call onClick to open upgrade modal
    onClick?.()
  }

  // Get color scheme for this item
  const colorSchemes = ITEM_COLOR_SCHEMES[config.code] || DEFAULT_COLORS
  const colors = colorSchemes[Math.min(currentLevel, colorSchemes.length - 1)] || colorSchemes[0]
  
  // Get current emoji
  const currentEmoji = config.emoji_levels[Math.min(currentLevel, config.emoji_levels.length - 1)] || '❓'
  
  // Is max level?
  const isMaxLevel = currentLevel >= config.max_level

  // Detect level changes
  useEffect(() => {
    if (currentLevel !== displayedLevel) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      const direction = currentLevel > displayedLevel ? 'up' : 'down'
      setChangeDirection(direction)
      setDisplayedLevel(currentLevel)
      
      timeoutRef.current = setTimeout(() => {
        setChangeDirection(null)
      }, 400)
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [currentLevel, displayedLevel])

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  }

  const emojiSizes = {
    sm: 'text-2xl',
    md: 'text-4xl',
    lg: 'text-6xl',
  }

  const badgeSizes = {
    sm: 'w-5 h-5 text-xs -top-1 -right-1',
    md: 'w-6 h-6 text-xs -top-1 -right-1',
    lg: 'w-8 h-8 text-sm -top-2 -right-2',
  }

  return (
    <div className="flex flex-col items-center gap-2 relative">
      {/* Bonus Tooltip */}
      <AnimatePresence>
        {showTooltip && (itemBonus || levelDetail) && (
          <motion.div
            className="absolute -top-16 left-1/2 -translate-x-1/2 z-50 bg-gray-900/95 backdrop-blur-sm border border-gray-600 rounded-lg px-3 py-2 shadow-xl pointer-events-none whitespace-nowrap"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.15 }}
          >
            <div className="text-center">
              <p className="text-xs text-gray-300 mb-1">
                {levelDetail?.name_zh || levelDetail?.name_en || config.name_zh || config.name_en}
              </p>
              {itemBonus && (
                <p className={`text-sm font-bold ${getBonusColor(itemBonus.type)}`}>
                  {getBonusIcon(itemBonus.type)} +{itemBonus.value.toFixed(1)}%
                </p>
              )}
            </div>
            {/* Arrow */}
            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900/95 border-r border-b border-gray-600 transform rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        className={`relative ${sizeClasses[size]} rounded-xl flex items-center justify-center overflow-hidden cursor-pointer transition-all ${
          isSelected ? 'ring-2 ring-yellow-400 ring-offset-2 ring-offset-gray-900' : ''
        } ${canUpgrade ? 'animate-pulse' : ''}`}
        onClick={handleTap}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onTouchStart={() => {
          // Show tooltip on touch start
          setShowTooltip(true)
        }}
        animate={{
          background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`,
          boxShadow: colors.glow 
            ? `0 0 20px ${colors.glow}, 0 0 40px ${colors.glow}`
            : '0 4px 12px rgba(0,0,0,0.3)',
          scale: changeDirection === 'up' ? [1, 1.15, 1] : changeDirection === 'down' ? [1, 0.9, 1] : 1,
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        transition={{ 
          duration: 0.3,
          background: { duration: 0.4 },
        }}
      >
        {/* Glow effect for high levels */}
        <AnimatePresence>
          {colors.glow && (
            <motion.div
              key={`glow-${currentLevel}`}
              className="absolute inset-0 rounded-xl"
              style={{
                background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: [0.4, 0.7, 0.4] }}
              exit={{ opacity: 0 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            />
          )}
        </AnimatePresence>

        {/* Emoji */}
        <motion.span
          key={`emoji-${currentLevel}`}
          className={`${emojiSizes[size]} relative z-10`}
          initial={{ scale: 0.3, opacity: 0 }}
          animate={{ 
            scale: 1, 
            opacity: 1,
            y: isMaxLevel ? [0, -4, 0] : 0,
          }}
          transition={{
            scale: { type: 'spring', stiffness: 400, damping: 15 },
            opacity: { duration: 0.2 },
            y: isMaxLevel ? { duration: 2, repeat: Infinity, ease: 'easeInOut' } : undefined,
          }}
        >
          {currentEmoji}
        </motion.span>

        {/* Level badge */}
        <motion.div 
          className={`absolute ${badgeSizes[size]} rounded-full flex items-center justify-center text-white font-bold shadow-lg`}
          animate={{ 
            backgroundColor: colors.accent,
            scale: changeDirection ? [1, 1.2, 1] : 1,
          }}
          transition={{ duration: 0.3 }}
        >
          {currentLevel}
        </motion.div>

        {/* Can upgrade indicator */}
        {canUpgrade && !isSelected && (
          <motion.div
            className="absolute bottom-0 left-0 right-0 bg-green-500/80 text-white text-xs py-0.5 text-center font-medium"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            ⬆️
          </motion.div>
        )}

        {/* Level change flash */}
        <AnimatePresence>
          {changeDirection && (
            <motion.div
              key={`overlay-${currentLevel}-${changeDirection}`}
              className={`absolute inset-0 rounded-xl flex items-center justify-center ${
                changeDirection === 'up' ? 'bg-yellow-400/30' : 'bg-red-400/20'
              }`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <motion.span
                className="text-2xl"
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.5 }}
              >
                {changeDirection === 'up' ? '⬆️' : '⬇️'}
              </motion.span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Label */}
      {showLabel && (
        <div className="text-center">
          <p className="text-sm font-medium text-gray-200">
            {config.name_zh || config.name_en}
          </p>
          {isMaxLevel && (
            <span className="text-xs text-yellow-400">✨ MAX</span>
          )}
        </div>
      )}
    </div>
  )
}

export default FurnitureItem

