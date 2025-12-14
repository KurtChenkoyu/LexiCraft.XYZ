'use client'

import { type VocabularySense } from '@/lib/vocabulary'

interface WordValueBadgeProps {
  sense: VocabularySense
  variant?: 'full' | 'compact' | 'mini'
  className?: string
}

/**
 * Calculate connection count from sense data
 */
function getConnectionCount(sense: VocabularySense): number {
  const connections = sense.connections
  if (!connections) return 0
  
  let count = 0
  
  // Count synonyms
  if (connections.synonyms?.display_words) {
    count += connections.synonyms.display_words.length
  }
  
  // Count antonyms
  if (connections.antonyms?.display_words) {
    count += connections.antonyms.display_words.length
  }
  
  // Count similar words
  if (connections.similar_words?.display_words) {
    count += connections.similar_words.display_words.length
  }
  
  // Count collocations
  if (connections.collocations) {
    count += connections.collocations.length
  }
  
  // Count word family entries
  if (connections.word_family) {
    const family = connections.word_family
    count += (family.noun?.length || 0)
    count += (family.verb?.length || 0)
    count += (family.adjective?.length || 0)
    count += (family.adverb?.length || 0)
  }
  
  return count
}

/**
 * Get XP value from sense (handles different field locations)
 */
function getXpValue(sense: VocabularySense): number {
  // Try value.total_xp first
  if (sense.value?.total_xp) {
    return sense.value.total_xp
  }
  
  // Fallback: calculate from tier
  const tier = sense.tier || 1
  const tierBaseXp: Record<number, number> = {
    1: 100,
    2: 250,
    3: 500,
    4: 1000,
    5: 300,
    6: 400,
    7: 750,
  }
  
  const baseXp = tierBaseXp[tier] || 100
  const connectionCount = getConnectionCount(sense)
  const connectionBonus = connectionCount * 10 // Simplified: 10 XP per connection
  
  return baseXp + connectionBonus
}

/**
 * Get CEFR color class
 */
function getCefrColor(cefr?: string): string {
  switch (cefr) {
    case 'A1':
      return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    case 'A2':
      return 'bg-green-500/20 text-green-400 border-green-500/30'
    case 'B1':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    case 'B2':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
    case 'C1':
      return 'bg-red-500/20 text-red-400 border-red-500/30'
    case 'C2':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    default:
      return 'bg-slate-500/20 text-slate-400 border-slate-500/30'
  }
}

/**
 * Get connection color based on count
 */
function getConnectionColor(count: number): string {
  if (count >= 15) return 'text-amber-400' // Hub word!
  if (count >= 10) return 'text-cyan-400'
  if (count >= 5) return 'text-blue-400'
  return 'text-slate-400'
}

/**
 * WordValueBadge - Shows word value metrics (XP, connections, difficulty)
 * 
 * Variants:
 * - full: Shows all three metrics with labels
 * - compact: Shows all three as small badges
 * - mini: Shows just XP value (for grid squares)
 */
export function WordValueBadge({ sense, variant = 'compact', className = '' }: WordValueBadgeProps) {
  const xp = getXpValue(sense)
  const connections = getConnectionCount(sense)
  const cefr = sense.cefr || 'B1'
  
  if (variant === 'mini') {
    return (
      <div className={`flex items-center gap-1 ${className}`}>
        <span className="text-amber-400 text-xs font-bold">💎{xp}</span>
      </div>
    )
  }
  
  if (variant === 'compact') {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {/* XP */}
        <span className="px-1.5 py-0.5 text-xs font-bold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
          💎 {xp}
        </span>
        
        {/* Connections */}
        {connections > 0 && (
          <span className={`text-xs font-medium ${getConnectionColor(connections)}`}>
            🔗{connections}
          </span>
        )}
        
        {/* CEFR */}
        <span className={`px-1.5 py-0.5 text-xs font-bold rounded border ${getCefrColor(cefr)}`}>
          {cefr}
        </span>
      </div>
    )
  }
  
  // Full variant
  return (
    <div className={`flex flex-wrap items-center gap-3 ${className}`}>
      {/* XP */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-slate-500">Value:</span>
        <span className="px-2 py-0.5 text-sm font-bold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
          💎 {xp} XP
        </span>
      </div>
      
      {/* Connections */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-slate-500">Links:</span>
        <span className={`text-sm font-medium ${getConnectionColor(connections)}`}>
          🔗 {connections}
        </span>
        {connections >= 15 && (
          <span className="text-xs text-amber-400">Hub!</span>
        )}
      </div>
      
      {/* CEFR Difficulty */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-slate-500">Level:</span>
        <span className={`px-2 py-0.5 text-sm font-bold rounded border ${getCefrColor(cefr)}`}>
          {cefr}
        </span>
      </div>
    </div>
  )
}

// Export utilities for use elsewhere
export { getXpValue, getConnectionCount, getCefrColor }


