'use client'

import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { vocabulary } from '@/lib/vocabulary'

// Dynamic import to avoid SSR issues with canvas
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-900">
      <div className="text-white">載入圖表中...</div>
    </div>
  ),
})

interface GraphNode {
  id: string
  word: string
  pos: string
  value: number
  tier: number
  definition_en: string
  definition_zh: string
  // Runtime properties
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number | null
  fy?: number | null
}

interface GraphEdge {
  source: string | GraphNode
  target: string | GraphNode
  type: 'related' | 'opposite'
}

type LayoutMode = 'force' | 'grid' | 'radial' | 'cluster'

interface MineGraphProps {
  /** Initial center node (sense_id) */
  centerSenseId?: string
  /** User progress map: sense_id -> status */
  userProgress?: Record<string, 'raw' | 'hollow' | 'solid'>
  /** Callback when a node is selected */
  onNodeSelect?: (senseId: string) => void
  /** Height of the graph container */
  height?: number
  /** Demo mode: show all nodes with simulated progress */
  demoMode?: boolean
}

export function MineGraph({
  centerSenseId,
  userProgress = {},
  onNodeSelect,
  height = 600,
  demoMode = false,
}: MineGraphProps) {
  const graphRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height })
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('force')

  // Generate simulated progress for demo mode
  const simulatedProgress = useMemo(() => {
    if (!demoMode) return userProgress
    
    const allGraphData = vocabulary.getGraphData()
    if (!allGraphData) return userProgress
    
    const simulated: Record<string, 'raw' | 'hollow' | 'solid'> = {}
    
    // Simulate: 30% solid, 40% hollow, 30% raw
    allGraphData.nodes.forEach((node, index) => {
      const rand = Math.random()
      if (rand < 0.30) {
        simulated[node.id] = 'solid'
      } else if (rand < 0.70) {
        simulated[node.id] = 'hollow'
      }
      // Rest are 'raw' (undefined)
    })
    
    return simulated
  }, [demoMode, userProgress])

  // Handle container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: height,
        })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [height])

  // Initialize with center node
  useEffect(() => {
    if (centerSenseId) {
      setExpandedNodes(new Set([centerSenseId]))
    }
  }, [centerSenseId])

  // Build visible graph data from expanded nodes
  const graphData = useMemo(() => {
    const nodes: GraphNode[] = []
    const edges: GraphEdge[] = []
    const seenNodes = new Set<string>()
    const seenEdges = new Set<string>()

    // Get all graph data from vocabulary
    const allGraphData = vocabulary.getGraphData()
    if (!allGraphData) {
      return { nodes: [], links: [] }
    }

    const nodeMap = new Map<string, GraphNode>()
    for (const node of allGraphData.nodes) {
      nodeMap.set(node.id, node as GraphNode)
    }

    // DEMO MODE: Show ALL nodes at once (limited to MAX_NODES for performance)
    if (demoMode) {
      const MAX_DEMO_NODES = 500
      const demoNodes = allGraphData.nodes.slice(0, MAX_DEMO_NODES)
      const demoNodeIds = new Set(demoNodes.map(n => n.id))
      
      for (const node of demoNodes) {
        nodes.push({ ...node } as GraphNode)
      }
      
      for (const edge of allGraphData.edges) {
        if (demoNodeIds.has(edge.source) && demoNodeIds.has(edge.target)) {
          edges.push({
            source: edge.source,
            target: edge.target,
            type: edge.type as 'related' | 'opposite',
          })
        }
      }
      
      return { nodes, links: edges }
    }

    // NORMAL MODE: Only show expanded nodes and their connections
    // If no expanded nodes, show a sample
    const nodesToExpand = expandedNodes.size > 0 
      ? expandedNodes 
      : new Set(allGraphData.nodes.slice(0, 10).map(n => n.id))

    // Add expanded nodes and their connections
    for (const nodeId of nodesToExpand) {
      const node = nodeMap.get(nodeId)
      if (!node || seenNodes.has(nodeId)) continue
      
      seenNodes.add(nodeId)
      nodes.push({ ...node })

      // Find edges for this node
      const nodeEdges = allGraphData.edges.filter(
        e => e.source === nodeId || e.target === nodeId
      )

      for (const edge of nodeEdges) {
        const targetId = edge.source === nodeId ? edge.target : edge.source
        const edgeKey = [nodeId, targetId].sort().join('-')
        
        if (seenEdges.has(edgeKey)) continue
        seenEdges.add(edgeKey)

        // Add the connected node (as unexpanded)
        if (!seenNodes.has(targetId as string)) {
          const targetNode = nodeMap.get(targetId as string)
          if (targetNode) {
            seenNodes.add(targetId as string)
            nodes.push({ ...targetNode })
          }
        }

        edges.push({
          source: edge.source,
          target: edge.target,
          type: edge.type as 'related' | 'opposite',
        })
      }
    }

    // Ensure all edges reference existing nodes
    const nodeIds = new Set(nodes.map(n => n.id))
    const validEdges = edges.filter(
      e => nodeIds.has(e.source as string) && nodeIds.has(e.target as string)
    )

    // Limit to prevent performance issues
    const MAX_NODES = 150
    if (nodes.length > MAX_NODES) {
      const limitedNodes = nodes.slice(0, MAX_NODES)
      const limitedNodeIds = new Set(limitedNodes.map(n => n.id))
      const limitedEdges = validEdges.filter(
        e => limitedNodeIds.has(e.source as string) && limitedNodeIds.has(e.target as string)
      )
      return { nodes: limitedNodes, links: limitedEdges }
    }

    return { nodes, links: validEdges }
  }, [expandedNodes, demoMode])

  // Apply layout when mode changes (after graphData is defined)
  useEffect(() => {
    if (!graphRef.current || graphData.nodes.length === 0) return
    
    const nodes = graphData.nodes
    const width = dimensions.width
    const height = dimensions.height
    const centerX = 0
    const centerY = 0
    
    // First, pause simulation for non-force layouts
    if (layoutMode !== 'force') {
      graphRef.current.pauseAnimation()
    }
    
    if (layoutMode === 'grid') {
      // Grid layout - organize in rows/columns
      const cols = Math.ceil(Math.sqrt(nodes.length))
      const spacing = 18 // Tighter spacing for blocks
      
      nodes.forEach((node, i) => {
        const col = i % cols
        const row = Math.floor(i / cols)
        const x = centerX + (col - cols / 2) * spacing
        const y = centerY + (row - nodes.length / cols / 2) * spacing
        node.x = x
        node.y = y
        node.fx = x
        node.fy = y
      })
      
      // After a tick, zoom to fit
      setTimeout(() => graphRef.current?.zoomToFit(400, 50), 100)
      
    } else if (layoutMode === 'radial') {
      // Radial layout - organize by status in concentric circles
      const statusGroups: Record<string, GraphNode[]> = { solid: [], hollow: [], raw: [] }
      
      nodes.forEach(node => {
        const status = simulatedProgress[node.id] || 'raw'
        statusGroups[status].push(node)
      })
      
      // Inner ring: solid (mastered) at center
      // Middle ring: hollow (learning)
      // Outer ring: raw (undiscovered)
      const rings = [
        { key: 'solid', nodes: statusGroups.solid, radius: 60 },
        { key: 'hollow', nodes: statusGroups.hollow, radius: 150 },
        { key: 'raw', nodes: statusGroups.raw, radius: 280 },
      ]
      
      rings.forEach(ring => {
        if (ring.nodes.length === 0) return
        const angleStep = (2 * Math.PI) / ring.nodes.length
        ring.nodes.forEach((node, i) => {
          const angle = i * angleStep - Math.PI / 2
          const x = centerX + Math.cos(angle) * ring.radius
          const y = centerY + Math.sin(angle) * ring.radius
          node.x = x
          node.y = y
          node.fx = x
          node.fy = y
        })
      })
      
      setTimeout(() => graphRef.current?.zoomToFit(400, 50), 100)
      
    } else if (layoutMode === 'cluster') {
      // Cluster by tier - vertical columns
      const tierGroups: Record<number, GraphNode[]> = {}
      
      nodes.forEach(node => {
        const tier = node.tier || 1
        if (!tierGroups[tier]) tierGroups[tier] = []
        tierGroups[tier].push(node)
      })
      
      const tiers = Object.keys(tierGroups).sort((a, b) => Number(a) - Number(b))
      const tierSpacing = 120 // Horizontal spacing between tiers
      
      tiers.forEach((tier, tierIndex) => {
        const groupNodes = tierGroups[Number(tier)]
        const tierX = centerX + (tierIndex - tiers.length / 2) * tierSpacing
        const nodeSpacing = 16 // Vertical spacing
        
        groupNodes.forEach((node, i) => {
          const x = tierX + (Math.random() - 0.5) * 30 // Slight horizontal jitter
          const y = centerY + (i - groupNodes.length / 2) * nodeSpacing
          node.x = x
          node.y = y
          node.fx = x
          node.fy = y
        })
      })
      
      setTimeout(() => graphRef.current?.zoomToFit(400, 50), 100)
      
    } else {
      // Force layout - release fixed positions and resume
      nodes.forEach(node => {
        node.fx = undefined
        node.fy = undefined
      })
      graphRef.current.resumeAnimation()
      graphRef.current.d3ReheatSimulation()
      setTimeout(() => graphRef.current?.zoomToFit(400, 50), 500)
    }
  }, [layoutMode, graphData.nodes, dimensions, simulatedProgress])

  // Handle node click
  const handleNodeClick = useCallback((node: GraphNode) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      if (next.has(node.id)) {
        // Don't collapse if it's the only expanded node
        if (next.size > 1) {
          next.delete(node.id)
        }
      } else {
        next.add(node.id)
      }
      return next
    })
  }, [])

  // Handle node double-click (open detail)
  const handleNodeDoubleClick = useCallback((node: GraphNode) => {
    onNodeSelect?.(node.id)
  }, [onNodeSelect])

  // Get node color based on status
  const getNodeColor = useCallback((node: GraphNode) => {
    const status = simulatedProgress[node.id] || 'raw'
    const isExpanded = expandedNodes.has(node.id)
    
    if (isExpanded) {
      // Expanded nodes are brighter
      switch (status) {
        case 'solid': return '#FFD700'  // Gold
        case 'hollow': return '#F97316' // Orange
        default: return '#60A5FA'       // Blue (center/expanded)
      }
    } else {
      // Unexpanded nodes are dimmer
      switch (status) {
        case 'solid': return '#B8860B'  // Dark gold
        case 'hollow': return '#C2410C' // Dark orange
        default: return '#6B7280'       // Gray
      }
    }
  }, [simulatedProgress, expandedNodes])

  // Get node size based on value
  const getNodeSize = useCallback((node: GraphNode) => {
    const baseSize = 4
    const valueBonus = Math.sqrt(node.value || 100) / 10
    const isExpanded = expandedNodes.has(node.id)
    return isExpanded ? baseSize + valueBonus + 2 : baseSize + valueBonus
  }, [expandedNodes])

  // Get link color based on type
  const getLinkColor = useCallback((link: GraphEdge) => {
    return link.type === 'opposite' 
      ? 'rgba(239, 68, 68, 0.4)'   // Red for opposites
      : 'rgba(255, 255, 255, 0.2)' // White for related
  }, [])

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    graphRef.current?.zoom(1.5, 400)
  }, [])

  const handleZoomOut = useCallback(() => {
    graphRef.current?.zoom(0.67, 400)
  }, [])

  const handleCenter = useCallback(() => {
    graphRef.current?.centerAt(0, 0, 400)
    graphRef.current?.zoom(1, 400)
  }, [])

  return (
    <div ref={containerRef} className="relative w-full bg-slate-900 rounded-xl overflow-hidden">
      {/* Graph */}
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        
        // Custom node rendering - rounded rectangles (blocks)
        nodeCanvasObject={(node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const status = simulatedProgress[node.id] || 'raw'
          const isExpanded = expandedNodes.has(node.id)
          
          // Block dimensions
          const blockWidth = 12
          const blockHeight = 8
          const radius = 2 // Corner radius
          
          // Colors based on status
          let fillColor: string
          let strokeColor: string
          if (isExpanded) {
            fillColor = status === 'solid' ? '#FFD700' : status === 'hollow' ? '#F97316' : '#60A5FA'
            strokeColor = status === 'solid' ? '#B8860B' : status === 'hollow' ? '#C2410C' : '#3B82F6'
          } else {
            fillColor = status === 'solid' ? '#B8860B' : status === 'hollow' ? '#C2410C' : '#4B5563'
            strokeColor = status === 'solid' ? '#8B6914' : status === 'hollow' ? '#9A3412' : '#374151'
          }
          
          // Draw rounded rectangle
          const x = (node.x || 0) - blockWidth / 2
          const y = (node.y || 0) - blockHeight / 2
          
          ctx.beginPath()
          ctx.moveTo(x + radius, y)
          ctx.lineTo(x + blockWidth - radius, y)
          ctx.quadraticCurveTo(x + blockWidth, y, x + blockWidth, y + radius)
          ctx.lineTo(x + blockWidth, y + blockHeight - radius)
          ctx.quadraticCurveTo(x + blockWidth, y + blockHeight, x + blockWidth - radius, y + blockHeight)
          ctx.lineTo(x + radius, y + blockHeight)
          ctx.quadraticCurveTo(x, y + blockHeight, x, y + blockHeight - radius)
          ctx.lineTo(x, y + radius)
          ctx.quadraticCurveTo(x, y, x + radius, y)
          ctx.closePath()
          
          ctx.fillStyle = fillColor
          ctx.fill()
          ctx.strokeStyle = strokeColor
          ctx.lineWidth = 1
          ctx.stroke()
          
          // Draw word label when zoomed in enough
          if (globalScale > 1.5) {
            ctx.font = `${Math.max(3, 4 / globalScale)}px Inter, sans-serif`
            ctx.textAlign = 'center'
            ctx.textBaseline = 'middle'
            ctx.fillStyle = '#FFFFFF'
            ctx.fillText(node.word, node.x || 0, (node.y || 0) + blockHeight / 2 + 6)
          }
        }}
        nodePointerAreaPaint={(node: GraphNode, color: string, ctx: CanvasRenderingContext2D) => {
          const blockWidth = 12
          const blockHeight = 8
          ctx.fillStyle = color
          ctx.fillRect(
            (node.x || 0) - blockWidth / 2,
            (node.y || 0) - blockHeight / 2,
            blockWidth,
            blockHeight
          )
        }}
        
        // Custom link rendering - 90° connections with rounded corners
        linkCanvasObject={(link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const source = link.source
          const target = link.target
          if (!source.x || !target.x) return
          
          const isOpposite = link.type === 'opposite'
          ctx.strokeStyle = isOpposite ? 'rgba(239, 68, 68, 0.5)' : 'rgba(100, 149, 237, 0.4)'
          ctx.lineWidth = isOpposite ? 1.5 : 1
          
          // Calculate midpoint for 90° bend
          const midX = source.x
          const midY = target.y
          
          ctx.beginPath()
          ctx.moveTo(source.x, source.y)
          
          // Draw with rounded corner at bend
          const cornerRadius = Math.min(10, Math.abs(target.x - source.x) / 4, Math.abs(target.y - source.y) / 4)
          
          if (cornerRadius > 2) {
            // Horizontal to corner
            ctx.lineTo(source.x, midY > source.y ? midY - cornerRadius : midY + cornerRadius)
            // Rounded corner
            ctx.quadraticCurveTo(source.x, midY, source.x + (target.x > source.x ? cornerRadius : -cornerRadius), midY)
            // To target
            ctx.lineTo(target.x, midY)
            ctx.lineTo(target.x, target.y)
          } else {
            // Straight line for short distances
            ctx.lineTo(target.x, target.y)
          }
          
          ctx.stroke()
        }}
        
        // Interactions
        onNodeClick={handleNodeClick}
        onNodeRightClick={handleNodeDoubleClick}
        onNodeHover={(node: GraphNode | null) => setHoveredNode(node)}
        
        // Physics - tighter clustering
        cooldownTicks={200}
        d3AlphaDecay={0.01}
        d3VelocityDecay={0.4}
        d3Force={(forceName: string, force: any) => {
          if (forceName === 'charge') {
            // Reduce repulsion for tighter clustering
            force.strength(-30).distanceMax(150)
          }
          if (forceName === 'link') {
            // Shorter links
            force.distance(40)
          }
          if (forceName === 'center') {
            // Stronger centering
            force.strength(0.1)
          }
        }}
        
        // Zoom/Pan
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.3}
        maxZoom={6}
        
        // Background
        backgroundColor="transparent"
      />

      {/* Hover tooltip */}
      {hoveredNode && (
        <div className="absolute top-4 left-4 bg-slate-800/90 backdrop-blur-sm rounded-lg p-4 max-w-xs pointer-events-none border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl font-bold text-white">{hoveredNode.word}</span>
            {hoveredNode.pos && (
              <span className="text-sm text-slate-400">({hoveredNode.pos})</span>
            )}
          </div>
          {hoveredNode.definition_zh && (
            <p className="text-sm text-slate-300 mb-1">{hoveredNode.definition_zh}</p>
          )}
          {hoveredNode.definition_en && (
            <p className="text-xs text-slate-400">{hoveredNode.definition_en}</p>
          )}
          <div className="mt-2 pt-2 border-t border-slate-700 text-xs text-slate-500">
            點擊展開 · 右鍵查看詳情
          </div>
        </div>
      )}

      {/* Zoom controls */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-2">
        <button
          onClick={handleZoomIn}
          className="w-10 h-10 bg-slate-800/90 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center transition-colors"
          title="放大"
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          className="w-10 h-10 bg-slate-800/90 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center transition-colors"
          title="縮小"
        >
          −
        </button>
        <button
          onClick={handleCenter}
          className="w-10 h-10 bg-slate-800/90 hover:bg-slate-700 text-white rounded-lg flex items-center justify-center transition-colors"
          title="置中"
        >
          ⌖
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-slate-800/90 backdrop-blur-sm rounded-lg p-3 text-xs">
        <div className="flex flex-wrap gap-3 text-slate-300">
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm bg-yellow-500"></span>
            已掌握
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm bg-orange-500"></span>
            學習中
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm bg-blue-400"></span>
            探索中
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm bg-gray-500"></span>
            未開始
          </span>
        </div>
      </div>

      {/* Layout controls */}
      <div className="absolute top-4 left-4 bg-slate-800/90 backdrop-blur-sm rounded-lg p-2 text-xs">
        <div className="flex gap-1">
          <button
            onClick={() => setLayoutMode('force')}
            className={`px-2 py-1 rounded transition-colors ${
              layoutMode === 'force' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
            title="自由排列"
          >
            🌊 自由
          </button>
          <button
            onClick={() => setLayoutMode('grid')}
            className={`px-2 py-1 rounded transition-colors ${
              layoutMode === 'grid' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
            title="網格排列"
          >
            ⊞ 網格
          </button>
          <button
            onClick={() => setLayoutMode('radial')}
            className={`px-2 py-1 rounded transition-colors ${
              layoutMode === 'radial' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
            title="按進度分層"
          >
            ◎ 進度
          </button>
          <button
            onClick={() => setLayoutMode('cluster')}
            className={`px-2 py-1 rounded transition-colors ${
              layoutMode === 'cluster' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
            title="按等級分群"
          >
            ⬡ 等級
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-slate-800/90 backdrop-blur-sm rounded-lg px-3 py-2 text-xs text-slate-400">
        {graphData.nodes.length} 節點 · {graphData.links.length} 連結
      </div>
    </div>
  )
}

