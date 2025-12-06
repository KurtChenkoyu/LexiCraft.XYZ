'use client'

import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react'
// @ts-ignore - No types available for react-cytoscapejs
import CytoscapeComponent from 'react-cytoscapejs'
import type { Core, ElementDefinition, LayoutOptions } from 'cytoscape'

// cytoscape Stylesheet type
type Stylesheet = any
import { vocabulary } from '@/lib/vocabulary'

type LayoutMode = 'grid' | 'circle' | 'concentric' | 'cose' | 'breadthfirst'

interface MineGraphCytoscapeProps {
  userProgress?: Record<string, 'raw' | 'hollow' | 'solid'>
  onNodeSelect?: (wordPOS: string) => void
  demoMode?: boolean
}

interface WordPOSNode {
  id: string        // e.g., "drop_verb"
  word: string      // e.g., "drop"
  pos: string       // e.g., "verb"
  senseCount: number
  status: 'raw' | 'hollow' | 'solid'
  tier: number
}

/**
 * Build graph data grouped by word+POS
 */
function buildWordPOSGraph(
  demoMode: boolean,
  userProgress: Record<string, 'raw' | 'hollow' | 'solid'>
): { nodes: ElementDefinition[]; edges: ElementDefinition[] } {
  const graphData = vocabulary.getGraphData()
  if (!graphData) return { nodes: [], edges: [] }

  // Group senses by word+POS
  const wordPOSMap = new Map<string, {
    word: string
    pos: string
    senses: string[]
    tier: number
    connections: Set<string> // Other word+POS nodes this connects to
  }>()

  // First pass: group senses by word+POS
  const nodesToProcess = demoMode 
    ? graphData.nodes.slice(0, 500) 
    : graphData.nodes.slice(0, 50)

  for (const node of nodesToProcess) {
    const sense = vocabulary.getSense(node.id)
    if (!sense) continue

    const pos = sense.pos || 'other'
    const wordPOSKey = `${sense.word}_${pos}`

    if (!wordPOSMap.has(wordPOSKey)) {
      wordPOSMap.set(wordPOSKey, {
        word: sense.word,
        pos,
        senses: [],
        tier: sense.tier || 1,
        connections: new Set()
      })
    }
    wordPOSMap.get(wordPOSKey)!.senses.push(node.id)
  }

  // Second pass: build connections between word+POS nodes
  for (const edge of graphData.edges) {
    const sourceSense = vocabulary.getSense(edge.source)
    const targetSense = vocabulary.getSense(edge.target)
    if (!sourceSense || !targetSense) continue

    const sourceKey = `${sourceSense.word}_${sourceSense.pos || 'other'}`
    const targetKey = `${targetSense.word}_${targetSense.pos || 'other'}`

    // Only connect if both nodes exist in our map
    if (wordPOSMap.has(sourceKey) && wordPOSMap.has(targetKey) && sourceKey !== targetKey) {
      wordPOSMap.get(sourceKey)!.connections.add(targetKey)
    }
  }

  // Build Cytoscape elements
  const nodes: ElementDefinition[] = []
  const edges: ElementDefinition[] = []
  const seenEdges = new Set<string>()

  for (const [id, data] of Array.from(wordPOSMap.entries())) {
    // Determine status from user progress (any sense solid = solid, any hollow = hollow)
    let status: 'raw' | 'hollow' | 'solid' = 'raw'
    if (demoMode) {
      // Simulate progress for demo
      const rand = Math.random()
      status = rand < 0.25 ? 'solid' : rand < 0.6 ? 'hollow' : 'raw'
    } else {
      for (const senseId of data.senses) {
        const senseStatus = userProgress[senseId]
        if (senseStatus === 'solid') {
          status = 'solid'
          break
        } else if (senseStatus === 'hollow' && status === 'raw') {
          status = 'hollow'
        }
      }
    }

    nodes.push({
      data: {
        id,
        label: `${data.word}\n(${data.pos})`,
        word: data.word,
        pos: data.pos,
        senseCount: data.senses.length,
        status,
        tier: data.tier,
      }
    })

    // Add edges
    for (const targetId of Array.from(data.connections)) {
      const edgeKey = [id, targetId].sort().join('--')
      if (!seenEdges.has(edgeKey)) {
        seenEdges.add(edgeKey)
        edges.push({
          data: {
            id: edgeKey,
            source: id,
            target: targetId,
          }
        })
      }
    }
  }

  return { nodes, edges }
}

