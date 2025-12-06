# Data Pipeline V2 Handoff Document

**Handoff Date**: 2025-12-06  
**From**: Architecture & Frontend Chat  
**To**: Data Pipeline Implementation Chat  
**Status**: Ready for implementation

---

## Executive Summary

We need to rebuild the vocabulary data pipeline to produce a **12,000 word dictionary** with:
- Learner-appropriate definitions (B1/B2 level)
- Validated Chinese translations
- Taiwan-context examples
- CEFR difficulty levels
- Proper sense selection (not academic/obscure)

**Output**: A new `vocabulary.json` file (~40MB uncompressed, ~8MB gzip)

**Timeline**: ~3 weeks

**The frontend will continue working with the current data** - when you're done, we simply swap the file.

---

## Background: Why This Rebuild?

### Problems Discovered in Current Pipeline

| Issue | Example | Root Cause |
|-------|---------|------------|
| British spellings | "colour" instead of "color" | Source data + WordNet |
| Academic senses | "quark color property" | WordNet is academic |
| Over-granular | 3 nearly identical noun senses | Top 3 selection blind |
| Missing verbs | "drop" has no verb sense | POS-unaware selection |
| Bad examples | Example doesn't match sense | AI hallucination |

### Current State

- **3,500 words**, ~7,600 senses
- **7 MB** vocabulary.json
- Quality issues throughout
- Located: `landing-page/data/vocabulary.json`

### Target State

- **12,000 words**, ~24,000 senses (2 per word avg)
- **~40 MB** vocabulary.json
- Validated quality
- Same location (drop-in replacement)

---

## Critical Decision: Neo4j → Build Tool Only

### The Question
We currently use Neo4j Aura for:
1. Storing vocabulary data
2. Relationship queries (synonyms, antonyms)
3. Hop traversal ("words 2 hops from X")
4. Graph visualization (admin/debug)

**But if we're dumping everything to JSON... do we still need Neo4j at runtime?**

### Answer: NO. Neo4j becomes BUILD-TIME only.

```
BEFORE (Current)                    AFTER (New)
─────────────────                   ────────────
                                    
Frontend → API → Neo4j              Frontend → vocabulary.json
    (slow, connection overhead)         (instant, cached)
                                    
Neo4j stores everything             JSON stores everything
Neo4j queries relationships         JSON has pre-computed relationships
Neo4j for hops                      JSON has pre-computed hops
                                    
Runtime dependency                  Build-time only
```

### What This Means

1. **Keep Neo4j for data pipeline** (local or temp Aura instance)
   - Mine relationships from WordNet
   - Compute hops during enrichment
   - Build the graph, then export

2. **Export EVERYTHING to JSON**
   - All senses with enriched content
   - All relationships (1-hop directly connected)
   - Pre-computed 2-hop connections if needed
   - Band indexes for fast filtering

3. **Remove Neo4j from production**
   - No more Aura hosting
   - No connection overhead
   - No runtime dependency
   - Frontend/backend just read JSON

### Pre-Computing Relationships

```python
def export_with_hops():
    """Export relationships with pre-computed hops"""
    
    relationships = {}
    
    for sense_id in all_senses:
        # 1-hop: Direct connections
        direct = get_direct_connections(sense_id)  # From Neo4j
        
        # 2-hop: Friends of friends (optional)
        two_hop = set()
        for neighbor in direct['related']:
            neighbor_connections = get_direct_connections(neighbor)
            two_hop.update(neighbor_connections['related'])
        two_hop.discard(sense_id)  # Remove self
        
        relationships[sense_id] = {
            "related": direct['related'],
            "opposite": direct['opposite'],
            "two_hop_related": list(two_hop)[:20]  # Limit for size
        }
    
    return relationships
```

### Do We Need 2-Hop at Runtime?

For the vocabulary app, probably not:
- Show direct connections in block detail ✅
- "Related words" section shows 1-hop ✅
- Exploration paths can be computed client-side ✅

**If needed later**: We have the data, can add 2-hop to JSON.

### What About the Current Neo4j Data?

**Option A: Start Fresh (RECOMMENDED)**
- Current data has quality issues
- New pipeline will create clean data
- No migration needed

**Option B: Migrate**
- Export current Neo4j → JSON
- Enrich in place
- More complex, keeps old issues

**Recommendation**: Start fresh. Delete old Aura data after new export is validated.

### Infrastructure Simplification

| Before | After |
|--------|-------|
| Neo4j Aura (free tier limits) | No cloud database |
| Connection per request | Zero connections |
| 3-5 second cold starts | Instant (cached JSON) |
| Query latency | Zero (local lookup) |
| $0 but rate limited | $0 and unlimited |

---

## Critical Feature: The Mine Graph Visualization

**The Mine should look like Obsidian's graph view or Visuwords.**

Players explore a visual knowledge graph, not a word list.

```
Reference Apps:
- Visuwords (visuwords.com) - Visual WordNet
- Visual Thesaurus - Interactive word web
- Obsidian Graph View - Knowledge connections
```

### What The Mine Looks Like

```
                              [3rd Degree - Fog]
                           ╭─────────────────────╮
                          ╱   ○ ○ ○   ○ ○ ○ ○   ╲
                         ╱  ○             ○  ○   ╲
                        │   [2nd Degree - Dim]    │
                        │  ╭───────────────────╮  │
                        │ ╱  ○──○  ○──○  ○──○  ╲ │
                        ││  [1st Degree - Lit]  ││
                        ││ ╭─────────────────╮ ││
                        ││ │  🧱──⭐──🪨    │ ││
                        ││ │  │   │   │     │ ││
                        ││ │  🪨──🧱──🪨    │ ││
                        ││ ╰─────────────────╯ ││
                        │╲                     ╱│
                        │ ╰───────────────────╯ │
                        ╲                       ╱
                         ╲                     ╱
                          ╰───────────────────╯
```

### Visual States

| State | Visual | Meaning |
|-------|--------|---------|
| ⭐ Current | Glowing, pulsing | Word you're viewing |
| 🟨 Solid | Gold, solid | Mastered |
| 🧱 Hollow | Orange, hollow | Learning |
| 🪨 Raw | Gray, dim | Not started |
| 🔒 Locked | Foggy, barely visible | Outside current degree |

### Data Structure for Visualization

The vocabulary.json must support graph rendering:

```json
{
  "graph_data": {
    "nodes": [
      {
        "id": "break.n.01",
        "word": "break",
        "pos": "n",
        "value": 410,
        "tier": 2,
        "group": "1000"
      }
    ],
    "edges": [
      {
        "source": "break.n.01",
        "target": "opportunity.n.01",
        "type": "related",
        "weight": 1
      },
      {
        "source": "break.n.01",
        "target": "fix.v.01",
        "type": "opposite",
        "weight": 1
      }
    ]
  }
}
```

### Frontend Libraries (for reference)

The frontend will use one of these:
- **react-force-graph** - 3D/2D force-directed graphs
- **cytoscape.js** - Full graph library
- **vis.js** - Network visualization
- **D3.js** - Low-level, flexible

**Data pipeline just needs to export nodes + edges correctly.**

---

## Frontend Visualization Requirements (For Reference)

This section describes what the frontend will build with the data. 
**Data pipeline team**: ensure the data structure supports these features.

### Required Interactions

| Interaction | Description | Data Needed |
|-------------|-------------|-------------|
| **Click to Expand** | Click a node → show its 1st degree connections | `hop_1.senses` |
| **Click to Collapse** | Click expanded node → hide children | Node tracking |
| **Zoom In/Out** | Mouse wheel or pinch gesture | Built into library |
| **Pan/Drag** | Click + drag to move around | Built into library |
| **Hover Preview** | Show definition tooltip on hover | `definition_en`, `definition_zh` |
| **Click to Open** | Double-click → open block detail modal | `sense_id` |
| **Degree Unlock Animation** | New nodes fly in when degree unlocks | `hop_2.senses`, `hop_3.count` |

