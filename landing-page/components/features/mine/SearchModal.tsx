'use client'

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { vocabulary, VocabularySense } from '@/lib/vocabulary'

type StatusFilter = 'all' | 'raw' | 'hollow' | 'solid'
type SortBy = 'relevance' | 'cefr' | 'connections' | 'rank'

interface SearchResult {
  sense_id: string
  word: string
  pos?: string
  cefr?: string
  definition_en?: string
  definition_zh?: string
  connection_count: number
  frequency_rank?: number
  status: 'raw' | 'hollow' | 'solid'
  score: number // relevance score
}

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
  userProgress?: Record<string, 'raw' | 'hollow' | 'solid'>
  onSelectWord?: (senseId: string) => void
  onStartForging?: (senseId: string) => void
}

// CEFR level badge colors
const cefrColors: Record<string, { bg: string; text: string; border: string }> = {
  'A1': { bg: 'bg-emerald-500/20', text: 'text-emerald-300', border: 'border-emerald-500/40' },
  'A2': { bg: 'bg-green-500/20', text: 'text-green-300', border: 'border-green-500/40' },
  'B1': { bg: 'bg-amber-500/20', text: 'text-amber-300', border: 'border-amber-500/40' },
  'B2': { bg: 'bg-orange-500/20', text: 'text-orange-300', border: 'border-orange-500/40' },
  'C1': { bg: 'bg-rose-500/20', text: 'text-rose-300', border: 'border-rose-500/40' },
  'C2': { bg: 'bg-purple-500/20', text: 'text-purple-300', border: 'border-purple-500/40' },
}

// Status colors (matches the graph)
const statusColors = {
  solid: { bg: 'bg-amber-600/30', text: 'text-amber-300', label: '已掌握' },
  hollow: { bg: 'bg-red-600/30', text: 'text-red-300', label: '學習中' },
  raw: { bg: 'bg-slate-600/30', text: 'text-slate-400', label: '未開始' },
}

// POS display names
const posLabels: Record<string, string> = {
  'n': '名',
  'v': '動',
  'adj': '形',
  'adv': '副',
  'a': '形',
  's': '形',
  'r': '副',
  'noun': '名',
  'verb': '動',
  'prep': '介',
  'conj': '連',
  'pron': '代',
}

