'use client'

import React from 'react'

interface Props {
  phase: number      // 1, 2, or 3
  questionCount: number
  totalTarget: number // usually 15
}

const SurveyProgress: React.FC<Props> = ({ phase, questionCount, totalTarget }) => {
  
  // Visual width calculation
  const progressPct = Math.min((questionCount / totalTarget) * 100, 100)

  // Phase Labels - Aligned with "Geodetic Survey" metaphor
  const getPhaseLabel = (p: number) => {
    switch(p) {
      case 1: return "PHASE 1: COARSE SWEEP // 粗掃描"
      case 2: return "PHASE 2: FINE TUNING // 精細定位"
      case 3: return "PHASE 3: VERIFICATION // 最終驗證"
      default: return "CALIBRATING..."
    }
  }

  return (
    <div className="w-full mb-8">
      {/* Label Row */}
      <div className="flex justify-between items-end mb-2 text-xs font-mono">
        <span className={phase === 3 ? "text-emerald-400 animate-pulse" : "text-cyan-500"}>
          {getPhaseLabel(phase)}
        </span>
        <span className="text-gray-600">
          SEQ: {questionCount.toString().padStart(2, '0')} / {totalTarget}
        </span>
      </div>

      {/* The Bar Container */}
      <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden relative">
        {/* The Fill */}
        <div 
          className="h-full bg-gradient-to-r from-cyan-600 to-blue-500 transition-all duration-700 ease-out relative"
          style={{ width: `${progressPct}%` }}
        >
          {/* The "Survey Light" effect at the tip of the bar */}
          <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white opacity-30" />
        </div>
      </div>
    </div>
  )
}

export default SurveyProgress

