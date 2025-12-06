'use client'

import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react'
import { vocabulary } from '@/lib/vocabulary'
import { localStore } from '@/lib/local-store'

// G6 types - we'll import dynamically to avoid SSR issues
type G6Graph = any

type LayoutMode = 'force' | 'grid' | 'circular' | 'radial' | 'concentric'

// Cache key for positions
const GRAPH_POSITIONS_KEY = 'graph_node_positions'
const GRAPH_VIEWPORT_KEY = 'graph_viewport'

interface MineGraphG6Props {
  userProgress?: Record<string, 'raw' | 'hollow' | 'solid'>
  onNodeSelect?: (wordPOS: string) => void
  onStartForging?: (wordPOS: string) => void  // New callback for direct forging
  demoMode?: boolean
}

interface GraphNode {
  id: string
  word: string
  pos: string
  status: 'raw' | 'hollow' | 'solid'
  senseCount: number
  xp: number
  connections: number
}

interface GraphEdge {
  source: string
  target: string
  type: string
}

// Demo vocabulary data for when real data is small
const DEMO_WORDS = [
  { word: 'run', pos: 'verb', connections: ['walk', 'sprint', 'jog', 'move', 'rush'] },
  { word: 'walk', pos: 'verb', connections: ['run', 'stroll', 'move', 'step'] },
  { word: 'sprint', pos: 'verb', connections: ['run', 'dash', 'race'] },
  { word: 'jog', pos: 'verb', connections: ['run', 'exercise'] },
  { word: 'move', pos: 'verb', connections: ['run', 'walk', 'shift', 'change'] },
  { word: 'rush', pos: 'verb', connections: ['run', 'hurry', 'dash'] },
  { word: 'stroll', pos: 'verb', connections: ['walk', 'wander'] },
  { word: 'step', pos: 'verb', connections: ['walk', 'climb'] },
  { word: 'dash', pos: 'verb', connections: ['sprint', 'rush'] },
  { word: 'race', pos: 'verb', connections: ['sprint', 'compete'] },
  { word: 'exercise', pos: 'verb', connections: ['jog', 'train', 'work'] },
  { word: 'shift', pos: 'verb', connections: ['move', 'change'] },
  { word: 'change', pos: 'verb', connections: ['move', 'shift', 'transform'] },
  { word: 'hurry', pos: 'verb', connections: ['rush', 'quick'] },
  { word: 'wander', pos: 'verb', connections: ['stroll', 'roam'] },
  { word: 'climb', pos: 'verb', connections: ['step', 'ascend'] },
  { word: 'compete', pos: 'verb', connections: ['race', 'contest'] },
  { word: 'train', pos: 'verb', connections: ['exercise', 'learn'] },
  { word: 'work', pos: 'noun', connections: ['exercise', 'job', 'task'] },
  { word: 'transform', pos: 'verb', connections: ['change', 'convert'] },
  { word: 'quick', pos: 'adj', connections: ['hurry', 'fast', 'rapid'] },
  { word: 'roam', pos: 'verb', connections: ['wander', 'travel'] },
  { word: 'ascend', pos: 'verb', connections: ['climb', 'rise'] },
  { word: 'contest', pos: 'noun', connections: ['compete', 'game'] },
  { word: 'learn', pos: 'verb', connections: ['train', 'study', 'know'] },
  { word: 'job', pos: 'noun', connections: ['work', 'career'] },
  { word: 'task', pos: 'noun', connections: ['work', 'duty'] },
  { word: 'convert', pos: 'verb', connections: ['transform', 'switch'] },
  { word: 'fast', pos: 'adj', connections: ['quick', 'speed'] },
  { word: 'rapid', pos: 'adj', connections: ['quick', 'swift'] },
  { word: 'travel', pos: 'verb', connections: ['roam', 'journey', 'trip'] },
  { word: 'rise', pos: 'verb', connections: ['ascend', 'grow'] },
  { word: 'game', pos: 'noun', connections: ['contest', 'play', 'fun'] },
  { word: 'study', pos: 'verb', connections: ['learn', 'read'] },
  { word: 'know', pos: 'verb', connections: ['learn', 'understand'] },
  { word: 'career', pos: 'noun', connections: ['job', 'profession'] },
  { word: 'duty', pos: 'noun', connections: ['task', 'responsibility'] },
  { word: 'switch', pos: 'verb', connections: ['convert', 'toggle'] },
  { word: 'speed', pos: 'noun', connections: ['fast', 'velocity'] },
  { word: 'swift', pos: 'adj', connections: ['rapid', 'nimble'] },
  { word: 'journey', pos: 'noun', connections: ['travel', 'trip'] },
  { word: 'trip', pos: 'noun', connections: ['travel', 'journey'] },
  { word: 'grow', pos: 'verb', connections: ['rise', 'develop'] },
  { word: 'play', pos: 'verb', connections: ['game', 'fun'] },
  { word: 'fun', pos: 'noun', connections: ['game', 'play', 'joy'] },
  { word: 'read', pos: 'verb', connections: ['study', 'book'] },
  { word: 'understand', pos: 'verb', connections: ['know', 'comprehend'] },
  { word: 'profession', pos: 'noun', connections: ['career', 'skill'] },
  { word: 'responsibility', pos: 'noun', connections: ['duty', 'role'] },
  { word: 'toggle', pos: 'verb', connections: ['switch', 'flip'] },
]

