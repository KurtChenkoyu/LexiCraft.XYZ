'use client'

import { motion } from 'framer-motion'

export interface Currencies {
  sparks: number
  essence: number
  energy: number
  blocks: number
  level: number
  level_progress: number
  total_xp?: number
  xp_to_next_level?: number
  xp_in_current_level?: number
}

export interface CurrencyBarProps {
  currencies: Currencies
  compact?: boolean
}

export function CurrencyBar({ currencies, compact = false }: CurrencyBarProps) {
  const items = [
    {
      icon: '✨',
      label: 'Sparks',
      labelZh: '火花',
      value: currencies.sparks,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
      sublabel: `Lv.${currencies.level}`,
      progress: currencies.level_progress,
    },
    {
      icon: '⚡',
      label: 'Energy',
      labelZh: '能量',
      value: currencies.energy,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      icon: '💧',
      label: 'Essence',
      labelZh: '精華',
      value: currencies.essence,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
    },
    {
      icon: '🧱',
      label: 'Blocks',
      labelZh: '磚塊',
      value: currencies.blocks,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
    },
  ]

  if (compact) {
    return (
      <div className="flex items-center gap-3 text-sm">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-1">
            <span>{item.icon}</span>
            <span className={item.color}>{item.value}</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-wrap justify-center gap-3">
      {items.map((item, index) => (
        <motion.div
          key={item.label}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl ${item.bgColor} border border-gray-700/50`}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <span className="text-xl">{item.icon}</span>
          <div className="flex flex-col">
            <div className="flex items-baseline gap-1">
              <span className={`font-bold ${item.color}`}>
                {item.value.toLocaleString()}
              </span>
              {item.sublabel && (
                <span className="text-xs text-gray-400">{item.sublabel}</span>
              )}
            </div>
            <span className="text-xs text-gray-500">{item.labelZh}</span>
          </div>
          
          {/* Level progress bar for Sparks */}
          {item.progress !== undefined && (
            <div className="w-16 h-1 bg-gray-700 rounded-full overflow-hidden ml-2">
              <motion.div
                className="h-full bg-yellow-400 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${item.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          )}
        </motion.div>
      ))}
    </div>
  )
}

export default CurrencyBar