### Recommended Library: `react-force-graph`

```tsx
import ForceGraph2D from 'react-force-graph-2d'

function MineGraph({ centerSenseId, userProgress }) {
  const [expandedNodes, setExpandedNodes] = useState(new Set([centerSenseId]))
  
  // Build visible graph from expanded nodes
  const visibleData = useMemo(() => {
    const nodes = []
    const links = []
    const seen = new Set()
    
    for (const nodeId of expandedNodes) {
      const sense = vocabulary.getSense(nodeId)
      if (!sense || seen.has(nodeId)) continue
      seen.add(nodeId)
      
      // Add the expanded node
      nodes.push({
        id: nodeId,
        word: sense.word,
        status: userProgress[nodeId] || 'raw',
        isCenter: nodeId === centerSenseId
      })
      
      // Add its 1st degree connections
      for (const connId of sense.hop_1?.senses || []) {
        if (!seen.has(connId)) {
          seen.add(connId)
          const connSense = vocabulary.getSense(connId)
          if (connSense) {
            nodes.push({
              id: connId,
              word: connSense.word,
              status: userProgress[connId] || 'raw',
              isCenter: false
            })
          }
        }
        links.push({ source: nodeId, target: connId })
      }
    }
    
    return { nodes, links }
  }, [expandedNodes, userProgress])

  return (
    <ForceGraph2D
      graphData={visibleData}
      
      // CLICK TO EXPAND/COLLAPSE
      onNodeClick={(node) => {
        setExpandedNodes(prev => {
          const next = new Set(prev)
          if (next.has(node.id)) {
            next.delete(node.id)  // Collapse
          } else {
            next.add(node.id)     // Expand
          }
          return next
        })
      }}
      
      // DOUBLE-CLICK TO OPEN DETAIL
      onNodeRightClick={(node) => {
        openBlockDetailModal(node.id)
      }}
      
      // ZOOM & PAN (built-in)
      enableZoomInteraction={true}
      enablePanInteraction={true}
      
      // NODE COLORS BY STATUS
      nodeColor={(node) => {
        if (node.isCenter) return '#3B82F6'  // Blue - center
        if (node.status === 'solid') return '#FFD700'   // Gold
        if (node.status === 'hollow') return '#F97316'  // Orange
        return '#6B7280'  // Gray - raw
      }}
      
      // NODE SIZE BY VALUE
      nodeVal={(node) => {
        const sense = vocabulary.getSense(node.id)
        return Math.sqrt(sense?.value?.total_xp || 100) / 5
      }}
      
      // HOVER TOOLTIP
      nodeLabel={(node) => {
        const sense = vocabulary.getSense(node.id)
        return `${node.word}\n${sense?.definition_zh || sense?.definition_en || ''}`
      }}
      
      // LINK STYLING
      linkColor={() => 'rgba(255,255,255,0.2)'}
      linkWidth={1}
    />
  )
}
```

### Visual States

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Node States:                                                  │
│   ────────────                                                  │
│                                                                 │
│   ⭐ CENTER      Blue, pulsing         Currently viewing        │
│   🟡 SOLID       Gold, solid fill      Mastered                 │
│   🟠 HOLLOW      Orange, hollow        Learning                 │
│   ⚪ RAW         Gray, dim             Not started              │
│   🔒 LOCKED      Very dim, in fog      Beyond current degree    │
│                                                                 │
│   Edge States:                                                  │
│   ────────────                                                  │
│                                                                 │
│   ─── RELATED    Thin gray line        Synonym/similar          │
│   ═══ OPPOSITE   Dashed red line       Antonym                  │
│   ~~~ PHRASE     Dotted blue line      Part of phrase           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Degree Progression UI

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Initial State (just learned "break"):                          │
│  ──────────────────────────────────                             │
│                                                                 │
│                    [fog]  [fog]  [fog]                          │
│                       ╲     │     ╱                             │
│                        ╲    │    ╱                              │
│           [fog] ─────── ⭐ ─────── [fog]                        │
│                        ╱    │    ╲                              │
│                       ╱     │     ╲                             │
│                    [fog]  [fog]  [fog]                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🔓 1st Degree: 5 words visible                         │   │
│  │  🔒 2nd Degree: Learn 3 more to unlock (12 waiting)     │   │
│  │  🔒 3rd Degree: Complete 2nd degree first (45+ waiting) │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  After learning 3 words (2nd degree unlocks!):                  │
│  ─────────────────────────────────────────────                  │
│                                                                 │
│           [fog]                          [fog]                  │
│              ╲                            ╱                     │
│               ○ luck                 ○ fate                     │
│                ╲                      ╱                         │
│     ○ chance ── 🟡 ─── ⭐ ─── 🟡 ── ○ catch                    │
│                       │                                         │
│                       │                                         │
│                   🟡 fortune                                    │
│                       │                                         │
│                   ○ prosperity                                  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ✅ 1st Degree: COMPLETE! (3/5 learned)                 │   │
│  │  🔓 2nd Degree: 12 words visible                        │   │
│  │  🔒 3rd Degree: Learn 7 from 2nd degree (45+ waiting)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Performance Considerations

With 12,000 words, we need smart loading:

```tsx
// 1. LAZY LOADING - Only load what's visible
const MAX_VISIBLE_NODES = 150

// 2. PROGRESSIVE REVEAL - Animate new nodes in
function animateNewNodes(newNodeIds) {
  for (const id of newNodeIds) {
    // Start invisible, fade in
    nodeOpacity[id] = 0
    animateTo(nodeOpacity[id], 1, { duration: 500 })
  }
}

// 3. CULLING - Hide distant nodes when zoomed in
function cullDistantNodes(centerNode, zoomLevel) {
  const maxDistance = 3 / zoomLevel  // Fewer nodes when zoomed in
  return nodes.filter(n => 
    distanceFromNode(n, centerNode) < maxDistance
  )
}

// 4. LEVEL OF DETAIL - Simplify when zoomed out
function getNodeLabel(node, zoomLevel) {
  if (zoomLevel < 0.5) return ''  // No labels when zoomed out
  if (zoomLevel < 1) return node.word  // Just word
  return `${node.word}\n${node.definition_preview}`  // Full when zoomed in
}
```

### Mobile Touch Support

```tsx
<ForceGraph2D
  // Touch gestures
  enablePointerInteraction={true}
  
  // Larger touch targets on mobile
  nodeRelSize={isMobile ? 8 : 6}
  
  // Disable zoom on mobile (use buttons instead)
  enableZoomInteraction={!isMobile}
/>

// Mobile zoom controls
<div className="fixed bottom-4 right-4 flex gap-2">
  <button onClick={() => graphRef.current.zoom(1.5)}>🔍+</button>
  <button onClick={() => graphRef.current.zoom(0.67)}>🔍-</button>
  <button onClick={() => graphRef.current.centerAt(0, 0)}>🎯</button>
</div>
```

### Data Structure Required

For all the above to work, the vocabulary.json must have:

