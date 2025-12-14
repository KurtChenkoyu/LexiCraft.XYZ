'use client'

import { motion, AnimatePresence } from 'framer-motion'
import type { VocabularySense } from '@/lib/vocabulary'

interface SensePickerModalProps {
  isOpen: boolean
  word: string
  senses: VocabularySense[]
  onSelect: (sense: VocabularySense) => void
  onClose: () => void
}

/**
 * SensePickerModal - Shows when a word has multiple meanings
 * 
 * Allows user to pick which sense they want to view/navigate to.
 * Example: "bank" -> bank.n.01 (financial), bank.n.02 (river)
 */
export function SensePickerModal({
  isOpen,
  word,
  senses,
  onSelect,
  onClose
}: SensePickerModalProps) {
  if (!isOpen) return null

  // Group senses by POS
  const groupedByPos = senses.reduce((acc, sense) => {
    const pos = sense.pos || 'other'
    if (!acc[pos]) acc[pos] = []
    acc[pos].push(sense)
    return acc
  }, {} as Record<string, VocabularySense[]>)

  const posLabels: Record<string, string> = {
    n: 'noun',
    v: 'verb',
    a: 'adjective',
    r: 'adverb',
    s: 'adjective',
    other: 'other'
  }

  const posColors: Record<string, string> = {
    n: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    v: 'bg-green-500/20 text-green-400 border-green-500/30',
    a: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    r: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    s: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    other: 'bg-slate-500/20 text-slate-400 border-slate-500/30'
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/60 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          {/* Modal */}
          <motion.div
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[90vw] max-w-md max-h-[80vh] overflow-hidden bg-slate-900 rounded-2xl border border-slate-700 shadow-2xl"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white">
                  Which meaning of "{word}"?
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {senses.length} meanings found
                </p>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors text-xl"
              >
                ×
              </button>
            </div>
            
            {/* Sense List */}
            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <div className="space-y-3">
                {Object.entries(groupedByPos).map(([pos, posSenses]) => (
                  <div key={pos}>
                    {/* POS Header */}
                    <div className="text-xs font-bold text-slate-500 uppercase mb-2 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded border ${posColors[pos] || posColors.other}`}>
                        {posLabels[pos] || pos}
                      </span>
                      <span className="text-slate-600">({posSenses.length})</span>
                    </div>
                    
                    {/* Senses for this POS */}
                    <div className="space-y-2">
                      {posSenses.map((sense) => (
                        <button
                          key={sense.id}
                          onClick={() => onSelect(sense)}
                          className="w-full text-left p-3 bg-slate-800/50 hover:bg-slate-700/70 rounded-xl border border-slate-700/50 hover:border-slate-600 transition-all group active:scale-[0.98]"
                        >
                          {/* Definition */}
                          <p className="text-sm text-slate-200 leading-relaxed group-hover:text-white transition-colors">
                            {sense.definition_en || sense.definition || sense.definition_zh || '(No definition)'}
                          </p>
                          
                          {/* Chinese Definition */}
                          {sense.definition_zh && sense.definition_en && (
                            <p className="text-xs text-slate-400 mt-1">
                              {sense.definition_zh}
                            </p>
                          )}
                          
                          {/* Metadata */}
                          <div className="flex items-center gap-2 mt-2">
                            {/* CEFR Badge */}
                            {sense.cefr && (
                              <span className="px-2 py-0.5 text-xs font-bold rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                                {sense.cefr}
                              </span>
                            )}
                            
                            {/* Sense ID */}
                            <span className="text-xs text-slate-500 font-mono">
                              {sense.id}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Footer */}
            <div className="p-4 border-t border-slate-700">
              <button
                onClick={onClose}
                className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}