/**
 * Build graph data grouped by word+POS
 */
function buildGraphData(
  demoMode: boolean,
  userProgress: Record<string, 'raw' | 'hollow' | 'solid'>
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  // In demo mode, always use demo data for visualization
  if (demoMode) {
    return buildDemoGraphData()
  }

  const graphData = vocabulary.getGraphData()
  
  // If real data is too small, use demo data
  if (!graphData || graphData.nodes.length < 10) {
    console.log('📊 Using demo graph data (vocabulary too small)')
    return buildDemoGraphData()
  }

  // Group senses by word+POS
  const wordPOSMap = new Map<string, {
    word: string
    pos: string
    senses: string[]
    connections: Set<string>
  }>()

  // Process nodes
  const nodesToProcess = graphData.nodes.slice(0, 100)

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
        connections: new Set()
      })
    }
    wordPOSMap.get(wordPOSKey)!.senses.push(node.id)
  }

  // Build connections
  for (const edge of graphData.edges) {
    const sourceSense = vocabulary.getSense(edge.source)
    const targetSense = vocabulary.getSense(edge.target)
    if (!sourceSense || !targetSense) continue

    const sourceKey = `${sourceSense.word}_${sourceSense.pos || 'other'}`
    const targetKey = `${targetSense.word}_${targetSense.pos || 'other'}`

    if (wordPOSMap.has(sourceKey) && wordPOSMap.has(targetKey) && sourceKey !== targetKey) {
      wordPOSMap.get(sourceKey)!.connections.add(targetKey)
    }
  }

  // Convert to G6 format
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const addedEdges = new Set<string>()

  wordPOSMap.forEach((data, key) => {
    // Determine status from any of its senses
    let status: 'raw' | 'hollow' | 'solid' = 'raw'
    
    // Use actual progress
    for (const senseId of data.senses) {
      const senseStatus = userProgress[senseId]
      if (senseStatus === 'solid') {
        status = 'solid'
        break
      } else if (senseStatus === 'hollow') {
        status = 'hollow'
      }
    }

    // Calculate XP based on connections (base 100 + 10 per connection)
    const connectionCount = data.connections.size
    const xp = 100 + (connectionCount * 10)
    
    nodes.push({
      id: key,
      word: data.word,
      pos: data.pos,
      status,
      senseCount: data.senses.length,
      xp,
      connections: connectionCount,
    })

    // Add edges
    for (const targetKey of Array.from(data.connections)) {
      const edgeKey = [key, targetKey].sort().join('--')
      if (!addedEdges.has(edgeKey)) {
        addedEdges.add(edgeKey)
        edges.push({
          source: key,
          target: targetKey,
          type: 'related',
        })
      }
    }
  })

  return { nodes, edges }
}

/**
 * Build demo graph data for visualization showcase
 */