```json
{
  "senses": {
    "break.n.01": {
      "word": "break",
      "definition_en": "...",
      "definition_zh": "...",
      "hop_1": {
        "senses": ["opportunity.n.01", "chance.n.01", ...],
        "count": 5,
        "unlock_next_at": 3
      },
      "hop_2": {
        "senses": ["luck.n.01", "fate.n.01", ...],
        "count": 12,
        "unlock_next_at": 7
      },
      "hop_3": {
        "count": 45
      },
      "value": {
        "total_xp": 230
      }
    }
  },
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**This is already specified in the deliverables checklist above.**

---

## Critical Game Mechanic: Connection Value System

**READ THIS CAREFULLY** - This is a core feature, not optional!

### The Design (from `docs/30-ux-vision-game-design.md`)

```
Block Value = Base XP + (Connection Count × Connection Bonus)
```

**Hub words with many connections are MORE VALUABLE.**

This drives player behavior:
- Explore connected words → Higher XP
- Discover relationships → Bonus XP
- Learn hub words first → Better ROI

### Connection Types & Bonuses

| Type | Bonus | Example |
|------|-------|---------|
| Related | +10 XP | drop ↔ fall |
| Opposite | +10 XP | drop ↔ catch |
| Phrase | +20 XP | "drop out" |
| Idiom | +30 XP | "drop the ball" |
| Morphological | +10 XP | drop → dropped |

### Example: "break" (hub word)

```
Base XP (Multi-Block):     250 XP
Related words (6):         +60 XP
Opposite words (3):        +30 XP
Phrases (2):               +40 XP
Idioms (1):                +30 XP
─────────────────────────────────
TOTAL VALUE:               410 XP

vs. isolated word:         100 XP
```

**This 4x difference is the game!**

### What Must Be in vocabulary.json

For EVERY sense:
```json
{
  "connections": {
    "related": ["sense_id_1", "sense_id_2"],
    "opposite": ["sense_id_3"],
    "phrases": ["phrase_id_1"],
    "idioms": [],
    "morphological": []
  },
  "connection_counts": {
    "related": 2,
    "opposite": 1,
    "phrases": 1,
    "idioms": 0,
    "morphological": 0,
    "total": 4
  },
  "value": {
    "base_xp": 100,
    "connection_bonus": 50,
    "total_xp": 150
  }
}
```

### Degree-Based Progression System

The graph has "degrees" (like degrees of separation):

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEGREE UNLOCK PROGRESSION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STARTING POINT: User learns "break"                            │
│                                                                  │
│  ═══════════════════════════════════════════════════════════    │
│                                                                  │
│  1ST DEGREE (Immediate)                                          │
│  ─────────────────────                                          │
│  • VISIBLE: 5 directly connected words                          │
│  • Requirement: Learn "break"                                   │
│  • Milestone: "First Connections" 🏆                            │
│                                                                  │
│  2ND DEGREE (Unlock at 60% of 1st)                              │
│  ─────────────────────────────────                              │
│  • VISIBLE: 12 words (friends of friends)                       │
│  • Requirement: Learn 3 of 5 from 1st degree                    │
│  • Milestone: "Network Explorer" 🏆                             │
│  • Bonus: +100 XP discovery bonus                               │
│                                                                  │
│  3RD DEGREE (Unlock at 60% of 2nd)                              │
│  ─────────────────────────────────                              │
│  • VISIBLE: 45+ words (shown as count, not list)                │
│  • Requirement: Learn 7 of 12 from 2nd degree                   │
│  • Milestone: "Web Weaver" 🏆                                   │
│  • Bonus: +250 XP discovery bonus                               │
│                                                                  │
│  NETWORK MASTER (Learn 10+ interconnected words)                │
│  ────────────────────────────────────────────────               │
│  • Special achievement                                           │
│  • Unlocks network visualization mode                           │
│  • Bonus: +500 XP                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Hop Data Structure

```json
{
  "break.n.01": {
    "hop_1": {
      "senses": ["opportunity.n.01", "chance.n.01", "fortune.n.01", "lucky.adj.01", "success.n.01"],
      "count": 5,
      "unlock_next_at": 3
    },
    "hop_2": {
      "senses": ["luck.n.01", "fate.n.01", "destiny.n.01", "achievement.n.01", "prosperity.n.01", ...],
      "count": 12,
      "unlock_next_at": 7
    },
    "hop_3": {
      "count": 45
    },
    "network_value": {
      "total_reachable": 62,
      "potential_xp": 2480
    }
  }
}
```

### Pre-computation Code

```python
def compute_hop_data(sense_id, all_connections, max_hop=3):
    """Compute multi-hop connection data for degree visualization"""
    
    hop_data = {}
    seen = {sense_id}
    current_frontier = {sense_id}
    
    for hop in range(1, max_hop + 1):
        next_frontier = set()
        
        for node in current_frontier:
            connections = all_connections.get(node, {})
            for conn_type in ["related", "opposite"]:
                for neighbor in connections.get(conn_type, []):
                    if neighbor not in seen:
                        next_frontier.add(neighbor)
                        seen.add(neighbor)
        
        if hop <= 2:
            # Full list for hop 1 and 2
            hop_data[f"hop_{hop}"] = {
                "senses": list(next_frontier),
                "count": len(next_frontier),
                "unlock_next_at": max(1, int(len(next_frontier) * 0.6))
            }
        else:
            # Just count for hop 3+
            hop_data[f"hop_{hop}"] = {
                "count": len(next_frontier)
            }
        
        current_frontier = next_frontier
    
    # Total network value
    hop_data["network_value"] = {
        "total_reachable": len(seen) - 1,  # Exclude self
        "potential_xp": (len(seen) - 1) * 40  # Rough estimate
    }
    
    return hop_data
```

### Why This Matters for The Mine

```
Without Degree System:          With Degree System:
─────────────────────          ────────────────────

User sees flat list            User sees expanding universe
of 50 random words             centered on their learning

No sense of progress           Clear progression:
                               "Unlock 2nd degree!"

No exploration feeling         Discovery feeling:
                               "Wow, 45 more words 
                                connected to what I know!"

