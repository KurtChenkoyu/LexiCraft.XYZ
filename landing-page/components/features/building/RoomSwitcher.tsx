'use client'

import { motion } from 'framer-motion'

export interface RoomSwitcherProps {
  currentRoom: 'study' | 'living'
  onRoomChange: (room: 'study' | 'living') => void
}

const ROOMS = [
  { code: 'study' as const, icon: '📚', nameZh: '書房', nameEn: 'Study Room' },
  { code: 'living' as const, icon: '🛋️', nameZh: '客廳', nameEn: 'Living Room' },
]

export function RoomSwitcher({ currentRoom, onRoomChange }: RoomSwitcherProps) {
  return (
    <div className="flex gap-2 p-1 bg-gray-800/50 rounded-xl">
      {ROOMS.map((room) => (
        <motion.button
          key={room.code}
          onClick={() => onRoomChange(room.code)}
          className={`relative flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            currentRoom === room.code
              ? 'text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {/* Active background */}
          {currentRoom === room.code && (
            <motion.div
              layoutId="activeRoom"
              className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          
          <span className="relative z-10 text-xl">{room.icon}</span>
          <span className="relative z-10 hidden sm:inline">{room.nameZh}</span>
        </motion.button>
      ))}
    </div>
  )
}

export default RoomSwitcher

