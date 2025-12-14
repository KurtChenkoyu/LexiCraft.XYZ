/**
 * MineGraph Component
 * 
 * TEMPORARILY DISABLED - Requires refactoring for async vocabulary API
 * 
 * This component uses vocabulary.getGraphData() which is not available
 * in the new IndexedDB-backed vocabulary store.
 * 
 * TODO: Refactor to load graph data asynchronously from IndexedDB
 */

export function MineGraph() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center text-slate-400">
        <p className="text-lg">Graph view temporarily unavailable</p>
        <p className="text-sm">Component being refactored for async data</p>
      </div>
    </div>
  )
}