Boring                         Addictive
```

---

## Architecture Decision: Multi-Authority Hybrid

**DO NOT** go full AI generation (hallucination risk).  
**DO NOT** rely solely on WordNet (academic, not learner-focused).

**DO** use multiple authoritative sources for facts, AI for selection/transformation.

```
┌─────────────────────────────────────────────────────────────┐
│              AUTHORITATIVE SOURCES (Facts)                   │
│                                                              │
│  WordNet ──── Synsets, relationships, POS                    │
│  CC-CEDICT ── Chinese translations (verified)                │
│  EVP/CEFR ─── Difficulty levels (A1-C2)                      │
│  NGSL ─────── Frequency rankings                             │
│  Taiwan MOE ─ Word list, curriculum levels                   │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              AI LAYER (Selection & Transformation)           │
│                                                              │
│  1. Sense Selection ──── "Which 2 senses are useful?"        │
│  2. Simplification ───── "Rewrite for B1/B2"                 │
│  3. Translation Check ── "Is Chinese natural?"               │
│  4. Example Generation ─ "Taiwan-context example"            │
│  5. Validation ───────── "Does example match sense?"         │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              VALIDATION LAYER                                │
│                                                              │
│  Auto: Length checks, character checks, sense match          │
│  Human: Sample review of top 500 words                       │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    vocabulary.json
```

---

## Implementation Tasks

### Phase 1: Add Authority Sources (3 days)

#### Task 1.1: CC-CEDICT Integration
**Goal**: Get verified Chinese translations for every word

**Source**: https://www.mdbg.net/chinese/dictionary?page=cc-cedict  
**Format**: Text file, ~120k entries

**Steps**:
1. Download CC-CEDICT file
2. Parse into Python dict: `{english_word: [translations]}`
3. Save as `backend/data/source/cc-cedict.json`
4. Create lookup function in `backend/src/data_sources/cc_cedict.py`

**Output**: Function `get_translations(word: str) -> List[str]`

#### Task 1.2: CEFR/EVP Integration
**Goal**: Get A1-C2 difficulty levels

**Source**: https://www.englishprofile.org/wordlists/evp  
**Note**: May need to register (free)

**Steps**:
1. Download EVP word list
2. Parse into: `{word: {level: "A1", pos: "noun"}}`
3. Save as `backend/data/source/evp-cefr.json`
4. Create lookup function

**Output**: Function `get_cefr_level(word: str, pos: str) -> str`

#### Task 1.3: Spelling Normalization
**Goal**: Convert British → American spellings

**Steps**:
1. Create mapping file `backend/data/source/spelling_map.json`:
   ```json
   {
     "colour": "color",
     "favour": "favor",
     "honour": "honor",
     "centre": "center",
     ...
   }
   ```
2. Apply during export, keeping British as variant

---

### Phase 2: AI Pipeline Refactor (5 days)

#### Task 2.1: New Sense Selector
**Goal**: AI picks most useful senses, not arbitrary top 3

**File**: Create `backend/src/ai/sense_selector.py`

**Prompt Template**:
```python
SENSE_SELECTION_PROMPT = """
You are helping build a vocabulary app for Taiwan B1/B2 English students.

Word: {word}
Frequency Rank: {rank} (lower = more common)
CEFR Level: {cefr}

All WordNet senses:
{all_senses}

Select the {max_senses} MOST USEFUL senses based on:
1. Daily usage frequency (not academic/technical)
2. Clear distinction from other senses
3. Include at least one verb if commonly used as verb
4. Relevance to Taiwan students

Output JSON:
{
  "selected": [
    {"sense_id": "...", "reason": "..."}
  ]
}
"""
```

#### Task 2.2: Definition Simplifier
**Goal**: Convert academic definitions to B1/B2 level

**Input**: WordNet definition  
**Output**: 15-word max, simple vocabulary

**Prompt**:
```python
SIMPLIFY_PROMPT = """
Rewrite this dictionary definition for a B1/B2 English learner.

Original: {definition}
Word: {word}
POS: {pos}

Rules:
- Maximum 15 words
- Use only common vocabulary
- Start with the word type (noun/verb/adj)
- Be clear and specific

Output just the simplified definition, nothing else.
"""
```

#### Task 2.3: Translation Validator
**Goal**: Verify/improve Chinese translations

**Input**: CC-CEDICT translation + word context  
**Output**: Validated Taiwan Mandarin translation

**Prompt**:
```python
TRANSLATION_PROMPT = """
Check this Chinese translation for a Taiwan student vocabulary app.

English: {word} ({pos})
Definition: {definition}
CC-CEDICT translation: {cc_cedict_translation}

Is this translation:
1. Natural Taiwan Mandarin (繁體中文)?
2. Appropriate for this specific meaning?
3. Not too formal/literary?

If good, output: {"translation": "...", "status": "approved"}
If needs improvement, output: {"translation": "improved version", "status": "improved", "reason": "..."}
"""
```

#### Task 2.4: Example Generator
**Goal**: Create Taiwan-context examples

**Prompt**:
```python
EXAMPLE_PROMPT = """
Create an example sentence for a Taiwan B1/B2 vocabulary app.

Word: {word}
Meaning: {definition}
POS: {pos}

Requirements:
1. 8-15 words
2. Relatable to Taiwan students (school, daily life, social media)
3. Make the meaning OBVIOUS from context
4. Natural, conversational tone

Output JSON:
{
  "example_en": "...",
  "example_zh": "..."
}
"""
```

#### Task 2.5: Example Validator
**Goal**: Verify example matches intended sense

**Prompt**:
```python
VALIDATE_PROMPT = """
Does this example clearly demonstrate this specific meaning?

Word: {word}
Target meaning: {definition}
Example: {example}

Answer:
- "PASS" if example clearly shows this meaning
- "FAIL: reason" if example is ambiguous or shows different meaning
"""
```

---

### Phase 3: Pipeline Orchestration (2 days)

#### Task 3.1: Main Pipeline Script
**File**: `backend/scripts/enrich_vocabulary_v2.py`

**Flow**:
```python
def enrich_word(word: str, frequency_rank: int) -> dict:
    # 1. Gather authorities
    wordnet_senses = get_all_wordnet_senses(word)
    cc_cedict_trans = get_translations(word)
    cefr_level = get_cefr_level(word)
    
    # 2. AI sense selection
    selected_senses = sense_selector.select(
        word, wordnet_senses, 
        max_senses=2 if frequency_rank < 1500 else 1
    )
    
    enriched_senses = []
    for sense in selected_senses:
        # 3. Simplify definition
        simple_def = simplifier.simplify(sense.definition, word, sense.pos)
        
        # 4. Validate translation
        translation = translator.validate(word, simple_def, cc_cedict_trans)
        
        # 5. Generate example
        example = example_gen.generate(word, simple_def, sense.pos)
        
        # 6. Validate example
        validation = validator.validate(word, simple_def, example)
        
        if validation.passed:
            enriched_senses.append({
                "sense_id": sense.id,
                "word": word,
                "pos": sense.pos,
                "cefr": cefr_level,
                "definition_en": simple_def,
                "definition_zh": translation,
                "example_en": example.en,
                "example_zh": example.zh,
                "validated": True
            })
        else:
            # Retry or flag for review
            ...
    
    return enriched_senses
```

#### Task 3.2: Batch Processing
**Goal**: Process 12,000 words with rate limiting

```python
def run_batch_enrichment():
    words = load_word_list()  # 12,000 words
    
    results = []
    for i, word in enumerate(tqdm(words)):
        try:
            enriched = enrich_word(word.name, word.frequency_rank)
            results.extend(enriched)
            
            # Rate limiting
            if i % 100 == 0:
                time.sleep(2)  # Gemini rate limits
                
        except Exception as e:
            log_error(word, e)
            continue
    
    # Export
    export_vocabulary_json(results)
```

---

### Phase 4: Export & Validation (3 days)

#### Task 4.1: New Export Format (WITH HOP DATA - CRITICAL!)
**File**: `landing-page/data/vocabulary.json`

**⚠️ CRITICAL: Block value is based on connections!**

From game design (`docs/30-ux-vision-game-design.md`):
```
Block Value = Base XP + (Connection Count × Connection Bonus)

Connection Bonuses:
- Related word: +10 XP per connection
- Opposite word: +10 XP per connection
- Part of phrase: +20 XP per phrase
- Part of idiom: +30 XP per idiom
- Morphological: +10 XP per pattern
```

**Hub blocks (highly connected) are MORE VALUABLE** - this is a core game mechanic!

**Structure**:
```json
{
  "version": "2.0",
  "exportedAt": "2025-12-XX",
  "stats": {
    "words": 12000,
    "senses": 24000,
    "validated": true
  },
  "words": {
    "drop": {
      "name": "drop",
      "frequency_rank": 1726,
      "moe_level": 1,
      "cefr": "A2",
      "senses": ["drop.v.01", "drop.n.03"]
    }
  },
  "senses": {
    "drop.v.01": {
      "id": "drop.v.01",
      "word": "drop",
      "pos": "v",
      "cefr": "A2",
      "tier": 1,
      "definition_en": "To let something fall from your hand",
      "definition_zh": "讓某物從手中掉落",
      "example_en": "Be careful not to drop your phone!",
      "example_zh": "小心別把手機摔了！",
      "validated": true,
      
      "connections": {
        "related": ["fall.v.01", "descend.v.01"],
        "opposite": ["catch.v.01", "lift.v.01", "raise.v.01"],
        "phrases": [],
        "idioms": [],
        "morphological": []
      },
      "connection_counts": {
        "related": 2,
        "opposite": 3,
        "phrases": 0,
        "idioms": 0,
        "morphological": 0,
        "total": 5
      },
      "value": {
        "base_xp": 100,
        "connection_bonus": 50,
        "total_xp": 150
      },
      
      "two_hop": {
        "discoverable": ["descent.n.01", "grab.v.01"],
        "count": 15
      }
    }
  },
  "bandIndex": {
    "1000": ["the.det.01", "be.v.01", ...],
    "2000": [...],
    ...
  }
}
```

#### Task 4.1.1: Connection & Value Calculation

```python
def calculate_sense_value(sense_id, connections):
    """Calculate block value based on connections (CORE GAME MECHANIC)"""
    
    # Base XP by tier
    TIER_BASE_XP = {
        1: 100,   # Basic block
        2: 250,   # Multi-sense block
        3: 500,   # Phrase block
        4: 1000,  # Idiom block
    }
    
    # Connection bonuses
    BONUS_PER_TYPE = {
        "related": 10,
        "opposite": 10,
        "phrases": 20,
        "idioms": 30,
        "morphological": 10,
    }
    
    tier = get_tier(sense_id)
    base_xp = TIER_BASE_XP.get(tier, 100)
    
    connection_bonus = 0
    for conn_type, bonus in BONUS_PER_TYPE.items():
        count = len(connections.get(conn_type, []))
        connection_bonus += count * bonus
    
    return {
        "base_xp": base_xp,
        "connection_bonus": connection_bonus,
        "total_xp": base_xp + connection_bonus
    }
