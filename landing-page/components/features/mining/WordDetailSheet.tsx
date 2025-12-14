'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { vocabulary, type VocabularySense } from '@/lib/vocabulary'
import { wordLookup, type LookupResult } from '@/lib/wordLookup'
import { useAppStore, selectCanGoBack, selectMiningQueueCount } from '@/stores/useAppStore'
import { useIsMobile } from '@/hooks/useIsMobile'
import { BlockDetail } from '@/types/mine'
import { SensePickerModal } from './SensePickerModal'

// ============================================
// Types
// ============================================

interface WordDetailSheetProps {
  /** Initial sense ID to display */
  senseId: string
  /** Called when user wants to close the sheet */
  onClose: () => void
  /** Called when user selects (for grid selection) */
  onToggleSelect?: () => void
  /** Is currently selected in grid */
  isSelected?: boolean
  /** Called when user wants to drill down into connections */
  onDrillDown?: () => void
}

// ============================================
// Component
// ============================================

export function WordDetailSheet({
  senseId: initialSenseId,
  onClose,
  onToggleSelect,
  isSelected = false,
  onDrillDown
}: WordDetailSheetProps) {
  const isMobile = useIsMobile()
  
  // Local state
  const [currentSenseId, setCurrentSenseId] = useState(initialSenseId)
  const [detail, setDetail] = useState<BlockDetail | null>(null)
  const [sense, setSense] = useState<VocabularySense | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  
  // Sense picker state (for ambiguous words)
  const [pickerOpen, setPickerOpen] = useState(false)
  const [pickerWord, setPickerWord] = useState('')
  const [pickerSenses, setPickerSenses] = useState<VocabularySense[]>([])
  
  // Navigation history (local to this sheet instance)
  const [history, setHistory] = useState<Array<{ senseId: string; word: string }>>([])
  
  // Zustand store
  const addToQueue = useAppStore((s) => s.addToQueue)
  const removeFromQueue = useAppStore((s) => s.removeFromQueue)
  const isInQueue = useAppStore((s) => s.isInQueue)
  const queueCount = useAppStore(selectMiningQueueCount)
  const mineAllQueued = useAppStore((s) => s.mineAllQueued)
  
  // Check if current sense is in queue
  const inQueue = isInQueue(currentSenseId)
  
  // Can go back?
  const canGoBack = history.length > 0

  // ============================================
  // Data Loading
  // ============================================

  useEffect(() => {
    let mounted = true
    
    async function loadDetail() {
      setIsLoading(true)
      const [detailData, senseData] = await Promise.all([
        vocabulary.getBlockDetail(currentSenseId),
        vocabulary.getSense(currentSenseId)
      ])
      
      if (mounted) {
        setDetail(detailData)
        setSense(senseData)
        setIsLoading(false)
      }
    }
    
    loadDetail()
    
    return () => { mounted = false }
  }, [currentSenseId])

  // ============================================
  // Navigation Handlers
  // ============================================

  /**
   * Navigate to a word/sense
   * Handles:
   * - Direct sense_id navigation
   * - Word lookup with possible sense picker
   */
  const navigateTo = useCallback(async (word: string, preferredSenseId?: string) => {
    // Save current to history before navigating
    if (sense) {
      setHistory(prev => [...prev, { senseId: currentSenseId, word: sense.word }])
    }
    
    // Do lookup
    const result = await wordLookup.lookup(preferredSenseId || word)
    
    switch (result.type) {
      case 'exact_sense':
      case 'single_sense':
      case 'fuzzy_match':
        // Direct navigation
        if (result.senses[0]?.id) {
          setCurrentSenseId(result.senses[0].id)
        }
        break
        
      case 'multiple_senses':
        // Show picker
        setPickerWord(word)
        setPickerSenses(result.senses)
        setPickerOpen(true)
        // Don't update history yet - wait for picker selection
        setHistory(prev => prev.slice(0, -1)) // Undo the history push
        break
        
      case 'not_found':
        // Could show a toast/notification here
        setHistory(prev => prev.slice(0, -1)) // Undo the history push
        break
    }
  }, [currentSenseId, sense])

  /**
   * Go back in navigation history
   */
  const goBack = useCallback(() => {
    if (history.length === 0) return
    
    const previous = history[history.length - 1]
    setHistory(prev => prev.slice(0, -1))
    setCurrentSenseId(previous.senseId)
  }, [history])

  /**
   * Handle sense picker selection
   */
  const handlePickerSelect = useCallback((selectedSense: VocabularySense) => {
    setPickerOpen(false)
    if (selectedSense.id) {
      // Add to history
      if (sense) {
        setHistory(prev => [...prev, { senseId: currentSenseId, word: sense.word }])
      }
      setCurrentSenseId(selectedSense.id)
    }
    setPickerWord('')
    setPickerSenses([])
  }, [currentSenseId, sense])

  /**
   * Handle chip click
   */
  const handleChipClick = useCallback((word: string, targetSenseId?: string) => {
    navigateTo(word, targetSenseId)
  }, [navigateTo])

  /**
   * Toggle queue status
   */
  const handleQueueToggle = useCallback(() => {
    if (inQueue) {
      removeFromQueue(currentSenseId)
    } else if (sense) {
      addToQueue(currentSenseId, sense.word)
    }
  }, [inQueue, currentSenseId, sense, addToQueue, removeFromQueue])

  // ============================================
  // Render
  // ============================================

  if (isLoading || !detail || !sense) {
    return (
      <>
        <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
        <motion.div
          className={`fixed z-50 bg-slate-900 border ${
            isMobile 
              ? 'bottom-0 left-0 right-0 rounded-t-2xl max-h-[70vh] border-t border-slate-700'
              : 'top-0 right-0 bottom-0 w-96 border-l border-slate-700'
          }`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="p-8 flex items-center justify-center">
            <div className="animate-pulse text-slate-500">Loading...</div>
          </div>
        </motion.div>
      </>
    )
  }
  
  const mobileVariants = {
    hidden: { y: '100%' },
    visible: { y: 0 }
  }
  
  const desktopVariants = {
    hidden: { x: '100%' },
    visible: { x: 0 }
  }

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />
      
      {/* Panel */}
      <motion.div
        className={`fixed z-50 bg-slate-900 border ${
          isMobile 
            ? 'bottom-0 left-0 right-0 rounded-t-2xl max-h-[70vh] border-t border-slate-700'
            : 'top-0 right-0 bottom-0 w-96 border-l border-slate-700'
        }`}
        variants={isMobile ? mobileVariants : desktopVariants}
        initial="hidden"
        animate="visible"
        exit="hidden"
        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center justify-between mb-1">
            {/* Back Button + Word */}
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {canGoBack && (
                <button
                  onClick={goBack}
                  className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors text-lg shrink-0"
                >
                  ←
                </button>
              )}
              <h3 className="text-2xl font-bold text-white truncate">{sense.word}</h3>
              {sense.cefr && (
                <span className="px-2 py-0.5 text-xs font-bold rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 shrink-0">
                  {sense.cefr}
                </span>
              )}
            </div>
            
            {/* Close Button */}
            <button 
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors text-2xl shrink-0"
            >
              ×
            </button>
          </div>
          
          {/* POS + Navigation breadcrumb */}
          <div className="flex items-center gap-2">
            {detail.pos && (
              <span className="text-xs text-slate-400 uppercase tracking-wide">
                {detail.pos}
              </span>
            )}
            {history.length > 0 && (
              <span className="text-xs text-slate-500">
                • {history.length} deep
              </span>
            )}
          </div>
        </div>
        
        {/* Content */}
        <div className="p-4 overflow-y-auto" style={{ maxHeight: isMobile ? 'calc(70vh - 180px)' : 'calc(100vh - 180px)' }}>
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
          
          {/* Other Senses */}
          {detail.other_senses && detail.other_senses.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
                Other Meanings ({detail.other_senses.length})
              </div>
              <div className="space-y-2">
                {detail.other_senses.map((otherSense) => (
                  <button
                    key={otherSense.sense_id}
                    className="w-full text-left p-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg border border-slate-700/50 transition-colors hover:scale-[1.02] active:scale-[0.98]"
                    onClick={() => handleChipClick(otherSense.word, otherSense.sense_id)}
                  >
                    <div className="text-xs text-slate-500 mb-0.5">{otherSense.pos}</div>
                    <div className="text-sm text-slate-300 line-clamp-2">{otherSense.definition_preview}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Synonyms */}
          {sense.connections?.synonyms?.display_words && sense.connections.synonyms.display_words.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
                🔗 SYNONYMS ({sense.connections.synonyms.display_words.length})
              </div>
              <div className="flex flex-wrap gap-2">
                {sense.connections.synonyms.display_words.map((word, idx) => {
                  const targetSenseId = sense.connections?.synonyms?.sense_ids?.[idx]
                  return (
                    <button 
                      key={`syn-${idx}`} 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleChipClick(word, targetSenseId)
                      }}
                      className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm rounded-full border border-blue-500/30 cursor-pointer hover:bg-blue-500/30 transition-colors hover:scale-105 active:scale-95"
                    >
                      {word}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Antonyms */}
          {sense.connections?.antonyms?.display_words && sense.connections.antonyms.display_words.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
                ⚡ ANTONYMS ({sense.connections.antonyms.display_words.length})
              </div>
              <div className="flex flex-wrap gap-2">
                {sense.connections.antonyms.display_words.map((word, idx) => {
                  const targetSenseId = sense.connections?.antonyms?.sense_ids?.[idx]
                  return (
                    <button 
                      key={`ant-${idx}`} 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleChipClick(word, targetSenseId)
                      }}
                      className="px-3 py-1 bg-red-500/20 text-red-300 text-sm rounded-full border border-red-500/30 cursor-pointer hover:bg-red-500/30 transition-colors hover:scale-105 active:scale-95"
                    >
                      {word}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Similar Words */}
          {sense.connections?.similar_words?.display_words && sense.connections.similar_words.display_words.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-bold text-cyan-400 mb-2 uppercase tracking-wide">
                🎯 SIMILAR ({sense.connections.similar_words.display_words.length})
              </div>
              <div className="flex flex-wrap gap-2">
                {sense.connections.similar_words.display_words.map((word, idx) => {
                  const targetSenseId = sense.connections?.similar_words?.sense_ids?.[idx]
                  return (
                    <button 
                      key={`similar-${idx}`} 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleChipClick(word, targetSenseId)
                      }}
                      className="px-3 py-1 bg-purple-500/20 text-purple-300 text-sm rounded-full border border-purple-500/30 cursor-pointer hover:bg-purple-500/30 transition-colors hover:scale-105 active:scale-95"
                    >
                      {word}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Word Family */}
          {sense.connections?.word_family && Object.keys(sense.connections.word_family).length > 0 && (
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
                        {words.map((word, idx) => (
                          <button 
                            key={`wf-${pos}-${idx}`} 
                            onClick={() => handleChipClick(word)}
                            className="px-2 py-0.5 bg-amber-500/20 text-amber-300 text-sm rounded cursor-pointer hover:bg-amber-500/30 transition-colors hover:scale-105 active:scale-95"
                          >
                            {word}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Forms */}
          {sense.connections?.forms && Object.keys(sense.connections.forms).length > 0 && (
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
          {sense.connections?.collocations && sense.connections.collocations.length > 0 && (
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
        
        {/* Actions */}
        <div className="p-4 border-t border-slate-700">
          {/* Queue Status Banner */}
          {queueCount > 0 && (
            <div className="mb-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between">
              <span className="text-sm text-amber-400">
                📦 {queueCount} word{queueCount > 1 ? 's' : ''} in queue
              </span>
              <button
                onClick={() => mineAllQueued()}
                className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white text-sm rounded font-medium transition-colors"
              >
                Mine All
              </button>
            </div>
          )}
          
          <div className="flex gap-2">
            {/* Add to Queue Button */}
            <button
              onClick={handleQueueToggle}
              className={`flex-1 py-3 rounded-lg font-bold transition-all ${
                inQueue 
                  ? 'bg-amber-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {inQueue ? '📦 In Queue' : '+ Add to Queue'}
            </button>
            
            {/* Select Button (if grid mode) */}
            {onToggleSelect && (
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
            )}
            
            {/* Drill Down Button */}
            {onDrillDown && detail.connection_count > 0 && (
              <button
                onClick={onDrillDown}
                className="flex-1 py-3 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-bold transition-colors"
              >
                🔍 Drill ({detail.connection_count})
              </button>
            )}
          </div>
        </div>
      </motion.div>
      
      {/* Sense Picker Modal */}
      <SensePickerModal
        isOpen={pickerOpen}
        word={pickerWord}
        senses={pickerSenses}
        onSelect={handlePickerSelect}
        onClose={() => {
          setPickerOpen(false)
          setPickerWord('')
          setPickerSenses([])
        }}
      />
    </>
  )
}


