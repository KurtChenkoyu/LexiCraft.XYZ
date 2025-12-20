'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { vocabulary, VocabularySense } from '@/lib/vocabulary'
import { getXpValue } from '@/components/features/vocabulary'
import { useAppStore } from '@/stores/useAppStore'

type StatusFilter = 'all' | 'raw' | 'hollow' | 'solid'
type SortBy = 'relevance' | 'xp' | 'cefr' | 'connections'

// Individual sense result
interface SenseResult {
  sense_id: string
  pos?: string
  cefr?: string
  definition_en?: string
  definition_zh?: string
  connection_count: number
  xp_value: number
  status: 'raw' | 'hollow' | 'solid'
  score: number
  word?: string       // The actual word field (may be inflected like "were")
}

// Grouped word result (groups multiple senses of same lemma)
interface GroupedResult {
  type: 'word' | 'phrase'
  lemma: string       // The base form (e.g., "be")
  displayWord?: string // Show if different from lemma (e.g., "were")
  primary: SenseResult
  otherSenses: SenseResult[]
  totalXp: number
  bestCefr?: string
  // For phrases
  phrase?: string
  phrase_meaning?: string
}

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
  userProgress?: Record<string, 'raw' | 'hollow' | 'solid'>
  onSelectWord?: (senseId: string) => void
  onStartForging?: (senseId: string) => void
}

// CEFR level badge colors
const cefrColors: Record<string, string> = {
  'A1': 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  'A2': 'bg-green-500/20 text-green-300 border-green-500/40',
  'B1': 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  'B2': 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  'C1': 'bg-rose-500/20 text-rose-300 border-rose-500/40',
  'C2': 'bg-purple-500/20 text-purple-300 border-purple-500/40',
}

// Status colors
const statusColors = {
  solid: { bg: 'bg-amber-600/30', text: 'text-amber-300', label: '已掌握' },
  hollow: { bg: 'bg-red-600/30', text: 'text-red-300', label: '學習中' },
  raw: { bg: 'bg-slate-600/30', text: 'text-slate-400', label: '未開始' },
}

// POS display names
const posLabels: Record<string, string> = {
  'n': '名', 'v': '動', 'adj': '形', 'adv': '副',
  'a': '形', 's': '形', 'r': '副', 'noun': '名',
  'verb': '動', 'prep': '介', 'conj': '連', 'pron': '代',
}

// CEFR ordering (lower = easier)
const cefrOrder = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