```

#### Task 4.1.2: Pre-compute 2-Hop for Discovery

The "discovery" mechanic requires knowing what's 2 hops away:

```python
def compute_two_hop(sense_id, all_connections):
    """Find senses 2 hops away (for discovery mechanics)"""
    
    one_hop = set()
    for conn_type in ["related", "opposite"]:
        one_hop.update(all_connections.get(sense_id, {}).get(conn_type, []))
    
    two_hop = set()
    for neighbor in one_hop:
        for conn_type in ["related", "opposite"]:
            two_hop.update(all_connections.get(neighbor, {}).get(conn_type, []))
    
    # Remove self and direct connections
    two_hop.discard(sense_id)
    two_hop -= one_hop
    
    return {
        "discoverable": list(two_hop)[:20],  # Limit for size
        "count": len(two_hop)
    }
```

#### Why This Matters

```
Without connections:
  "drop" = 100 XP (boring)

With connections:
  "drop" = 100 XP base + 50 XP (5 connections) = 150 XP
  
Highly connected hub like "break":
  "break" = 250 XP base + 120 XP (12 connections) = 370 XP
  
This makes players WANT to explore connected words!
```

#### Task 4.2: Validation Report
Generate a report showing:
- Total words/senses processed
- Pass/fail rates for each step
- Words flagged for human review
- Sample outputs for spot checking

---

## File Locations

### Existing (Read/Modify)
```
backend/
├── src/
│   ├── structure_miner.py      # Current WordNet extraction
│   ├── agent.py                 # Current Gemini enrichment
│   ├── adversary_miner.py       # Relationship mining
│   └── data_prep.py             # Word list preparation
├── scripts/
│   └── export_vocabulary_json.py # Current export
├── data/
│   └── processed/
│       └── master_vocab.csv     # 3,500 word list
└── docs/
    └── EXTERNAL_RESOURCES_AND_APIS.md  # Source documentation
```

### New (Create)
```
backend/
├── src/
│   ├── data_sources/
│   │   ├── cc_cedict.py         # CC-CEDICT lookup
│   │   ├── evp_cefr.py          # CEFR level lookup
│   │   └── spelling.py          # British→American
│   └── ai/
│       ├── sense_selector.py    # AI sense selection
│       ├── simplifier.py        # Definition simplifier
│       ├── translator.py        # Translation validator
│       ├── example_gen.py       # Example generator
│       └── validator.py         # Example validator
├── scripts/
│   └── enrich_vocabulary_v2.py  # Main pipeline
└── data/
    └── source/
        ├── cc-cedict.json       # CC-CEDICT parsed
        ├── evp-cefr.json        # CEFR levels
        └── spelling_map.json    # Spelling normalization
```

---

## LLM Strategy

### Recommended: Multi-LLM Approach

Different tasks have different requirements. Use the right model for each:

| Task | Recommended LLM | Why |
|------|----------------|-----|
| Sense Selection | Gemini Flash | Fast, cheap, structured output |
| Definition Simplification | Gemini Flash | Good enough, high volume |
| Chinese Translation Validation | Claude 3.5 Sonnet OR GPT-4o | Better nuanced Chinese |
| Example Generation | Gemini Flash | Creative, fast |
| Example Validation | Claude 3.5 Sonnet | Better at nuanced judgment |
| Final QA (top 500) | Claude 3.5 Sonnet | Highest quality |

### Cost Comparison (per 1M tokens)

| Model | Input | Output | Speed |
|-------|-------|--------|-------|
| Gemini 1.5 Flash | $0.075 | $0.30 | Fast |
| Gemini 1.5 Pro | $1.25 | $5.00 | Medium |
| Claude 3.5 Sonnet | $3.00 | $15.00 | Medium |
| GPT-4o | $2.50 | $10.00 | Medium |
| GPT-4o-mini | $0.15 | $0.60 | Fast |

### Recommended Setup

```python
# config.py
LLM_CONFIG = {
    "bulk_tasks": {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "use_for": ["sense_selection", "simplification", "example_gen"]
    },
    "quality_tasks": {
        "provider": "anthropic",  # or "openai"
        "model": "claude-3-5-sonnet-20241022",
        "use_for": ["translation_validation", "example_validation", "final_qa"]
    },
    "fallback": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "use_for": ["rate_limit_fallback"]
    }
}
```

### Chinese Language Considerations

All major models handle Traditional Chinese well, but:
- **Claude**: Slightly better at nuanced Taiwan Mandarin
- **GPT-4o**: Good, well-tested
- **Gemini**: Good, but occasionally outputs Simplified (add "繁體中文" in prompts)

**Recommendation**: Use Gemini for bulk, Claude/GPT for validation.

---

## Dependencies

### Already Installed
- Python 3.x
- NLTK + WordNet (THIS IS THE SOURCE FOR RELATIONSHIPS - no Neo4j needed!)
- google-generativeai (Gemini)

### Need to Add
- `anthropic` - For Claude API (validation tasks)
- `openai` - For GPT fallback
- `requests` - For downloading sources
- `tqdm` - For progress bars

### API Keys Needed
```bash
# .env
GEMINI_API_KEY=xxx          # Already have
ANTHROPIC_API_KEY=xxx       # Need to add
OPENAI_API_KEY=xxx          # Optional fallback
```

### Estimated API Costs (12k words)

| Task | Calls | Model | Est. Cost |
|------|-------|-------|-----------|
| Sense Selection | 12,000 | Gemini Flash | ~$5 |
| Simplification | 24,000 | Gemini Flash | ~$8 |
| Example Gen | 24,000 | Gemini Flash | ~$8 |
| Translation Valid | 24,000 | Claude Sonnet | ~$30 |
| Example Valid | 24,000 | Claude Sonnet | ~$30 |
| **Total** | | | **~$80-100** |

*Can reduce by using Gemini for all tasks (~$30 total) if budget constrained.*

---

## Success Criteria

### Quantitative
- [ ] 12,000 words processed
- [ ] ~24,000 senses (2 per word avg)
- [ ] 95%+ pass auto-validation
- [ ] <5% flagged for human review
- [ ] File size <50MB uncompressed

### Qualitative
- [ ] No British-only spellings in primary entries
- [ ] No academic/obscure senses (physics, archaic)
- [ ] Examples clearly match intended sense
- [ ] Chinese is natural Taiwan Mandarin
- [ ] CEFR levels present for all entries

### Connection & Value Data (CRITICAL FOR GAME)
- [ ] Every sense has `connections` object with typed relationships
- [ ] Every sense has `connection_counts` with totals
- [ ] Every sense has `value` with base_xp, connection_bonus, total_xp
- [ ] Hub words (10+ connections) have higher values

### Hop/Degree Data (CRITICAL FOR MINE VISUALIZATION)
- [ ] Every sense has `hop_1` with full sense list
- [ ] Every sense has `hop_2` with full sense list  
- [ ] Every sense has `hop_3` with count only
- [ ] `unlock_next_at` thresholds computed (60% of current hop)
- [ ] `network_value` with total_reachable and potential_xp

### Graph Visualization Data
- [ ] `graph_data.nodes` array with id, word, pos, value, tier, group
- [ ] `graph_data.edges` array with source, target, type, weight
- [ ] All edges are bidirectional (or explicitly both directions)

### Integration
- [ ] File drops into `landing-page/data/vocabulary.json`
- [ ] Frontend works without code changes
- [ ] Export script is repeatable

---

## Word List: Where Do 12,000 Words Come From?

### Current: 3,500 words
Source: NGSL + Taiwan MOE merged list
File: `backend/data/processed/master_vocab.csv`

### Target: 12,000 words

| Source | Words | Notes |
|--------|-------|-------|
| Taiwan MOE 7000 | 7,000 | Official curriculum |
| NGSL extended | 2,800 | High frequency |
| Academic Word List | 570 | University prep |
| TOEFL/IELTS common | ~1,600 | Test prep |

**Task**: Create expanded `master_vocab_12k.csv`

```python
# Merge sources, deduplicate, rank by:
# 1. MOE level (1-6)
# 2. NGSL frequency
# 3. Test frequency
```

---

## Handling Missing Data

### Words Not in CC-CEDICT

~5-10% of words may not have CC-CEDICT entries.

**Fallback Strategy**:
```python
def get_translation(word, definition):
    # 1. Try CC-CEDICT
    trans = cc_cedict.lookup(word)
    if trans:
        return {"source": "cc-cedict", "translation": trans}
    
    # 2. Fallback to AI generation
    trans = ai_translate(word, definition)
    return {"source": "ai-generated", "translation": trans, "needs_review": True}
