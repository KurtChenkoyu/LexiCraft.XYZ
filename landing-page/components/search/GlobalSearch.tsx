'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { vocabulary } from '@/lib/vocabulary'
import { useRouter } from 'next/navigation'

interface SearchResult {
  id: string
  word: string
  pos?: string
  cefr?: string
  definition_en?: string
  definition_zh?: string
  frequency_rank?: number
}

export function GlobalSearch() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim().length < 2) {
        setResults([])
        setIsOpen(false)
        return
      }

      setIsSearching(true)
      try {
        const searchResults = await vocabulary.searchSenses(query, {
          limit: 8,
          sortBy: 'relevance'
        })

        setResults(searchResults.map(r => ({
          id: r.id || '',
          word: r.word,
          pos: r.pos || undefined,
          cefr: r.cefr,
          definition_en: r.definition_en || r.definition,
          definition_zh: r.definition_zh,
          frequency_rank: r.frequency_rank ?? undefined
        })))
        setIsOpen(true)
      } catch (error) {
        console.error('Search error:', error)
        setResults([])
      } finally {
        setIsSearching(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

  const handleSelectWord = useCallback((senseId: string) => {
    // Navigate to mine page with this word (could also add to grid directly)
    router.push(`/learner/mine?word=${senseId}`)
    setQuery('')
    setIsOpen(false)
  }, [router])

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
      
      if (e.key === 'Escape') {
        setIsOpen(false)
        inputRef.current?.blur()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className="relative w-full max-w-md">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {isSearching ? (
            <div className="animate-spin h-4 w-4 border-2 border-slate-400 border-t-transparent rounded-full" />
          ) : (
            <svg
              className="h-4 w-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          )}
        </div>
        
        <input
          ref={inputRef}
          type="text"
          placeholder="搜尋單字... (Ctrl+K)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          className="w-full bg-slate-800/50 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
        />

        {query && (
          <button
            onClick={() => {
              setQuery('')
              setIsOpen(false)
            }}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && results.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50 max-h-96 overflow-y-auto"
        >
          {results.map((result) => (
            <button
              key={result.id}
              onClick={() => handleSelectWord(result.id)}
              className="w-full text-left px-4 py-3 hover:bg-slate-800 border-b border-slate-800/50 last:border-0 transition-colors group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-slate-200">{result.word}</span>
                    {result.pos && (
                      <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
                        {result.pos}
                      </span>
                    )}
                    {result.cefr && (
                      <span className="text-xs text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                        {result.cefr}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 truncate">
                    {result.definition_en || result.definition_zh}
                  </div>
                </div>
                <div className="text-xs text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  查看 →
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results */}
      {isOpen && query.length >= 2 && !isSearching && results.length === 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-4 z-50"
        >
          <div className="text-center text-slate-400 text-sm">
            找不到「{query}」相關的單字
          </div>
        </div>
      )}
    </div>
  )
}