export function SearchModal({
  isOpen,
  onClose,
  userProgress = {},
  onSelectWord,
  onStartForging,
}: SearchModalProps) {
  // Mining queue from global store
  const miningQueue = useAppStore((state) => state.miningQueue)
  const addToQueue = useAppStore((state) => state.addToQueue)
  const removeFromQueue = useAppStore((state) => state.removeFromQueue)
  const miningQueueCount = miningQueue.length

  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortBy, setSortBy] = useState<SortBy>('relevance')
  const [results, setResults] = useState<GroupedResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isSearching, setIsSearching] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const resultsContainerRef = useRef<HTMLDivElement>(null)

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
      setQuery('')
      setResults([])
      setSelectedIndex(0)
    }
  }, [isOpen])

  // Calculate connection count from sense
  const getConnectionCount = (sense: VocabularySense): number => {
    const conns = sense.connections || {}
    return (
      (conns.synonyms?.display_words?.length || 0) +
      (conns.antonyms?.display_words?.length || 0) +
      (conns.similar_words?.display_words?.length || 0) +
      (conns.collocations?.length || 0)
    )
  }

  // Helper to extract lemma from sense_id (e.g., "be.v.01" -> "be")
  const extractLemma = (senseId: string): string => {
    return senseId.split('.')[0] || senseId
  }

  // Search function with grouping
  const performSearch = useCallback(async (searchQuery: string, filter: StatusFilter) => {
    const normalizedQuery = searchQuery.toLowerCase().trim()
    
    // Raw results before grouping
    const rawResults: Array<SenseResult & { lemma: string; word: string }> = []

    // Get word results from vocabulary
    const vocabResults = await vocabulary.searchSenses(normalizedQuery, {
      limit: 150,
      sortBy: 'relevance'
    })

    for (const sense of vocabResults) {
      const senseId = sense.id || ''
      const status = userProgress[senseId] || 'raw'
      
      if (filter !== 'all' && status !== filter) continue

      // Extract lemma from sense_id (more reliable than lemma field)
      const lemma = extractLemma(senseId)

      rawResults.push({
        lemma,
        word: sense.word,
        sense_id: senseId,
        pos: sense.pos || undefined,
        cefr: sense.cefr,
        definition_en: sense.definition_en || sense.definition,
        definition_zh: sense.definition_zh,
        connection_count: getConnectionCount(sense),
        xp_value: getXpValue(sense),
        status,
        score: sense.score,
      })
    }

    // Group by LEMMA (not word) - this is the key fix!
    const lemmaGroups = new Map<string, Array<SenseResult & { lemma: string; word: string }>>()
    
    for (const result of rawResults) {
      const key = result.lemma.toLowerCase()
      if (!lemmaGroups.has(key)) {
        lemmaGroups.set(key, [])
      }
      lemmaGroups.get(key)!.push(result)
    }

    // Convert to grouped results
    const groupedResults: GroupedResult[] = []
    
    for (const [lemmaKey, senses] of Array.from(lemmaGroups)) {
      // Sort senses by score (best first)
      senses.sort((a, b) => b.score - a.score)
      
      const primary = senses[0]
      const otherSenses = senses.slice(1)
      
      // Calculate total XP
      const totalXp = senses.reduce((sum, s) => sum + s.xp_value, 0)
      
      // Find best (easiest) CEFR
      const bestCefr = senses
        .map(s => s.cefr)
        .filter(Boolean)
        .sort((a, b) => cefrOrder.indexOf(a!) - cefrOrder.indexOf(b!))[0]

      // Check if any word differs from lemma
      const hasVariant = senses.some(s => s.word.toLowerCase() !== lemmaKey)

      groupedResults.push({
        type: 'word',
        lemma: primary.lemma,
        displayWord: hasVariant ? primary.word : undefined,
        primary: {
          sense_id: primary.sense_id,
          pos: primary.pos,
          cefr: primary.cefr,
          definition_en: primary.definition_en,
          definition_zh: primary.definition_zh,
          connection_count: primary.connection_count,
          xp_value: primary.xp_value,
          status: primary.status,
          score: primary.score,
          word: primary.word,
        },
        otherSenses: otherSenses.map(s => ({
          sense_id: s.sense_id,
          pos: s.pos,
          cefr: s.cefr,
          definition_en: s.definition_en,
          definition_zh: s.definition_zh,
          connection_count: s.connection_count,
          xp_value: s.xp_value,
          status: s.status,
          score: s.score,
          word: s.word,
        })),
        totalXp,
        bestCefr,
      })
    }

    // Search collocations if query has 2+ characters
    if (normalizedQuery.length >= 2) {
      const sensesForCollocations = await vocabulary.searchSenses('', { limit: 500 })
      const phraseResults = new Map<string, GroupedResult>()
      
      for (const sense of sensesForCollocations) {
        const collocations = sense.connections?.collocations || []
        const senseId = sense.id || ''
        const lemma = extractLemma(senseId)
        
        for (const coll of collocations) {
          const phrase = coll.phrase?.toLowerCase() || ''
          const meaning = coll.meaning?.toLowerCase() || ''
          const meaningZh = coll.meaning_zh || ''
          
          if (phrase.includes(normalizedQuery) || meaning.includes(normalizedQuery) || meaningZh.includes(normalizedQuery)) {
            const status = userProgress[senseId] || 'raw'
            
            if (filter !== 'all' && status !== filter) continue
            if (phraseResults.has(phrase)) continue

            let score = 0
            if (phrase === normalizedQuery) score = 95
            else if (phrase.startsWith(normalizedQuery)) score = 85
            else if (phrase.includes(normalizedQuery)) score = 70
            else if (meaning.includes(normalizedQuery)) score = 50
            else score = 40

            phraseResults.set(phrase, {
              type: 'phrase',
              lemma: lemma,
              displayWord: sense.word !== lemma ? sense.word : undefined,
              phrase: coll.phrase,
              phrase_meaning: coll.meaning,
              primary: {
                sense_id: senseId,
                pos: sense.pos || undefined,
                cefr: coll.cefr || sense.cefr,
                definition_en: coll.meaning,
                definition_zh: coll.meaning_zh,
                connection_count: getConnectionCount(sense),
                xp_value: getXpValue(sense),
                status,
                score,
                word: sense.word,
              },
              otherSenses: [],
              totalXp: getXpValue(sense),
              bestCefr: coll.cefr || sense.cefr,
            })
          }
        }
      }
      
      groupedResults.push(...Array.from(phraseResults.values()))
    }

    return groupedResults
  }, [userProgress])

  // Debounced search
  useEffect(() => {
    if (!isOpen) return

    setIsSearching(true)
    const timer = setTimeout(async () => {
      const searchResults = await performSearch(query, statusFilter)
      
      // Sort results
      searchResults.sort((a, b) => {
        switch (sortBy) {
          case 'xp':
            return b.totalXp - a.totalXp
          case 'cefr':
            return cefrOrder.indexOf(a.bestCefr || 'C2') - cefrOrder.indexOf(b.bestCefr || 'C2')
          case 'connections':
            return b.primary.connection_count - a.primary.connection_count
          case 'relevance':
          default:
            return b.primary.score - a.primary.score
        }
      })

      setResults(searchResults.slice(0, 50))
      setSelectedIndex(0)
      setIsSearching(false)
    }, 200)

    return () => clearTimeout(timer)
  }, [query, statusFilter, sortBy, performSearch, isOpen])

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => Math.min(prev + 1, results.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => Math.max(prev - 1, 0))
          break
        case 'Enter':
          e.preventDefault()
          if (results[selectedIndex]) {
            onSelectWord?.(results[selectedIndex].primary.sense_id)
            onClose()
          }
          break
        case 'Escape':
          e.preventDefault()
          onClose()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, results, selectedIndex, onSelectWord, onClose])

  // Scroll selected item into view
  useEffect(() => {
    if (resultsContainerRef.current && results.length > 0) {
      const selectedElement = resultsContainerRef.current.querySelector(`[data-index="${selectedIndex}"]`)
      selectedElement?.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedIndex, results.length])

  // Stats for current filter
  const [filterStats, setFilterStats] = useState({ raw: 0, hollow: 0, solid: 0, total: 0 })

  useEffect(() => {
    let mounted = true

    async function loadStats() {
      const allSenseIds = await vocabulary.getAllSenseIds()
      
      let raw = 0, hollow = 0, solid = 0
      
      for (const senseId of allSenseIds) {
        const status = userProgress[senseId] || 'raw'
        if (status === 'raw') raw++
        else if (status === 'hollow') hollow++
        else solid++
      }

      if (mounted) {
        setFilterStats({ raw, hollow, solid, total: raw + hollow + solid })
      }
    }

    loadStats()

    return () => { mounted = false }
  }, [userProgress])

  // Use state to track if we're in browser (for portal)
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!isOpen || !mounted) return null

  const modalContent = (
    <div 
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[5vh] sm:pt-[10vh]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative w-full max-w-2xl mx-3 bg-slate-900 rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden">
        {/* Header */}
        <div className="px-4 sm:px-5 pt-4 pb-3">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⛏️</span>
              <h2 className="text-lg font-bold text-white tracking-tight">Prospect</h2>
            </div>
            <span className="text-xs text-slate-500 font-mono hidden sm:inline">詞彙探索</span>
            <div className="flex-1" />
            
            {/* Desktop keyboard hints */}
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500">
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">↑↓</kbd>
              <span>選擇</span>
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 ml-1">Enter</kbd>
              <span>確認</span>
            </div>
            
            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 -mr-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              aria-label="關閉"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Search Input */}
          <div className="relative">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜尋單字、片語、定義..."
              className="w-full pl-12 pr-4 py-3.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all text-lg"
            />
            {isSearching && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <div className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="px-4 sm:px-5 py-3 border-t border-slate-800 bg-slate-900/50 overflow-x-auto">
          <div className="flex items-center gap-3 min-w-max">
            {/* Status filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium whitespace-nowrap">進度：</span>
              <div className="flex gap-1">
                {[
                  { value: 'all', label: '全部', count: filterStats.total },
                  { value: 'raw', label: '未開始', count: filterStats.raw, color: 'slate' },
                  { value: 'hollow', label: '學習中', count: filterStats.hollow, color: 'red' },
                  { value: 'solid', label: '已掌握', count: filterStats.solid, color: 'amber' },
                ].map(({ value, label, count, color }) => (
                  <button
                    key={value}
                    onClick={() => setStatusFilter(value as StatusFilter)}
                    className={`px-2 py-1 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                      statusFilter === value
                        ? color === 'amber' ? 'bg-amber-600/40 text-amber-200 border border-amber-500/50'
                        : color === 'red' ? 'bg-red-600/40 text-red-200 border border-red-500/50'
                        : 'bg-cyan-600/40 text-cyan-200 border border-cyan-500/50'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-transparent'
                    }`}
                  >
                    {label}
                    <span className="ml-1 text-[10px] opacity-70">({count})</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="w-px h-6 bg-slate-700" />

            {/* Sort */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium whitespace-nowrap">排序：</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="px-2 py-1 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500/50"
              >
                <option value="relevance">相關性</option>
                <option value="xp">💎 XP 值</option>
                <option value="cefr">CEFR 等級</option>
                <option value="connections">🔗 連結數</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        <div 
          ref={resultsContainerRef}
          className="max-h-[55vh] overflow-y-auto"
        >
          {results.length === 0 ? (
            <div className="py-12 text-center px-4">
              {query ? (
                <>
                  <p className="text-slate-400 text-lg mb-2">沒有找到「{query}」</p>
                  <p className="text-slate-500 text-sm">試試其他關鍵字，或搜尋片語如 "in love"</p>
                </>
              ) : (
                <>
                  <div className="text-4xl mb-4">🔍</div>
                  <p className="text-slate-400 text-lg mb-2">搜尋單字或片語</p>
                  <p className="text-slate-500 text-sm">輸入英文單字、片語或中文定義</p>
                </>
              )}
            </div>
          ) : (
            <div className="p-3 space-y-3">
              {results.map((result, index) => {
                const isSelected = index === selectedIndex
                const isPhrase = result.type === 'phrase'
                const allSenses = [result.primary, ...result.otherSenses]

                return (
                  <div 
                    key={`${result.lemma}-${result.phrase || index}`} 
                    data-index={index}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`rounded-xl border overflow-hidden transition-all ${
                      isSelected 
                        ? 'border-cyan-500/50 bg-cyan-950/30' 
                        : 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600'
                    }`}
                  >
                    {/* Word Header - Show LEMMA as main heading */}
                    <div className="px-4 py-2.5 bg-slate-800/50 border-b border-slate-700/50">
                      <div className="flex items-center gap-2 flex-wrap">
                        {isPhrase ? (
                          <>
                            <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">📝 片語</span>
                            <span className="text-lg font-bold text-white">"{result.phrase}"</span>
                            <span className="text-xs text-slate-500">from {result.lemma}</span>
                          </>
                        ) : (
                          <>
                            {/* Display LEMMA as the main word */}
                            <span className="text-xl font-bold text-white">{result.lemma}</span>
                            {/* Show word variant if different from lemma */}
                            {result.displayWord && result.displayWord.toLowerCase() !== result.lemma.toLowerCase() && (
                              <span className="text-sm text-slate-400 italic">({result.displayWord})</span>
                            )}
                            {allSenses.length > 1 && (
                              <span className="text-xs text-slate-400">({allSenses.length} 義)</span>
                            )}
                          </>
                        )}
                        <div className="flex-1" />
                        {/* Total XP for all senses */}
                        <span className="px-2 py-1 text-xs font-bold rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          💎 {result.totalXp} total
                        </span>
                      </div>
                    </div>

                    {/* All Senses */}
                    <div className="divide-y divide-slate-700/30">
                      {allSenses.map((sense, senseIdx) => {
                        const senseCefrStyle = cefrColors[sense.cefr || ''] || cefrColors['B1']
                        const senseStatusStyle = statusColors[sense.status]
                        const isQueued = miningQueue.some(q => q.senseId === sense.sense_id)
                        
                        return (
                          <div
                            key={sense.sense_id}
                            className="px-4 py-2.5 hover:bg-slate-700/30 transition-colors group"
                          >
                            <div className="flex items-start gap-2">
                              {/* Mine button */}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (isQueued) {
                                    removeFromQueue(sense.sense_id)
                                  } else {
                                    // addToQueue takes (senseId, word) - use lemma as display word
                                    addToQueue(sense.sense_id, result.lemma)
                                  }
                                }}
                                className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                                  isQueued
                                    ? 'bg-cyan-500 text-white'
                                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
                                }`}
                                title={isQueued ? '從佇列移除' : '加入挖礦佇列'}
                              >
                                {isQueued ? '✓' : '⛏️'}
                              </button>

                              {/* Main content - clickable to view details */}
                              <div 
                                className="flex-1 min-w-0 cursor-pointer"
                                onClick={() => {
                                  onSelectWord?.(sense.sense_id)
                                  onClose()
                                }}
                              >
                                {/* Word variant + badges */}
                                <div className="flex items-center gap-2 mb-1 flex-wrap">
                                  {/* Always show the word for clarity */}
                                  {sense.word && (
                                    <span className="text-base font-bold text-white mr-1">
                                      {sense.word}
                                    </span>
                                  )}
                                  {sense.pos && (
                                    <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-slate-700 text-slate-400">
                                      {posLabels[sense.pos.toLowerCase()] || sense.pos}
                                    </span>
                                  )}
                                  {sense.cefr && (
                                    <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded border ${senseCefrStyle}`}>
                                      {sense.cefr}
                                    </span>
                                  )}
                                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                    💎 {sense.xp_value}
                                  </span>
                                  <span className="flex items-center gap-1 text-[10px] text-slate-500">
                                    <span className="text-cyan-400">🔗</span>
                                    {sense.connection_count}
                                  </span>
                                  <span className={`px-1.5 py-0.5 text-[10px] rounded ${senseStatusStyle.bg} ${senseStatusStyle.text}`}>
                                    {senseStatusStyle.label}
                                  </span>
                                </div>
                                
                                {/* Definition */}
                                <p className="text-sm text-slate-300 line-clamp-2">
                                  {sense.definition_en || sense.definition_zh}
                                </p>
                              </div>
                              
                              {/* Arrow */}
                              <div 
                                className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 cursor-pointer self-center"
                                onClick={() => {
                                  onSelectWord?.(sense.sense_id)
                                  onClose()
                                }}
                              >
                                →
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 sm:px-5 py-3 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {results.length > 0 ? (
              <>
                找到 <span className="text-cyan-400 font-medium">{results.length}</span> 個結果
                {results.some(r => r.type === 'phrase') && (
                  <span className="text-slate-600 ml-1">（含片語）</span>
                )}
              </>
            ) : (
              '輸入關鍵字開始搜尋'
            )}
          </span>
          <div className="flex items-center gap-3">
            {miningQueueCount > 0 && (
              <span className="text-xs px-2 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-medium">
                ⛏️ {miningQueueCount} 待挖
              </span>
            )}
            <span className="text-xs text-slate-600 hidden sm:inline">
              ⌘K 開啟
            </span>
          </div>
        </div>
      </div>
    </div>
  )

  // Use portal to render outside game-container
  return createPortal(modalContent, document.body)
}

/**
 * Hook to handle global Cmd+K shortcut
 */
export function useSearchShortcut(onOpen: () => void) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        onOpen()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onOpen])
}

export default SearchModal