```

### Words Not in EVP/CEFR

~20-30% may not have CEFR levels.

**Fallback Strategy**:
```python
def get_cefr_level(word, frequency_rank):
    # 1. Try EVP lookup
    level = evp.lookup(word)
    if level:
        return level
    
    # 2. Estimate from frequency
    if frequency_rank < 1000:
        return "A1"
    elif frequency_rank < 2000:
        return "A2"
    elif frequency_rank < 4000:
        return "B1"
    elif frequency_rank < 7000:
        return "B2"
    else:
        return "C1"
```

---

## Error Handling Strategy

### Retry Logic

```python
MAX_RETRIES = 3
RETRY_DELAY = [2, 5, 10]  # seconds

def call_with_retry(func, *args):
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args)
        except RateLimitError:
            time.sleep(RETRY_DELAY[attempt])
        except Exception as e:
            log_error(e)
            if attempt == MAX_RETRIES - 1:
                return None  # Flag for manual review
    return None
```

### Error Categories

| Error Type | Action |
|------------|--------|
| Rate limit | Retry with backoff |
| API timeout | Retry once, then skip |
| Validation fail | Retry with different prompt |
| 3x validation fail | Flag for human review |
| Missing source data | Use fallback |

### Error Log

```python
# Save to backend/logs/enrichment_errors.json
{
    "word": "example",
    "sense_id": "example.n.01",
    "error_type": "validation_fail",
    "error_message": "Example doesn't match sense",
    "attempts": 3,
    "timestamp": "2025-12-06T10:00:00Z",
    "status": "flagged_for_review"
}
```

---

## Testing Strategy

### Phase 1: Unit Tests (Before Full Run)

Test each component with 10 words:

```python
TEST_WORDS = [
    "drop",      # Common, multiple POS
    "colour",    # British spelling
    "bank",      # Multiple distinct senses
    "run",       # Many phrasal verbs
    "set",       # Most senses in English
    "good",      # Common adjective
    "go",        # Irregular verb
    "technology", # Academic
    "selfie",    # Modern slang
    "bubble tea", # Taiwan-specific (if included)
]
```

### Phase 2: Pilot Run (100 words)

Run full pipeline on 100 random words:
- Check output format
- Verify all fields populated
- Spot-check quality
- Measure API costs

### Phase 3: Batch Run (1000 words)

Run on first 1000 words:
- Check error rate
- Verify rate limiting works
- Calculate full-run time estimate
- Review flagged entries

### Phase 4: Full Run (12000 words)

- Run overnight if needed
- Monitor progress
- Handle interruptions gracefully (resume capability)

---

## Incremental vs Full Rebuild

### For MVP: Full Rebuild

The current data has too many issues. Start fresh.

### For Future: Incremental Updates

```python
def needs_update(sense_id, current_version):
    """Check if sense needs re-enrichment"""
    entry = db.get(sense_id)
    
    # New word
    if not entry:
        return True
    
    # Schema changed
    if entry.version < current_version:
        return True
    
    # Flagged for review
    if entry.needs_review:
        return True
    
    # Previously failed
    if entry.validation_failed:
        return True
    
    return False
```

### Resume Capability

```python
def get_processed_words():
    """Get words already processed in this run"""
    if os.path.exists("enrichment_progress.json"):
        with open("enrichment_progress.json") as f:
            return set(json.load(f)["completed"])
    return set()

def save_progress(completed_words):
    with open("enrichment_progress.json", "w") as f:
        json.dump({"completed": list(completed_words)}, f)
```

---

## Relationship Mining Update

### Option A: Use Neo4j (if available)

Mine relationships from Neo4j during enrichment:

```python
def get_relationships_from_neo4j(sense_id):
    """Get relationships from Neo4j graph"""
    with neo4j_conn.get_session() as session:
        result = session.run("""
            MATCH (s:Sense {id: $sense_id})<-[:HAS_SENSE]-(w:Word)
            OPTIONAL MATCH (w)-[:RELATED_TO]->(w2:Word)-[:HAS_SENSE]->(s2:Sense)
            OPTIONAL MATCH (w)-[:OPPOSITE_TO]->(w3:Word)-[:HAS_SENSE]->(s3:Sense)
            RETURN collect(DISTINCT s2.id) as related, collect(DISTINCT s3.id) as opposite
        """, sense_id=sense_id)
        record = result.single()
        return {
            "related": record["related"] or [],
            "opposite": record["opposite"] or []
        }
```

### Option B: Use Existing vocabulary.json (NO Neo4j needed)

The current vocabulary.json already has relationships. Extract and reuse:

```python
def get_relationships_from_current_json():
    """Extract relationships from existing vocabulary.json"""
    with open("landing-page/data/vocabulary.json") as f:
        current = json.load(f)
    return current.get("relationships", {})

# Then filter to only valid new sense IDs
def migrate_relationships(current_relationships, new_sense_ids):
    valid_ids = set(new_sense_ids)
    migrated = {}
    for sense_id, rels in current_relationships.items():
        if sense_id in valid_ids:
            migrated[sense_id] = {
                "related": [r for r in rels.get("related", []) if r in valid_ids],
                "opposite": [r for r in rels.get("opposite", []) if r in valid_ids]
            }
    return migrated
```

### Option C: Mine Fresh from WordNet (NO Neo4j needed)

Use NLTK WordNet directly:

```python
from nltk.corpus import wordnet as wn

def get_relationships_from_wordnet(sense_id):
    """Get relationships directly from WordNet"""
    try:
        synset = wn.synset(sense_id)
    except:
        return {"related": [], "opposite": []}
    
    # Get lemmas and their relationships
    related = []
    opposite = []
    
    for lemma in synset.lemmas():
        # Antonyms
        for ant in lemma.antonyms():
            opposite.append(ant.synset().name())
        
        # Similar (for adjectives)
        for sim in synset.similar_tos():
            related.append(sim.name())
        
        # Also_sees
        for also in synset.also_sees():
            related.append(also.name())
    
    return {
        "related": list(set(related)),
        "opposite": list(set(opposite))
    }