function buildDemoGraphData(): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const addedEdges = new Set<string>()
  
  // Create nodes from demo words
  DEMO_WORDS.forEach((item, index) => {
    const key = `${item.word}_${item.pos}`
    
    // Simulate progress: 30% solid, 30% hollow, 40% raw
    let status: 'raw' | 'hollow' | 'solid' = 'raw'
    const rand = index % 10
    if (rand < 3) status = 'solid'
    else if (rand < 6) status = 'hollow'
    
    nodes.push({
      id: key,
      word: item.word,
      pos: item.pos,
      status,
      senseCount: 1,
      xp: 100 + item.connections.length * 10,
      connections: item.connections.length,
    })
    
    // Add edges
    for (const target of item.connections) {
      // Find the target word in demo data
      const targetItem = DEMO_WORDS.find(w => w.word === target)
      if (targetItem) {
        const targetKey = `${targetItem.word}_${targetItem.pos}`
        const edgeKey = [key, targetKey].sort().join('--')
        if (!addedEdges.has(edgeKey)) {
          addedEdges.add(edgeKey)
          edges.push({
            source: key,
            target: targetKey,
            type: 'related',
          })
        }
      }
    }
  })
  
  return { nodes, edges }
}

// Color mapping
const statusColors = {
  solid: '#D97706',   // Amber - mastered
  hollow: '#DC2626',  // Red - learning
  raw: '#4B5563',     // Gray - not started
}

// Selected node info for quick preview
interface SelectedNodeInfo {
  id: string
  word: string
  pos: string
  status: 'raw' | 'hollow' | 'solid'
  xp: number
  connections: number
}

