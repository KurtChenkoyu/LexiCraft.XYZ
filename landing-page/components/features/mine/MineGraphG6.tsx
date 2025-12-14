/**
 * MineGraphG6 Component
 * 
 * TEMPORARILY DISABLED - Requires refactoring for async vocabulary API
 */

interface MineGraphG6Props {
  userProgress?: Record<string, 'raw' | 'hollow' | 'solid'>
  onNodeSelect?: (nodeId: string) => void
  onStartForging?: (nodeId: string) => void
  demoMode?: boolean
}

export function MineGraphG6({}: MineGraphG6Props) {
  return (
    <div className="flex items-center justify-center h-full bg-slate-900">
      <div className="text-center text-slate-400">
        <p className="text-lg">G6 graph view temporarily unavailable</p>
        <p className="text-sm">Component being refactored for async data</p>
      </div>
    </div>
  )
}