```

### Decision: USE OPTION C (with B for validation)

**Primary: Option C (WordNet directly)**
- Covers ALL 12,000 words consistently
- No Neo4j dependency
- Same authoritative source (Neo4j was mining WordNet anyway)
- Clean, consistent approach

**Secondary: Option B (for validation only)**
- Cross-check the 3,500 overlapping words
- If Option C misses relationships that B has, investigate
- Catches regressions

**Why NOT Option A (Neo4j)**:
- Adds unnecessary complexity
- We're trying to eliminate Neo4j, not keep using it
- Option C gets the same data without the middleman

**Why NOT Option B alone**:
- Only covers 3,500 words
- We need 12,000 words
- New words would have zero relationships

### Post-Processing

After getting relationships, filter to only valid sense IDs:

```python
def finalize_relationships(new_senses, raw_relationships):
    """Ensure relationships reference valid sense IDs"""
    valid_sense_ids = set(s["sense_id"] for s in new_senses)
    
    final = {}
    for sense_id in valid_sense_ids:
        rels = raw_relationships.get(sense_id, {})
        final[sense_id] = {
            "related": [r for r in rels.get("related", []) if r in valid_sense_ids],
            "opposite": [r for r in rels.get("opposite", []) if r in valid_sense_ids]
        }
    return final
```

---

## Blockers / Risks

| Risk | Mitigation |
|------|------------|
| Gemini rate limits | Add delays, use fallback LLM |
| Claude rate limits | Batch validation, spread over time |
| CC-CEDICT parsing issues | Test with sample first |
| EVP access restrictions | Have fallback (frequency-based estimation) |
| Validation failures | Retry logic + human queue |
| API costs exceed budget | Start with Gemini-only (~$30) |
| Interrupted run | Resume capability |
| Output format mismatch | Schema validation before save |

---

## Communication

### Handoff Complete When
1. You've read this document
2. You can access all file locations
3. You understand the architecture
4. You have questions answered

### Progress Updates
Update this file with:
- Phase completion status
- Any architecture changes
- Blockers encountered

### Final Delivery
1. New `vocabulary.json` in `landing-page/data/`
2. Updated export script
3. Validation report
4. Any new documentation

---

## Questions?

If anything is unclear, the key documents are:
- `/docs/DATA_PIPELINE_V2_PROPOSAL.md` - Full architecture
- `/docs/DATA_PIPELINE_ARCHITECTURE_REVIEW.md` - Why we made these decisions
- `/docs/examples/SENSE_SELECTION_PROMPT_DESIGN.md` - Prompt examples
- `/backend/docs/EXTERNAL_RESOURCES_AND_APIS.md` - Data sources

---

---

## Quick Start Checklist

Before starting, verify you have:

- [ ] Access to codebase at `/Users/kurtchen/LexiCraft AG/`
- [ ] Can run Python in `backend/` directory
- [ ] `GEMINI_API_KEY` in `.env` file
- [ ] (Optional) `ANTHROPIC_API_KEY` for quality tasks
- [ ] Read this entire document

**NOTE: Neo4j is NOT required.** Relationships come from WordNet via NLTK.

### First Steps

```bash
# 1. Test existing setup works
cd backend
source venv/bin/activate
python -c "import google.generativeai; print('Gemini OK')"

# 2. Test WordNet (for relationships)
python -c "from nltk.corpus import wordnet as wn; print(f'WordNet OK: {len(list(wn.all_synsets()))} synsets')"

# 2. Download CC-CEDICT
mkdir -p data/source
curl -o data/source/cedict_ts.u8 "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
gunzip data/source/cedict_ts.u8.gz

# 3. Run test with 10 words
python scripts/enrich_vocabulary_v2.py --test --limit 10
```

---

## Verification: How to Know It's Working

### After Phase 1 (Authority Sources)
```python
# Test CC-CEDICT
from src.data_sources.cc_cedict import get_translations
print(get_translations("drop"))  # Should return ['掉', '落下', ...]

# Test CEFR
from src.data_sources.evp_cefr import get_cefr_level
print(get_cefr_level("drop"))  # Should return 'A2' or 'B1'
```

### After Phase 2 (AI Pipeline)
```python
# Test sense selection
from src.ai.sense_selector import SenseSelector
selector = SenseSelector()
result = selector.select("drop", all_wordnet_senses)
print(result)  # Should return 2 useful senses

# Test full enrichment
from scripts.enrich_vocabulary_v2 import enrich_word
result = enrich_word("drop", frequency_rank=1726)
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### After Phase 3 (Full Run)
```bash
# Check output file
ls -la landing-page/data/vocabulary.json
# Should be ~40MB

# Validate structure
python -c "
import json
with open('landing-page/data/vocabulary.json') as f:
    data = json.load(f)
print(f'Words: {len(data[\"words\"])}')
print(f'Senses: {len(data[\"senses\"])}')
print(f'Version: {data[\"version\"]}')
"
```

---

## Deliverables Checklist

When complete, ensure you have:

- [ ] `landing-page/data/vocabulary.json` (new file, ~40MB)
- [ ] `backend/data/source/cc-cedict.json` (parsed CC-CEDICT)
- [ ] `backend/data/source/evp-cefr.json` (CEFR levels)
- [ ] `backend/scripts/enrich_vocabulary_v2.py` (main script)
- [ ] `backend/src/data_sources/` (new modules)
- [ ] `backend/src/ai/` (AI pipeline modules)
- [ ] `backend/logs/enrichment_report.json` (stats + errors)
- [ ] Updated this handoff doc with completion notes

### Final JSON Structure Example

Here's what a complete sense should look like:

```json
{
  "drop.v.01": {
    "word": "drop",
    "pos": "v",
    "definition_en": "let fall to the ground",
    "definition_zh": "讓...掉落",
    "example_en": "She dropped her keys on the table.",
    "example_zh": "她把鑰匙放在桌上。",
    "cefr": "A2",
    "frequency_rank": 245,
    "tier": 2,
    "connections": {
      "related": ["fall.v.01", "descend.v.01"],
      "opposite": ["catch.v.01", "raise.v.01"],
      "phrases": ["drop_off.v.01", "drop_out.v.01"]
    },
    "connection_counts": {
      "related": 2,
      "opposite": 2,
      "phrases": 2,
      "total": 6
    },
    "hop_1": {
      "senses": ["fall.v.01", "descend.v.01", "catch.v.01", "raise.v.01"],
      "count": 4,
      "unlock_next_at": 3
    },
    "hop_2": {
      "senses": ["plunge.v.01", "tumble.v.01", "grab.v.01", "lift.v.01"],
      "count": 12,
      "unlock_next_at": 7
    },
    "hop_3": {
      "count": 45
    },
    "network_value": {
      "total_reachable": 61,
      "potential_xp": 2440
    },
    "value": {
      "base_xp": 150,
      "connection_bonus": 80,
      "total_xp": 230
    }
  }
}
```

### Graph Data Structure (for Visualization)

The file should also include a `graph_data` section for Obsidian-style visualization:

```json
{
  "graph_data": {
    "nodes": [
      {
        "id": "drop.v.01",
        "word": "drop",
        "pos": "v",
        "value": 230,
        "tier": 2,
        "group": "500"
      }
    ],
    "edges": [
      { "source": "drop.v.01", "target": "fall.v.01", "type": "related" },
      { "source": "drop.v.01", "target": "catch.v.01", "type": "opposite" }
    ]
  }
}
```

**Size estimate**: ~25-35 MB total (graph_data adds ~5-8 MB)

---

### Connection Data Verification (CRITICAL)

Run this to verify connection data is complete:

```python
import json

with open("landing-page/data/vocabulary.json") as f:
    data = json.load(f)

# Check every sense has connection data
missing_connections = []
missing_values = []

for sense_id, sense in data["senses"].items():
    if "connections" not in sense or "connection_counts" not in sense:
        missing_connections.append(sense_id)
    if "value" not in sense:
        missing_values.append(sense_id)

print(f"Senses missing connections: {len(missing_connections)}")
print(f"Senses missing values: {len(missing_values)}")

# Should both be 0!

# Check hub words have high values
hub_words = [(sid, s["value"]["total_xp"]) 
             for sid, s in data["senses"].items() 
             if s.get("connection_counts", {}).get("total", 0) > 10]
hub_words.sort(key=lambda x: -x[1])
print(f"\nTop 10 hub words by value:")
for sid, xp in hub_words[:10]:
    print(f"  {sid}: {xp} XP")
```

