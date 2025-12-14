'use client'

import { useState, useEffect } from 'react'
import { vocabulary, type VocabularySense } from '@/lib/vocabulary'
import { BlockDetail } from '@/types/mine'
import { Spinner } from '@/components/ui'
import { WordValueBadge } from '@/components/features/vocabulary'


interface MiningDetailPanelProps {
  senseId: string
  isSelected: boolean
  onClose: () => void
  onToggleSelect: () => void
  onDrillDown: () => void
  onNavigateToSense?: (senseId: string) => void
}

/**
 * MiningDetailPanel - Renders word detail CONTENT inside a Sheet
 * 
 * NOTE: This component is designed to be used inside a Radix Sheet.
 * It does NOT handle modal/overlay rendering - that's the Sheet's job.
 */
export function MiningDetailPanel({
  senseId,
  isSelected,
  onClose,
  onToggleSelect,
  onDrillDown,
  onNavigateToSense
}: MiningDetailPanelProps) {
  const [detail, setDetail] = useState<BlockDetail | null>(null)
  const [sense, setSense] = useState<VocabularySense | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [navigatingChip, setNavigatingChip] = useState<string | null>(null)
  
  /**
   * Smart navigation handler for connection chips WITHOUT sense_id
   * Shows loading state while looking up the word
   */
  const handleChipClick = async (word: string, chipKey: string) => {
    if (!onNavigateToSense) return
    
    setNavigatingChip(chipKey)
    
    try {
      // Lookup by word
      let senses = await vocabulary.getSensesForWord(word)
      
      // If not found, try alternate forms
      if (!senses || senses.length === 0) {
        const baseWord = word.replace(/(ly|ing|ed|s|es)$/, '')
        if (baseWord !== word && baseWord.length > 2) {
          senses = await vocabulary.getSensesForWord(baseWord)
        }
      }
      
      if (senses && senses.length > 0) {
        onNavigateToSense(senses[0].id || '')
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to lookup word:', error)
      }
    } finally {
      setNavigatingChip(null)
    }
  }
  
  /**
   * Navigate to new sense - validates existence first to prevent broken navigation
   * If sense doesn't exist, tries to find the word in vocabulary
   */
  const navigateToSense = async (targetSenseId: string, displayWord?: string) => {
    // Validate the target exists before navigating
    const targetSense = await vocabulary.getSense(targetSenseId)
    if (targetSense) {
      onNavigateToSense?.(targetSenseId)
      return
    }
    
    // Target sense doesn't exist - try to find by word
    // Extract word from sense_id (e.g., "great.a.01" -> "great")
    const wordFromSenseId = targetSenseId.split('.')[0]
    const wordToSearch = displayWord || wordFromSenseId
    
    console.warn(`Sense ${targetSenseId} not found, searching for word "${wordToSearch}"`)
    
    // Try to find any sense for this word
    const wordSenses = await vocabulary.getSensesForWord(wordToSearch)
    if (wordSenses.length > 0) {
      // Found alternative senses - navigate to first one
      console.log(`Found ${wordSenses.length} alternative sense(s) for "${wordToSearch}"`)
      const firstSense = wordSenses[0] as { id?: string }
      if (firstSense.id) {
        onNavigateToSense?.(firstSense.id)
        return
      }
    }
    
    // Word not in curriculum at all - show message
    console.warn(`Word "${wordToSearch}" is not in the Taiwan MOE vocabulary`)
    // Could add a toast notification here in the future
  }

  useEffect(() => {
    let mounted = true
    
    async function loadDetail() {
      setIsLoading(true)
      setNotFound(false)
      
      const [detailData, senseData] = await Promise.all([
        vocabulary.getBlockDetail(senseId),
        vocabulary.getSense(senseId)
      ])
      
      if (mounted) {
        setDetail(detailData)
        setSense(senseData)
        setIsLoading(false)
        
        // If sense doesn't exist, mark as not found
        if (!senseData) {
          setNotFound(true)
        }
      }
    }
    
    loadDetail()
    
    return () => { mounted = false }
  }, [senseId])
  
  // Loading state
  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <Spinner size="lg" className="text-cyan-500 mb-4" />
        <p className="text-slate-400">Loading word details...</p>
      </div>
    )
  }
  
  // Not found state
  if (notFound || !detail || !sense) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center">
        <div className="text-4xl mb-4">🔍</div>
        <h3 className="text-xl font-bold text-white mb-2">Word Not Found</h3>
        <p className="text-slate-400 mb-4">
          This word isn't in our vocabulary yet.
        </p>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium transition-colors"
        >
          Go Back
        </button>
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col bg-slate-900 text-slate-100">
      {/* Header */}
      <div className="p-4 pt-12 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-2">
          {/* Show lemma (base form) as main title - no forced capitalization */}
          <h3 className="text-2xl font-bold text-white">
            {sense.lemma || detail.word}
          </h3>
          {/* Show word variant if different from lemma */}
          {sense.lemma && detail.word && sense.lemma.toLowerCase() !== detail.word.toLowerCase() && (
            <span className="text-lg text-slate-400 font-medium">
              ({detail.word})
            </span>
          )}
          {detail.pos && (
            <span className="text-xs text-slate-400 uppercase tracking-wide bg-slate-800 px-2 py-0.5 rounded">
              {detail.pos}
            </span>
          )}
        </div>
        
        {/* Value Badge - shows XP, connections, difficulty */}
        <WordValueBadge sense={sense} variant="full" />
      </div>
      
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Definition */}
        <div className="mb-4">
          <p className="text-slate-200 text-sm leading-relaxed">{detail.definition_en}</p>
        </div>

        {/* Chinese Definition */}
        {detail.definition_zh && (
          <div className="mb-4">
            <div className="text-xs text-slate-500 mb-1">中文定義</div>
            <p className="text-slate-300 text-sm leading-relaxed">{detail.definition_zh}</p>
          </div>
        )}

        {/* Example */}
        {detail.example_en && (
          <div className="mb-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
            <p className="text-slate-300 text-sm italic leading-relaxed">"{detail.example_en}"</p>
          </div>
        )}
        
        {/* Other Senses of the Same Word */}
        {detail.other_senses && detail.other_senses.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              Other Meanings ({detail.other_senses.length})
            </div>
            <div className="space-y-2">
              {detail.other_senses.map((otherSense) => (
                <button
                  key={otherSense.sense_id}
                  className="w-full text-left p-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg border border-slate-700/50 transition-colors"
                  onClick={() => onNavigateToSense?.(otherSense.sense_id)}
                >
                  <div className="text-xs text-slate-500 mb-0.5">{otherSense.pos}</div>
                  <div className="text-sm text-slate-300 line-clamp-2">{otherSense.definition_preview}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Synonyms */}
        {sense?.connections?.synonyms?.display_words && sense.connections.synonyms.display_words.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              🔗 SYNONYMS ({sense.connections.synonyms.display_words.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {sense.connections.synonyms.display_words.map((word, idx) => {
                const targetSenseId = sense.connections?.synonyms?.sense_ids?.[idx]
                const chipKey = `syn-${idx}`
                
                // Direct navigation when sense_id is known
                if (targetSenseId) {
                  return (
                    <button
                      key={chipKey}
                      onClick={() => navigateToSense(targetSenseId, word)}
                      className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm rounded-full border border-blue-500/30 hover:bg-blue-500/30 transition-colors"
                    >
                      {word}
                    </button>
                  )
                }
                
                // Fallback: button with loading state for lookup
                return (
                  <button 
                    key={chipKey}
                    onClick={() => handleChipClick(word, chipKey)}
                    disabled={navigatingChip === chipKey}
                    className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm rounded-full border border-blue-500/30 hover:bg-blue-500/30 transition-colors disabled:opacity-50"
                  >
                    {navigatingChip === chipKey ? '...' : word}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Antonyms */}
        {sense?.connections?.antonyms?.display_words && sense.connections.antonyms.display_words.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              ⚡ ANTONYMS ({sense.connections.antonyms.display_words.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {sense.connections.antonyms.display_words.map((word, idx) => {
                const targetSenseId = sense.connections?.antonyms?.sense_ids?.[idx]
                const chipKey = `ant-${idx}`
                
                if (targetSenseId) {
                  return (
                    <button
                      key={chipKey}
                      onClick={() => navigateToSense(targetSenseId, word)}
                      className="px-3 py-1 bg-red-500/20 text-red-300 text-sm rounded-full border border-red-500/30 hover:bg-red-500/30 transition-colors"
                    >
                      {word}
                    </button>
                  )
                }
                
                return (
                  <button 
                    key={chipKey}
                    onClick={() => handleChipClick(word, chipKey)}
                    disabled={navigatingChip === chipKey}
                    className="px-3 py-1 bg-red-500/20 text-red-300 text-sm rounded-full border border-red-500/30 hover:bg-red-500/30 transition-colors disabled:opacity-50"
                  >
                    {navigatingChip === chipKey ? '...' : word}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Similar Words */}
        {sense?.connections?.similar_words?.display_words && sense.connections.similar_words.display_words.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              🎯 SIMILAR ({sense.connections.similar_words.display_words.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {sense.connections.similar_words.display_words.map((word, idx) => {
                const targetSenseId = sense.connections?.similar_words?.sense_ids?.[idx]
                const chipKey = `similar-${idx}`
                
                if (targetSenseId) {
                  return (
                    <button
                      key={chipKey}
                      onClick={() => navigateToSense(targetSenseId, word)}
                      className="px-3 py-1 bg-purple-500/20 text-purple-300 text-sm rounded-full border border-purple-500/30 hover:bg-purple-500/30 transition-colors"
                    >
                      {word}
                    </button>
                  )
                }
                
                return (
                  <button 
                    key={chipKey}
                    onClick={() => handleChipClick(word, chipKey)}
                    disabled={navigatingChip === chipKey}
                    className="px-3 py-1 bg-purple-500/20 text-purple-300 text-sm rounded-full border border-purple-500/30 hover:bg-purple-500/30 transition-colors disabled:opacity-50"
                  >
                    {navigatingChip === chipKey ? '...' : word}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Word Family */}
        {sense?.connections?.word_family && Object.keys(sense.connections.word_family).length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              👨‍👩‍👧‍👦 WORD FAMILY
            </div>
            <div className="space-y-2">
              {Object.entries(sense.connections.word_family).map(([pos, words]) => (
                words && words.length > 0 && (
                  <div key={pos} className="flex items-start">
                    <span className="text-xs text-slate-400 mr-2 min-w-[60px] uppercase">{pos}:</span>
                    <div className="flex flex-wrap gap-2 flex-1">
                      {words.map((word, idx) => {
                        const chipKey = `wf-${pos}-${idx}`
                        return (
                          <button 
                            key={chipKey}
                            onClick={() => handleChipClick(word, chipKey)}
                            disabled={navigatingChip === chipKey}
                            className="px-2 py-0.5 bg-amber-500/20 text-amber-300 text-sm rounded hover:bg-amber-500/30 transition-colors disabled:opacity-50"
                          >
                            {navigatingChip === chipKey ? '...' : word}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Forms (Grammar) */}
        {sense?.connections?.forms && Object.keys(sense.connections.forms).length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              📝 FORMS
            </div>
            <div className="space-y-1">
              {Object.entries(sense.connections.forms).map(([form, words]) => (
                words && words.length > 0 && (
                  <div key={form} className="flex items-center">
                    <span className="text-xs text-slate-400 mr-2 min-w-[100px]">{form}:</span>
                    <span className="text-slate-300 text-sm">{words.join(', ')}</span>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Collocations */}
        {sense?.connections?.collocations && sense.connections.collocations.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
              💬 COLLOCATIONS ({sense.connections.collocations.length})
            </div>
            <div className="space-y-2">
              {sense.connections.collocations.map((coll, idx) => {
                if (typeof coll === 'string') {
                  return (
                    <span 
                      key={`coll-${idx}`} 
                      className="inline-block px-3 py-1 bg-indigo-500/20 text-indigo-300 text-sm rounded-full border border-indigo-500/30 mr-2"
                    >
                      {coll}
                    </span>
                  )
                }
                
                return (
                  <div key={`coll-${idx}`} className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="text-sm font-bold text-slate-200">{coll.phrase}</div>
                      {coll.cefr && (
                        <span className="px-2 py-0.5 text-xs font-bold rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                          {coll.cefr}
                        </span>
                      )}
                      {coll.register && (
                        <span className={`px-2 py-0.5 text-xs rounded ${
                          coll.register === 'formal' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' :
                          coll.register === 'informal' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                          'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                        }`}>
                          {coll.register}
                        </span>
                      )}
                    </div>
                    
                    <div className="text-xs text-slate-400 mb-2">{coll.meaning}</div>
                    <p className="text-slate-300 text-sm italic leading-relaxed mb-2">{coll.example}</p>
                    
                    {coll.example_en_explanation && (
                      <div className="mt-2 text-xs text-blue-300 bg-blue-500/10 border-l-2 border-blue-500 pl-2 py-1">
                        💡 {coll.example_en_explanation}
                      </div>
                    )}
                    
                    {coll.example_zh_explanation && (
                      <div className="mt-2 text-xs text-slate-500 border-t border-slate-700 pt-2">
                        🧠 {coll.example_zh_explanation}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
      
      {/* Actions Footer */}
      <div className="p-4 border-t border-slate-700 flex gap-2 pb-safe">
        <button
          onClick={onToggleSelect}
          className={`flex-1 py-3 rounded-lg font-bold transition-all ${
            isSelected 
              ? 'bg-cyan-600 text-white' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          {isSelected ? '✓ Selected' : 'Select'}
        </button>
        
        {detail.connection_count > 0 && (
          <button
            onClick={onDrillDown}
            className="flex-1 py-3 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-bold transition-colors"
          >
            🔍 Drill Down ({detail.connection_count})
          </button>
        )}
      </div>
    </div>
  )
}