// Cytoscape stylesheet
const cytoscapeStylesheet: Stylesheet[] = [
  {
    selector: 'node',
    style: {
      'background-color': '#4B5563',
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'color': '#fff',
      'font-size': '10px',
      'text-wrap': 'wrap',
      'text-max-width': '80px',
      'width': '70px',
      'height': '40px',
      'shape': 'round-rectangle',
      'border-width': 2,
      'border-color': '#374151',
    }
  },
  {
    selector: 'node[status = "solid"]',
    style: {
      'background-color': '#D97706',
      'border-color': '#B45309',
    }
  },
  {
    selector: 'node[status = "hollow"]',
    style: {
      'background-color': '#DC2626',
      'border-color': '#B91C1C',
    }
  },
  {
    selector: 'node[status = "raw"]',
    style: {
      'background-color': '#4B5563',
      'border-color': '#374151',
    }
  },
  {
    selector: 'node:selected',
    style: {
      'background-color': '#3B82F6',
      'border-color': '#2563EB',
      'border-width': 3,
    }
  },
  {
    selector: 'edge',
    style: {
      'width': 1,
      'line-color': '#6B7280',
      'curve-style': 'taxi',
      'taxi-direction': 'auto',
      'taxi-turn': '50%',
      'taxi-turn-min-distance': 10,
    }
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#3B82F6',
      'width': 2,
    }
  }
]