export function MineGraphG6({
  userProgress = {},
  onNodeSelect,
  onStartForging,
  demoMode = false,
}: MineGraphG6Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<G6Graph | null>(null)
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('force')
  const [isLoading, setIsLoading] = useState(true)
  const [G6Module, setG6Module] = useState<any>(null)
  const [cachedPositions, setCachedPositions] = useState<Record<string, { x: number; y: number }> | null>(null)
  const positionsSaved = useRef(false)
  const [selectedNode, setSelectedNode] = useState<SelectedNodeInfo | null>(null)

  // Load cached positions on mount
  useEffect(() => {
    const loadCachedPositions = async () => {
      try {
        const positions = await localStore.get(GRAPH_POSITIONS_KEY)
        if (positions && typeof positions === 'object') {
          console.log('📍 Loaded cached positions for', Object.keys(positions).length, 'nodes')
          setCachedPositions(positions as Record<string, { x: number; y: number }>)
        }
      } catch (err) {
        console.warn('Failed to load cached positions:', err)
      }
    }
    loadCachedPositions()
  }, [])

  // Save positions when layout stabilizes
  const savePositions = useCallback(async () => {
    if (!graphRef.current || positionsSaved.current) return
    
    try {
      const nodes = graphRef.current.getNodeData()
      const positions: Record<string, { x: number; y: number }> = {}
      
      nodes.forEach((node: any) => {
        if (node.id && node.x !== undefined && node.y !== undefined) {
          positions[node.id] = { x: node.x, y: node.y }
        }
      })
      
      if (Object.keys(positions).length > 0) {
        await localStore.set(GRAPH_POSITIONS_KEY, positions)
        console.log('💾 Saved positions for', Object.keys(positions).length, 'nodes')
        positionsSaved.current = true
      }
    } catch (err) {
      console.warn('Failed to save positions:', err)
    }
  }, [])

  // Build graph data
  const graphData = useMemo(() => {
    if (!vocabulary.isLoaded) return { nodes: [], edges: [] }
    return buildGraphData(demoMode, userProgress)
  }, [demoMode, userProgress])

  // Dynamically import G6 (client-side only)
  useEffect(() => {
    import('@antv/g6').then((module) => {
      setG6Module(module)
    })
  }, [])

  // Initialize graph
  useEffect(() => {
    if (!G6Module || !containerRef.current || graphData.nodes.length === 0) return

    const { Graph } = G6Module

    // Get container dimensions
    const container = containerRef.current
    const width = container.offsetWidth || 800
    const height = container.offsetHeight || 600

    // Destroy existing graph
    if (graphRef.current) {
      // Save positions before destroying
      savePositions()
      graphRef.current.destroy()
      graphRef.current = null
    }

    // Reset position saved flag for new graph
    positionsSaved.current = false

    // Apply cached positions to nodes if available
    const nodesWithPositions = graphData.nodes.map(node => {
      const cached = cachedPositions?.[node.id]
      return {
        id: node.id,
        data: {
          word: node.word,
          pos: node.pos,
          status: node.status,
          senseCount: node.senseCount,
          xp: node.xp,
          connections: node.connections,
        },
        // Apply cached position if available
        ...(cached ? { x: cached.x, y: cached.y } : {}),
      }
    })

    const hasCachedPositions = cachedPositions && Object.keys(cachedPositions).length > 0
    console.log(hasCachedPositions ? '📍 Using cached positions' : '🔄 Computing new layout')

    // Create graph instance
    const graph = new Graph({
      container: containerRef.current,
      width,
      height,
      autoFit: hasCachedPositions ? 'view' : 'view',
      data: {
        nodes: nodesWithPositions,
        edges: graphData.edges.map((edge, i) => ({
          id: `edge-${i}`,
          source: edge.source,
          target: edge.target,
        })),
      },
      node: {
        type: 'rect',
        style: {
          size: [52, 52], // Square nodes
          radius: 6,
          fill: (d: any) => {
            const status = d.data?.status || 'raw'
            return statusColors[status as keyof typeof statusColors] || statusColors.raw
          },
          stroke: (d: any) => {
            const status = d.data?.status || 'raw'
            if (status === 'solid') return '#B45309'
            if (status === 'hollow') return '#B91C1C'
            return '#374151'
          },
          lineWidth: 2,
          // Label centered in the middle of node
          labelText: (d: any) => d.data?.word || '',
          labelFill: '#fff',
          labelFontSize: 10,
          labelFontWeight: 600,
          labelPlacement: 'center', // Center label inside node
          labelMaxWidth: 46,
          labelWordWrap: true,
          labelMaxLines: 2,
          cursor: 'pointer',
        },
        state: {
          hover: {
            stroke: '#3B82F6',
            lineWidth: 3,
            shadowColor: '#3B82F6',
            shadowBlur: 8,
          },
          selected: {
            stroke: '#10B981',
            lineWidth: 3,
            shadowColor: '#10B981',
            shadowBlur: 12,
          },
        },
      },
      edge: {
        type: 'line',
        style: {
          stroke: '#6B7280',
          lineWidth: 1,
          endArrow: false,
        },
        state: {
          hover: {
            stroke: '#3B82F6',
            lineWidth: 2,
          },
        },
      },
      layout: getLayoutConfig(layoutMode),
      behaviors: [
        'drag-canvas',
        'zoom-canvas',
        'drag-element',
        {
          type: 'hover-activate',
          degree: 1, // Highlight 1-hop neighbors on hover
        },
      ],
      plugins: [
        {
          type: 'tooltip',
          getContent: (e: any, items: any[]) => {
            if (!items || items.length === 0) return ''
            const item = items[0]
            const data = item.data || {}
            const word = data.word || item.id
            const pos = data.pos || ''
            const xp = data.xp || 100
            const connections = data.connections || 0
            const posLabel = pos === 'noun' ? '名詞' : pos === 'verb' ? '動詞' : 
                            pos === 'adj' ? '形容詞' : pos === 'adv' ? '副詞' : pos
            
            return `
              <div style="padding: 10px 14px; background: #0f172a; border: 1px solid #334155; border-radius: 10px; color: white; font-size: 12px; min-width: 140px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <div style="font-size: 18px; font-weight: bold; margin-bottom: 2px;">${word}</div>
                <div style="color: #64748b; font-size: 11px; margin-bottom: 8px;">${posLabel}</div>
                <div style="display: flex; gap: 12px; margin-bottom: 6px;">
                  <div>
                    <div style="color: #fbbf24; font-size: 16px; font-weight: bold;">⭐ ${xp}</div>
                    <div style="color: #64748b; font-size: 9px;">XP</div>
                  </div>
                  <div>
                    <div style="color: #38bdf8; font-size: 16px; font-weight: bold;">🔗 ${connections}</div>
                    <div style="color: #64748b; font-size: 9px;">連結</div>
                  </div>
                </div>
                <div style="color: #475569; font-size: 9px; border-top: 1px solid #334155; padding-top: 6px;">點擊選取</div>
              </div>
            `
          },
        },
        {
          type: 'minimap',
          size: [120, 80],
          position: 'bottom-right',
        },
      ],
      animation: false, // Disable animation to prevent jiggling
    })

    // Handle node click - show quick preview instead of full modal
    graph.on('node:click', (e: any) => {
      const nodeId = e.target.id
      const nodeData = e.target.data || {}
      console.log('🎯 G6 node clicked:', nodeId, nodeData)
      
      // Set selected node for quick preview panel
      setSelectedNode({
        id: nodeId,
        word: nodeData.word || nodeId.split('_')[0],
        pos: nodeData.pos || '',
        status: nodeData.status || 'raw',
        xp: nodeData.xp || 100,
        connections: nodeData.connections || 0,
      })
    })
    
    // Click on canvas to deselect
    graph.on('canvas:click', () => {
      setSelectedNode(null)
    })

    // Save positions after layout completes
    graph.on('afterlayout', () => {
      // Delay to ensure positions are finalized
      setTimeout(() => {
        savePositions()
      }, 500)
    })

    // Render
    graph.render().then(() => {
      setIsLoading(false)
    }).catch((error: any) => {
      console.warn('G6 render error (usually harmless):', error?.message || error)
      setIsLoading(false)
    })

    graphRef.current = graph

    // Cleanup
    return () => {
      if (graphRef.current) {
        savePositions() // Save positions before destroying
        graphRef.current.destroy()
        graphRef.current = null
      }
    }
  }, [G6Module, graphData, onNodeSelect, cachedPositions, savePositions]) // Note: layoutMode not in deps - we update separately

  // Update layout when mode changes
  useEffect(() => {
    if (!graphRef.current || !G6Module) return
    
    const graph = graphRef.current
    // Use non-animated layout for smoother transitions
    const newLayout = {
      ...getLayoutConfig(layoutMode),
      animated: false, // Disable animation to prevent jiggling
    }
    
    try {
      graph.setLayout(newLayout)
      // Wrap layout() in try-catch as it can throw async errors
      Promise.resolve(graph.layout()).catch((e: any) => {
        console.debug('Layout async error (usually harmless):', e?.message || e)
      })
    } catch (e) {
      console.warn('Layout change error:', e)
    }
  }, [layoutMode, G6Module])

  // Handle resize
  useEffect(() => {
    if (!containerRef.current || !graphRef.current) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        if (graphRef.current && width > 0 && height > 0) {
          graphRef.current.setSize(width, height)
        }
      }
    })

    resizeObserver.observe(containerRef.current)
    return () => resizeObserver.disconnect()
  }, [G6Module])

  // Stats
  const nodeCount = graphData.nodes.length
  const edgeCount = graphData.edges.length

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
            { mode: 'force' as LayoutMode, label: '🌊 自由', title: '力導向佈局' },
            { mode: 'grid' as LayoutMode, label: '⊞ 網格', title: '網格佈局' },
            { mode: 'concentric' as LayoutMode, label: '◎ 進度', title: '按進度分層' },
            { mode: 'circular' as LayoutMode, label: '○ 圓形', title: '圓形佈局' },
            { mode: 'radial' as LayoutMode, label: '◎ 等級', title: '等級放射' },
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
        {nodeCount} 節點 · {edgeCount} 連結
      </div>

      {/* Legend - positioned on the left side */}
      <div className="absolute top-16 left-4 z-20 bg-slate-800/95 backdrop-blur-sm rounded-lg p-3 text-xs shadow-lg">
        <div className="font-medium text-slate-200 mb-2">圖例</div>
        <div className="flex flex-col gap-2 text-slate-300">
          <span className="flex items-center gap-2">
            <span className="w-5 h-4 rounded" style={{ backgroundColor: statusColors.solid }}></span>
            已掌握
          </span>
          <span className="flex items-center gap-2">
            <span className="w-5 h-4 rounded" style={{ backgroundColor: statusColors.hollow }}></span>
            學習中
          </span>
          <span className="flex items-center gap-2">
            <span className="w-5 h-4 rounded" style={{ backgroundColor: statusColors.raw }}></span>
            未開始
          </span>
        </div>
        <div className="mt-3 pt-2 border-t border-slate-700 text-slate-500 text-[10px]">
          點擊節點查看詳情<br/>
          滾輪縮放 · 拖曳平移
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-2">
        <button
          onClick={() => graphRef.current?.zoom(1.2)}
          className="w-8 h-8 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center justify-center text-lg"
        >
          +
        </button>
        <button
          onClick={() => graphRef.current?.zoom(0.8)}
          className="w-8 h-8 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center justify-center text-lg"
        >
          −
        </button>
        <button
          onClick={() => graphRef.current?.fitView()}
          className="w-8 h-8 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center justify-center text-sm"
          title="適應視窗"
        >
          ⌖
        </button>
      </div>

      {/* Graph container */}
      <div ref={containerRef} className="w-full h-full" />

      {/* Quick Preview Panel - shows when a node is selected */}
      {selectedNode && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 bg-slate-800/95 backdrop-blur-sm rounded-xl px-4 py-3 shadow-2xl border border-slate-700">
          <div className="flex items-center gap-4">
            {/* Word and POS */}
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white">{selectedNode.word}</span>
              <span className="px-1.5 py-0.5 text-[10px] rounded bg-slate-700 text-slate-400">
                {selectedNode.pos === 'noun' ? '名' : 
                 selectedNode.pos === 'verb' ? '動' : 
                 selectedNode.pos === 'adj' ? '形' : 
                 selectedNode.pos === 'adv' ? '副' : selectedNode.pos}
              </span>
            </div>
            
            {/* XP and Connections */}
            <div className="flex items-center gap-3 text-sm border-l border-slate-700 pl-4">
              <span className="text-amber-400 font-semibold">⭐ {selectedNode.xp}</span>
              <span className="text-cyan-400">🔗 {selectedNode.connections}</span>
            </div>
            
            {/* Action Button or Status */}
            {selectedNode.status === 'raw' ? (
              <button
                onClick={() => {
                  // Update local status immediately (optimistic UI)
                  setSelectedNode(prev => prev ? { ...prev, status: 'hollow' } : null)
                  // Notify parent to start forging
                  if (onStartForging) {
                    onStartForging(selectedNode.id)
                  }
                }}
                className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-medium text-sm transition-colors whitespace-nowrap"
              >
                🔥 鍛造
              </button>
            ) : (
              <span 
                className="px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap"
                style={{ 
                  backgroundColor: statusColors[selectedNode.status] + '33',
                  color: selectedNode.status === 'solid' ? '#fbbf24' : '#f87171',
                  border: `1px solid ${statusColors[selectedNode.status]}`
                }}
              >
                {selectedNode.status === 'solid' ? '✓ 已掌握' : '📖 學習中'}
              </span>
            )}
            
            {/* Details link */}
            <button
              onClick={() => {
                if (onNodeSelect) {
                  onNodeSelect(selectedNode.id)
                }
              }}
              className="text-slate-500 hover:text-cyan-400 text-xs transition-colors"
            >
              詳情 →
            </button>
            
            {/* Close button */}
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-500 hover:text-white ml-1"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
          <div className="text-cyan-500">載入中...</div>
        </div>
      )}
    </div>
  )
}