export function SearchModal({
  isOpen,
  onClose,
  userProgress = {},
  onSelectWord,
  onStartForging,
}: SearchModalProps) {
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortBy, setSortBy] = useState<SortBy>('relevance')
  const [results, setResults] = useState<SearchResult[]>([])
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

  // Search function
  const performSearch = useCallback((searchQuery: string, filter: StatusFilter) => {
    if (!vocabulary.isLoaded) return []

    const normalizedQuery = searchQuery.toLowerCase().trim()
    const searchResults: SearchResult[] = []
    const allSenses = vocabulary.getAllSenses()

    for (const [senseId, sense] of Object.entries(allSenses)) {
      const s = sense as VocabularySense
      const status = userProgress[senseId] || 'raw'
      
      // Apply status filter
      if (filter !== 'all' && status !== filter) continue

      // Calculate relevance score
      let score = 0
      const word = s.word?.toLowerCase() || ''
      const defEn = (s.definition_en || s.definition || '').toLowerCase()
      const defZh = s.definition_zh || ''

      // Exact word match = highest score
      if (word === normalizedQuery) {
        score = 100
      }
      // Word starts with query
      else if (word.startsWith(normalizedQuery)) {
        score = 80
      }
      // Word contains query
      else if (word.includes(normalizedQuery)) {
        score = 60
      }
      // Definition contains query (English)
      else if (defEn.includes(normalizedQuery)) {
        score = 40
      }
      // Definition contains query (Chinese)
      else if (defZh.includes(normalizedQuery)) {
        score = 30
      }

      if (score > 0 || normalizedQuery === '') {
        const connections = vocabulary.getConnections(senseId)
        searchResults.push({
          sense_id: senseId,
          word: s.word,
          pos: s.pos || undefined,
          cefr: s.cefr,
          definition_en: s.definition_en || s.definition,
          definition_zh: s.definition_zh,
          connection_count: connections.length,
          frequency_rank: s.frequency_rank || undefined,
          status,
          score: normalizedQuery === '' ? 50 : score, // Default score for browsing
        })
      }
    }

    return searchResults
  }, [userProgress])

  // Debounced search
  useEffect(() => {
    if (!isOpen) return

    setIsSearching(true)
    const timer = setTimeout(() => {
      const searchResults = performSearch(query, statusFilter)
      
      // Sort results
      searchResults.sort((a, b) => {
        switch (sortBy) {
          case 'relevance':
            return b.score - a.score
          case 'cefr':
            const cefrOrder = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
            const aIdx = cefrOrder.indexOf(a.cefr || 'C2')
            const bIdx = cefrOrder.indexOf(b.cefr || 'C2')
            return aIdx - bIdx
          case 'connections':
            return b.connection_count - a.connection_count
          case 'rank':
            return (a.frequency_rank || 99999) - (b.frequency_rank || 99999)
          default:
            return b.score - a.score
        }
      })

      // Limit results to 50 for performance
      setResults(searchResults.slice(0, 50))
      setSelectedIndex(0)
      setIsSearching(false)
    }, 150)

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
            onSelectWord?.(results[selectedIndex].sense_id)
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
  const filterStats = useMemo(() => {
    if (!vocabulary.isLoaded) return { raw: 0, hollow: 0, solid: 0, total: 0 }
    
    const allSenses = vocabulary.getAllSenses()
    let raw = 0, hollow = 0, solid = 0
    
    for (const senseId of Object.keys(allSenses)) {
      const status = userProgress[senseId] || 'raw'
      if (status === 'raw') raw++
      else if (status === 'hollow') hollow++
      else solid++
    }
    
    return { raw, hollow, solid, total: raw + hollow + solid }
  }, [userProgress])

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[10vh]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      
      {/* Modal */}
      <div className="relative w-full max-w-2xl mx-4 bg-slate-900 rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden animate-fade-in-up">
        {/* Header */}
        <div className="px-5 pt-5 pb-3">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⛏️</span>
              <h2 className="text-lg font-bold text-white tracking-tight">Prospect</h2>
            </div>
            <span className="text-xs text-slate-500 font-mono">詞彙探索</span>
            <div className="flex-1" />
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">↑↓</kbd>
              <span>選擇</span>
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 ml-1">Enter</kbd>
              <span>確認</span>
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 ml-1">Esc</kbd>
              <span>關閉</span>
            </div>
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
              placeholder="搜尋單字、定義..."
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
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-4">
            {/* Status filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">進度：</span>
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
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
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

            <div className="flex-1" />

            {/* Sort */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">排序：</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500/50"
              >
                <option value="relevance">相關性</option>
                <option value="cefr">CEFR 等級</option>
                <option value="connections">連結數</option>
                <option value="rank">詞頻</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        <div 
          ref={resultsContainerRef}
          className="max-h-[50vh] overflow-y-auto"
        >
          {results.length === 0 ? (
            <div className="py-12 text-center">
              {query ? (
                <>
                  <p className="text-slate-400 text-lg mb-2">沒有找到符合的結果</p>
                  <p className="text-slate-500 text-sm">試試其他關鍵字</p>
                </>
              ) : (
                <>
                  <p className="text-slate-400 text-lg mb-2">開始輸入來搜尋詞彙</p>
                  <p className="text-slate-500 text-sm">或使用上方篩選器瀏覽</p>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-800/50">
              {results.map((result, index) => {
                const cefrStyle = cefrColors[result.cefr || ''] || cefrColors['A1']
                const statusStyle = statusColors[result.status]
                const isSelected = index === selectedIndex

                return (
                  <div
                    key={result.sense_id}
                    data-index={index}
                    onClick={() => {
                      onSelectWord?.(result.sense_id)
                      onClose()
                    }}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`px-5 py-3.5 cursor-pointer transition-all group ${
                      isSelected ? 'bg-cyan-600/20 border-l-2 border-cyan-500' : 'hover:bg-slate-800/50 border-l-2 border-transparent'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Main content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {/* Word */}
                          <span className="text-lg font-semibold text-white">{result.word}</span>
                          
                          {/* POS badge */}
                          {result.pos && (
                            <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-slate-700 text-slate-400">
                              {posLabels[result.pos.toLowerCase()] || result.pos}
                            </span>
                          )}
                          
                          {/* CEFR badge */}
                          {result.cefr && (
                            <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded border ${cefrStyle.bg} ${cefrStyle.text} ${cefrStyle.border}`}>
                              {result.cefr}
                            </span>
                          )}
                          
                          {/* Status badge */}
                          <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${statusStyle.bg} ${statusStyle.text}`}>
                            {statusStyle.label}
                          </span>
                        </div>

                        {/* Definition */}
                        <p className="text-sm text-slate-400 line-clamp-1 mb-1.5">
                          {result.definition_en || result.definition_zh}
                        </p>

                        {/* Stats row */}
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <span className="text-cyan-500">🔗</span>
                            {result.connection_count} 連結
                          </span>
                          {result.frequency_rank && (
                            <span className="flex items-center gap-1">
                              <span className="text-amber-500">#</span>
                              詞頻 {result.frequency_rank}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Action button */}
                      <div className="flex-shrink-0 flex items-center gap-2">
                        {result.status === 'raw' && onStartForging && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onStartForging(result.sense_id)
                              // Update the result status locally for immediate feedback
                            }}
                            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                          >
                            🔥 鍛造
                          </button>
                        )}
                        <span className={`text-slate-600 ${isSelected ? 'opacity-100' : 'opacity-0'} group-hover:opacity-100 transition-opacity`}>
                          →
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {results.length > 0 ? `找到 ${results.length} 個結果` : '輸入關鍵字開始搜尋'}
          </span>
          <span className="text-xs text-slate-600 font-mono">
            ⌘K 開啟 · ESC 關閉
          </span>
        </div>
      </div>
    </div>
  )
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