export function MineGraphCytoscape({
  userProgress = {},
  onNodeSelect,
  demoMode = false,
}: MineGraphCytoscapeProps) {
  const cyRef = useRef<Core | null>(null)
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('cose')
  const [isLoading, setIsLoading] = useState(true)
  const layoutInitialized = useRef(false)
  const prevLayoutMode = useRef<LayoutMode>(layoutMode)
  const isMounted = useRef(true)
  const layoutRef = useRef<any>(null)

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
      // Stop any running layout
      if (layoutRef.current) {
        try {
          layoutRef.current.stop()
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    }
  }, [])

  // Build graph elements
  const elements = useMemo(() => {
    if (!vocabulary.isLoaded) return []
    const { nodes, edges } = buildWordPOSGraph(demoMode, userProgress)
    return [...nodes, ...edges]
  }, [demoMode, userProgress])

  // Layout configurations
  const getLayoutConfig = useCallback((mode: LayoutMode): LayoutOptions => {
    const baseConfig = {
      name: mode,
      animate: false, // Disable animation to prevent timing issues
      fit: true,
      padding: 50,
    }

    switch (mode) {
      case 'grid':
        return {
          ...baseConfig,
          name: 'grid',
          rows: Math.ceil(Math.sqrt(elements.filter(e => !e.data.source).length)),
          spacingFactor: 1.2,
        }
      case 'circle':
        return {
          ...baseConfig,
          name: 'circle',
          spacingFactor: 1.5,
        }
      case 'concentric':
        return {
          ...baseConfig,
          name: 'concentric',
          concentric: (node: any) => {
            const status = node.data('status')
            return status === 'solid' ? 3 : status === 'hollow' ? 2 : 1
          },
          levelWidth: () => 2,
          minNodeSpacing: 30,
        }
      case 'breadthfirst':
        return {
          ...baseConfig,
          name: 'breadthfirst',
          directed: false,
          spacingFactor: 1.5,
        }
      case 'cose':
      default:
        return {
          ...baseConfig,
          name: 'cose',
          nodeRepulsion: () => 8000,
          idealEdgeLength: () => 100,
          edgeElasticity: () => 100,
          numIter: 100,
          randomize: false,
        }
    }
  }, [elements])

  // Apply layout ONLY when layout mode explicitly changes (not on every re-render)
  useEffect(() => {
    if (cyRef.current && elements.length > 0 && layoutInitialized.current) {
      // Only run layout if layout mode actually changed
      if (prevLayoutMode.current !== layoutMode) {
        prevLayoutMode.current = layoutMode
        try {
          // Stop previous layout if running
          if (layoutRef.current) {
            layoutRef.current.stop()
          }
          if (isMounted.current) {
            layoutRef.current = cyRef.current.layout(getLayoutConfig(layoutMode))
            layoutRef.current.run()
          }
        } catch (e) {
          console.warn('Layout error:', e)
        }
      }
    }
  }, [layoutMode, getLayoutConfig, elements.length])

  // Stable reference for onNodeSelect to avoid re-registering events
  const onNodeSelectRef = useRef(onNodeSelect)
  useEffect(() => {
    onNodeSelectRef.current = onNodeSelect
  }, [onNodeSelect])

  // Handle Cytoscape initialization - runs once
  const handleCy = useCallback((cy: Core) => {
    // Don't re-initialize if already done
    if (cyRef.current === cy) return
    
    cyRef.current = cy
    setIsLoading(false)

    // Register click handler once
    try {
      cy.off('tap', 'node') // Remove any existing handler
      cy.on('tap', 'node', (evt) => {
        const node = evt.target
        const wordPOS = node.data('id')
        const word = node.data('word')
        console.log('🎯 Cytoscape node tapped:', wordPOS, word)
        
        // Use ref to get current handler (avoids stale closure)
        if (onNodeSelectRef.current) {
          onNodeSelectRef.current(wordPOS)
        } else {
          console.warn('No onNodeSelect handler provided')
          alert(`Clicked: ${word} (${node.data('pos')})`)
        }
      })
    } catch (e) {
      console.warn('Error registering click handler:', e)
    }

    // Initial layout - only run once
    if (!layoutInitialized.current && isMounted.current) {
      layoutInitialized.current = true
      setTimeout(() => {
        if (!isMounted.current || !cyRef.current) return
        try {
          layoutRef.current = cy.layout(getLayoutConfig(layoutMode))
          layoutRef.current.run()
        } catch (e) {
          console.warn('Initial layout error:', e)
        }
      }, 100)
    }
  }, [getLayoutConfig, layoutMode]) // Reduced dependencies

  // Stats
  const nodeCount = elements.filter(e => !e.data.source).length
  const edgeCount = elements.filter(e => e.data.source).length

  if (!vocabulary.isLoaded) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-slate-900 rounded-xl">
        <p className="text-gray-400">詞彙資料尚未載入</p>
      </div>
    )
  }

  return (
    <div className="relative w-full h-[calc(100vh-280px)] min-h-[500px] bg-slate-900 rounded-xl overflow-hidden">
      {/* Layout controls */}
      <div className="absolute top-4 left-4 z-10 bg-slate-800/95 backdrop-blur-sm rounded-lg p-2">
        <div className="flex gap-1 text-xs">
          {[
            { mode: 'cose' as LayoutMode, label: '🌊 自由', title: '力導向佈局' },
            { mode: 'grid' as LayoutMode, label: '⊞ 網格', title: '網格佈局' },
            { mode: 'concentric' as LayoutMode, label: '◎ 同心', title: '按進度分層' },
            { mode: 'circle' as LayoutMode, label: '○ 圓形', title: '圓形佈局' },
            { mode: 'breadthfirst' as LayoutMode, label: '⬡ 樹狀', title: '樹狀佈局' },
          ].map(({ mode, label, title }) => (
            <button
              key={mode}
              onClick={() => setLayoutMode(mode)}
              className={`px-3 py-1.5 rounded transition-colors ${
                layoutMode === mode
                  ? 'bg-cyan-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
              title={title}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 z-10 bg-slate-800/95 backdrop-blur-sm rounded-lg px-3 py-2 text-sm text-slate-300">
        {nodeCount} 詞彙 · {edgeCount} 連結
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-800/95 backdrop-blur-sm rounded-lg p-3 text-xs">
        <div className="flex flex-wrap gap-3 text-slate-300">
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-3 rounded bg-amber-600"></span>
            已掌握
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-3 rounded bg-red-600"></span>
            學習中
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-3 rounded bg-gray-600"></span>
            未開始
          </span>
        </div>
        <div className="mt-2 text-slate-500 text-[10px]">
          點擊節點查看詳情 · 滾輪縮放 · 拖曳平移
        </div>
      </div>

      {/* Graph */}
      <CytoscapeComponent
        elements={elements}
        stylesheet={cytoscapeStylesheet}
        style={{ width: '100%', height: '100%' }}
        cy={handleCy}
        boxSelectionEnabled={false}
        autounselectify={false}
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
          <div className="text-cyan-500">載入中...</div>
        </div>
      )}
    </div>
  )
}