/**
 * Get layout configuration for G6
 */
function getLayoutConfig(mode: LayoutMode): any {
  const nodeSize = 56 // Square node size
  
  switch (mode) {
    case 'force':
      return {
        type: 'force',
        preventOverlap: true,
        nodeSize,
        linkDistance: 80,
        nodeStrength: -80,
        edgeStrength: 0.5,
        collideStrength: 1,
        alpha: 0.05,          // Very low initial energy
        alphaDecay: 0.08,     // Fast decay
        alphaMin: 0.02,       // Stop early
      }
    case 'grid':
      return {
        type: 'grid',
        // Sort by degree (number of connections) - most connected first
        sortBy: 'degree',
        rows: undefined,
        cols: undefined,
        preventOverlap: true,
        nodeSize,
        condense: true,
      }
    case 'circular':
      return {
        type: 'circular',
        radius: 250,
        divisions: 5,
        ordering: 'degree',
      }
    case 'radial':
      return {
        type: 'radial',
        unitRadius: 80,
        linkDistance: 100,
        preventOverlap: true,
        nodeSize,
      }
    case 'concentric':
      return {
        type: 'concentric',
        minNodeSpacing: 20,
        preventOverlap: true,
        nodeSize,
        // Sort by degree - most connected at center
        sortBy: 'degree',
        clockwise: true,
      }
    default:
      return { type: 'force' }
  }
}

export default MineGraphG6

