'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { FurnitureItem, type ItemConfig } from './FurnitureItem'

export interface RoomItem {
  blueprint: ItemConfig
  current_level: number
  current_emoji: string
  can_upgrade: boolean
  is_locked?: boolean  // NEW: Item slot is locked (needs progression to unlock)
  unlock_requirement?: string  // NEW: What's needed to unlock
  position?: number  // NEW: Grid position for rearrangement
  upgrade_cost?: {
    energy: number
    essence: number
    blocks: number
  }
}

export interface RoomProps {
  roomCode: 'study' | 'living'
  roomName: string
  roomNameZh: string
  items: RoomItem[]
  selectedItem?: string | null
  onSelectItem?: (itemCode: string) => void
  editMode?: boolean  // NEW: Edit mode for rearranging
  onSwapItems?: (itemA: string, itemB: string) => void  // NEW: Swap two items
}

// Room background styles
const ROOM_STYLES = {
  study: {
    gradient: 'from-amber-900/30 via-orange-900/20 to-yellow-900/30',
    border: 'border-amber-700/30',
    icon: '📚',
  },
  living: {
    gradient: 'from-emerald-900/30 via-teal-900/20 to-cyan-900/30',
    border: 'border-emerald-700/30',
    icon: '🛋️',
  },
}

export function Room({
  roomCode,
  roomName,
  roomNameZh,
  items,
  selectedItem,
  onSelectItem,
  editMode = false,
  onSwapItems,
}: RoomProps) {
  const style = ROOM_STYLES[roomCode] || ROOM_STYLES.study
  const [swapSource, setSwapSource] = React.useState<string | null>(null)

  const handleItemClick = (itemCode: string, isLocked: boolean) => {
    if (isLocked) {
      // Don't allow interaction with locked items
      return
    }

    if (editMode && onSwapItems) {
      // Edit mode: swap items
      if (!swapSource) {
        setSwapSource(itemCode)
      } else if (swapSource !== itemCode) {
        onSwapItems(swapSource, itemCode)
        setSwapSource(null)
      } else {
        setSwapSource(null) // Clicked same item, cancel
      }
    } else {
      // Normal mode: select for upgrade
      onSelectItem?.(itemCode)
    }
  }

  return (
    <motion.div
      className={`bg-gradient-to-br ${style.gradient} rounded-2xl p-6 border ${style.border} ${
        editMode ? 'ring-2 ring-blue-400 ring-offset-2 ring-offset-gray-900' : ''
      }`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Room Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{style.icon}</span>
          <div>
            <h3 className="text-lg font-bold text-white">{roomNameZh}</h3>
            <p className="text-sm text-gray-400">{roomName}</p>
          </div>
        </div>
        {editMode && (
          <div className="text-xs text-blue-400 bg-blue-500/20 px-3 py-1 rounded-full">
            🔄 編輯模式
          </div>
        )}
      </div>

      {/* Items Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {items.map((item) => (
          <div key={item.blueprint.code} className="relative">
            {item.is_locked ? (
              // Locked slot
              <LockedSlot 
                requirement={item.unlock_requirement || '達到更高等級解鎖'}
                icon={item.blueprint.emoji_levels[0] || '🔒'}
              />
            ) : (
              // Unlocked item
              <FurnitureItem
                config={item.blueprint}
                currentLevel={item.current_level}
                size="md"
                isSelected={editMode ? swapSource === item.blueprint.code : selectedItem === item.blueprint.code}
                canUpgrade={!editMode && item.can_upgrade}
                onClick={() => handleItemClick(item.blueprint.code, false)}
                showLabel={true}
              />
            )}
          </div>
        ))}
      </div>

      {/* Empty state */}
      {items.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No items in this room yet</p>
        </div>
      )}

      {/* Edit mode hint */}
      {editMode && swapSource && (
        <motion.div
          className="mt-4 text-center text-sm text-blue-300 bg-blue-500/20 px-4 py-2 rounded-lg"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          點擊另一個物品來交換位置
        </motion.div>
      )}
    </motion.div>
  )
}

// Locked slot component
function LockedSlot({ requirement, icon }: { requirement: string; icon: string }) {
  return (
    <motion.div
      className="relative w-24 h-24 rounded-xl flex flex-col items-center justify-center bg-gray-800/50 border-2 border-gray-700 border-dashed cursor-not-allowed"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Lock icon */}
      <div className="text-4xl opacity-30 mb-1">🔒</div>
      <div className="text-2xl opacity-50">{icon}</div>
      
      {/* Requirement tooltip on hover */}
      <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity bg-gray-900/90 rounded-xl p-2">
        <p className="text-xs text-center text-gray-300">{requirement}</p>
      </div>
    </motion.div>
  )
}

export default Room