### Hop/Degree Data Verification

```python
import json

with open("landing-page/data/vocabulary.json") as f:
    data = json.load(f)

missing_hop_1 = []
missing_hop_2 = []
missing_hop_3 = []
missing_network = []

for sense_id, sense in data["senses"].items():
    if "hop_1" not in sense:
        missing_hop_1.append(sense_id)
    if "hop_2" not in sense:
        missing_hop_2.append(sense_id)
    if "hop_3" not in sense:
        missing_hop_3.append(sense_id)
    if "network_value" not in sense:
        missing_network.append(sense_id)

print(f"Senses missing hop_1: {len(missing_hop_1)}")
print(f"Senses missing hop_2: {len(missing_hop_2)}")
print(f"Senses missing hop_3: {len(missing_hop_3)}")
print(f"Senses missing network_value: {len(missing_network)}")

# Check hop data makes sense
sample_sense = list(data["senses"].values())[0]
if "hop_1" in sample_sense:
    print(f"\nSample hop data:")
    print(f"  hop_1 count: {sample_sense['hop_1']['count']}")
    print(f"  hop_2 count: {sample_sense.get('hop_2', {}).get('count', 'N/A')}")
    print(f"  hop_3 count: {sample_sense.get('hop_3', {}).get('count', 'N/A')}")
    print(f"  network total: {sample_sense.get('network_value', {}).get('total_reachable', 'N/A')}")
```

### Graph Data Verification

```python
import json

with open("landing-page/data/vocabulary.json") as f:
    data = json.load(f)

if "graph_data" not in data:
    print("ERROR: graph_data section missing!")
else:
    nodes = data["graph_data"]["nodes"]
    edges = data["graph_data"]["edges"]
    print(f"Graph nodes: {len(nodes)}")
    print(f"Graph edges: {len(edges)}")
    
    # Check all sense IDs have nodes
    sense_ids = set(data["senses"].keys())
    node_ids = set(n["id"] for n in nodes)
    missing = sense_ids - node_ids
    print(f"Senses without nodes: {len(missing)}")
    
    # Check edges reference valid nodes
    invalid_edges = [e for e in edges if e["source"] not in node_ids or e["target"] not in node_ids]
    print(f"Invalid edges: {len(invalid_edges)}")
```

---

## Contact / Questions

If you get stuck:
1. Check the related docs listed above
2. Review error logs
3. Test with smaller batches
4. Document the issue in this handoff file

---

## Implementation Progress Log

### 2025-12-06: Initial Implementation Complete

**Completed:**

1. **Phase 1: Authority Sources** ✅
   - CC-CEDICT integration: 53,176 English words indexed from 124k Chinese entries
   - EVP/CEFR bootstrap data: 230 common words with levels
   - British→American spelling map: 310 word pairs
   - Files created:
     - `backend/src/data_sources/cc_cedict.py`
     - `backend/src/data_sources/evp_cefr.py`
     - `backend/src/data_sources/spelling.py`
     - `backend/data/source/cc-cedict.json` (97.8 MB)
     - `backend/data/source/evp-cefr.json`
     - `backend/data/source/spelling_map.json`

2. **Phase 2: AI Pipeline** ✅
   - Sense selector: Picks most useful WordNet senses via Gemini
   - Definition simplifier: B1/B2 level definitions  
   - Translation validator: Validates CC-CEDICT translations
   - Example generator: Taiwan-context examples (捷運, 珍珠奶茶, 小七, etc.)
   - Example validator: Verifies examples match intended sense
   - Files created:
     - `backend/src/ai/base.py` (shared LLM config, retry logic)
     - `backend/src/ai/sense_selector.py`
     - `backend/src/ai/simplifier.py`
     - `backend/src/ai/translator.py`
     - `backend/src/ai/example_gen.py`
     - `backend/src/ai/validator.py`

3. **Phase 3: Pipeline Orchestration** ✅
   - Main pipeline script with full enrichment flow
   - WordNet relationship mining (NO Neo4j required!)
   - Checkpoint/resume capability
   - Rate limiting and error handling
   - Files created:
     - `backend/scripts/enrich_vocabulary_v2.py`

4. **Phase 4: Export & Validation** ✅
   - JSON export with:
     - `connections` and `connection_counts` for each sense
     - `value` with base_xp, connection_bonus, total_xp
     - `hop_1`, `hop_2`, `hop_3` for degree progression
     - `network_value` with total_reachable and potential_xp
     - `graph_data` with nodes and edges for visualization
   - Pilot test with 20 words: 18 senses created, 10/18 validated

**Pending:**

1. **Word List Expansion** (Phase 4.1)
   - Current: 3,500 words
   - Target: 12,000 words
   - Need to integrate: AWL (Academic Word List), TOEFL vocabulary
   - This is a data acquisition task, not code

2. **Translation Quality Issues**
   - CC-CEDICT lookup sometimes returns unrelated translations
   - The AI validator should catch these but occasionally fails
   - Consider using AI-only translations for function words

**How to Run:**

```bash
# Test with 10 words
cd backend
source venv/bin/activate
python scripts/enrich_vocabulary_v2.py --test --limit 10

# Full run (3,500 words with current list)
python scripts/enrich_vocabulary_v2.py

# Resume interrupted run
python scripts/enrich_vocabulary_v2.py --resume
```

**Output Files:**
- `backend/data/vocabulary.json`
- `landing-page/data/vocabulary.json`
- `backend/logs/enrichment_report.json`
- `backend/logs/enrichment_checkpoint.json`

**Estimated Runtime:**
- 20 words: ~2 minutes
- 100 words: ~10 minutes
- 3,500 words: ~6-8 hours (with rate limiting)
- 12,000 words: ~20-24 hours

**Estimated API Cost:**
- Current 3,500 words: ~$25-30 (Gemini Flash)
- Target 12,000 words: ~$80-100 (with Claude for validation)

---

### 2025-12-06 22:50: Pipeline Running (Live Status)

**State**: ✅ Running smoothly overnight

| Metric | Value |
|--------|-------|
| Progress | 704 / 3,495 words (20.14%) |
| Current word | "far" |
| Senses created | 1,263 (~1.8 per word) |
| Validation pass rate | 89.4% (1,129/1,263) |
| Errors | 0 |
| AI calls | 5,980 |
| Cost so far | $0.60 USD (~NT$19) |
| ETA | ~6:30 AM (Dec 7) |

**Observations:**
- 1.8 senses/word = good filtering (not grabbing all WordNet senses)
- 89.4% validation = healthy (industry standard 85%+)
- Cost WAY under budget (~$3 projected vs $25-30 estimated)
- Zero errors = excellent stability

**Projected Final Cost:**
- 3,500 words: ~$3 USD (10x under budget!)
- 12,000 words: ~$10-12 USD

**When Complete (check these):**
```bash
# 1. Verify hop data exists
python -c "
import json
with open('backend/data/vocabulary.json') as f:
    data = json.load(f)
sample = list(data['senses'].values())[0]
print('hop_1:', 'senses' in sample.get('hop_1', {}))
print('hop_2:', 'count' in sample.get('hop_2', {}))
print('graph_data:', 'graph_data' in data)
"

# 2. Check validation failures
grep -c '"validated": false' backend/data/vocabulary.json

# 3. Copy to frontend
cp backend/data/vocabulary.json landing-page/data/vocabulary.json
```

---

*Handoff created: 2025-12-06*
*Implementation started: 2025-12-06*
*Phase 1-4 code complete: 2025-12-06*
*Pipeline running: 2025-12-06 20:52 → ETA 2025-12-07 06:30*

