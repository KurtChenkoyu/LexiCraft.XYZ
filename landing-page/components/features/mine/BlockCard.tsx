'use client'

import { Block } from '@/types/mine'
import { Card } from '@/components/ui'

interface BlockCardProps {
  block: Block
  onClick: () => void
}

export function BlockCard({ block, onClick }: BlockCardProps) {
  const getStatusColor = () => {
    switch (block.status) {
      case 'solid':
        return 'bg-green-100 border-green-300 text-green-800'
      case 'hollow':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800'
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800'
    }
  }

  const getStatusLabel = () => {
    switch (block.status) {
      case 'solid':
        return '🟨 實心'
      case 'hollow':
        return '🧱 鍛造中'
      default:
        return '🪨 原始'
    }
  }

  const getTierBadge = () => {
    const stars = '⭐'.repeat(Math.min(block.tier, 4))
    return stars
  }

  return (
    <Card
      className={`cursor-pointer hover:shadow-lg transition-shadow ${getStatusColor()}`}
      onClick={onClick}
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-1">
              {block.word}
            </h3>
            <div className="text-sm text-gray-600 mb-2">
              {block.definition_preview}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs font-semibold mb-1">{getTierBadge()}</div>
            <div className="text-xs text-gray-500">{getStatusLabel()}</div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
          <div className="text-sm">
            <span className="font-semibold text-cyan-600">
              {block.total_value} XP
            </span>
            {block.connection_count > 0 && (
              <span className="text-gray-500 ml-2">
                ({block.connection_count} 連接)
              </span>
            )}
          </div>
          {block.source && (
            <div className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
              {block.source === 'gap' && '知識缺口'}
              {block.source === 'prerequisite' && '前置字塊'}
              {block.source === 'related_to' && '相關字塊'}
              {block.source === 'opposite_to' && '相反字塊'}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

