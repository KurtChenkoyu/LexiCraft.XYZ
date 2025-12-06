'use client'

import React, { useState } from 'react'
import { QuestionPayload } from '../../services/surveyApi'

interface Props {
  question: QuestionPayload
  onSubmit: (selectedIds: string[]) => void
}

const MultiSelectMatrix: React.FC<Props> = ({ question, onSubmit }) => {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggleOption = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    setSelected(next)
  }

  const handleSubmit = () => {
    onSubmit(Array.from(selected))
  }

  return (
    <div className="w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* The Asset (Target Word) */}
      <div className="text-center mb-16">
        <h2 className="text-6xl md:text-7xl font-serif text-gray-100 tracking-tight mb-2">
          {question.word}
        </h2>
        <p className="text-gray-600 text-sm font-mono uppercase tracking-widest">
          Rank Class: {Math.floor(question.rank / 1000)}000
        </p>
      </div>

      {/* The Matrix (Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {question.options.map((opt) => {
          const isSelected = selected.has(opt.id)
          return (
            <button
              key={opt.id}
              onClick={() => toggleOption(opt.id)}
              className={`
                group relative flex items-center p-6 text-left rounded-lg border transition-all duration-200
                ${
                  isSelected
                    ? 'bg-gray-100 border-white text-gray-900 shadow-[0_0_20px_rgba(255,255,255,0.2)]'
                    : 'bg-gray-900/50 border-gray-800 text-gray-400 hover:border-gray-600 hover:text-gray-200'
                }
              `}
            >
              {/* Checkbox Visual */}
              <div
                className={`
                w-5 h-5 mr-4 border rounded-sm flex items-center justify-center transition-colors
                ${
                  isSelected
                    ? 'border-gray-900 bg-gray-900 text-white'
                    : 'border-gray-600 group-hover:border-gray-400'
                }
              `}
              >
                {isSelected && <div className="w-2.5 h-2.5 bg-current rounded-sm" />}
              </div>

              <span className="text-lg font-medium">{opt.text}</span>
            </button>
          )
        })}
      </div>

      {/* Action Bar */}
      <div className="flex justify-center">
        <button
          onClick={handleSubmit}
          className={`
            px-12 py-4 rounded-full font-bold tracking-widest text-sm uppercase transition-all duration-300
            ${
              selected.size > 0
                ? 'bg-cyan-600 text-white hover:bg-cyan-500 hover:shadow-[0_0_20px_rgba(8,145,178,0.6)] translate-y-0 opacity-100'
                : 'bg-gray-800 text-gray-600 cursor-not-allowed translate-y-2 opacity-50'
            }
          `}
          disabled={selected.size === 0}
        >
          Confirm Selection
        </button>
      </div>

      <p className="text-center mt-6 text-xs text-gray-600 font-mono">
        * Select all definitions that apply. Multiple valid assets may exist.
      </p>
    </div>
  )
}

export default MultiSelectMatrix
