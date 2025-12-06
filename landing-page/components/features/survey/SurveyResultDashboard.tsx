'use client'

import { useState } from 'react'
import { TriMetricReport, QuestionHistoryItem, Methodology } from './types'

interface SurveyResultDashboardProps {
  metrics: TriMetricReport
  detailedHistory?: QuestionHistoryItem[]
  methodology?: Methodology
  onExit: () => void
}

/**
 * SurveyResultDashboard: Final Results Display
 * 
 * Displays the Tri-Metric Report (Volume, Reach, Density)
 * in a terminal-style, high-tech format.
 */
export default function SurveyResultDashboard({
  metrics,
  detailedHistory,
  methodology,
  onExit,
}: SurveyResultDashboardProps) {
  const { volume, reach, density } = metrics
  const [showFullReport, setShowFullReport] = useState(false)

  // Calculate density percentage
  const densityPercent = Math.round(density * 100)

  // Format numbers with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-TW')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-cyan-500 font-mono">
      <div className="max-w-4xl mx-auto px-6 py-20">
        {/* Header */}
        <div className="mb-12 border-b border-gray-800 pb-4">
          <h1 className="text-2xl font-bold mb-2">SURVEY_COMPLETE</h1>
          <p className="text-gray-500 text-sm">ASSET_REPORT_GENERATED</p>
        </div>

        {/* Tri-Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Volume Card */}
          <div className="bg-gray-900 border border-cyan-500/30 rounded-lg p-6">
            <div className="text-cyan-400 text-xs mb-2">VOLUME_RESERVES</div>
            <div className="text-3xl font-bold text-cyan-500 mb-1">
              {formatNumber(volume)}
            </div>
            <div className="text-gray-500 text-xs">EST_WORDS_OWNED</div>
          </div>

          {/* Reach Card */}
          <div className="bg-gray-900 border border-cyan-500/30 rounded-lg p-6">
            <div className="text-cyan-400 text-xs mb-2">REACH_HORIZON</div>
            <div className="text-3xl font-bold text-cyan-500 mb-1">
              {formatNumber(reach)}
            </div>
            <div className="text-gray-500 text-xs">HIGHEST_RELIABLE_RANK</div>
          </div>

          {/* Density Card */}
          <div className="bg-gray-900 border border-cyan-500/30 rounded-lg p-6">
            <div className="text-cyan-400 text-xs mb-2">DENSITY_SOLIDITY</div>
            <div className="text-3xl font-bold text-cyan-500 mb-1">
              {densityPercent}%
            </div>
            <div className="text-gray-500 text-xs">CONSISTENCY_SCORE</div>
          </div>
        </div>

        {/* Summary Section */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 mb-8">
          <h2 className="text-lg font-bold mb-4 text-cyan-400">REPORT_SUMMARY</h2>
          <div className="space-y-3 text-gray-300 text-sm">
            <p>
              <span className="text-cyan-500">EST_RESERVES:</span> {formatNumber(volume)}{' '}
              words
            </p>
            <p>
              <span className="text-cyan-500">HORIZON:</span> Rank {formatNumber(reach)}
            </p>
            <p>
              <span className="text-cyan-500">SOLIDITY:</span> {densityPercent}% consistency
            </p>
          </div>
        </div>

        {/* Methodology Section */}
        {methodology && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 mb-8">
            <h2 className="text-lg font-bold mb-4 text-cyan-400">SURVEY_METHODOLOGY</h2>
            <div className="space-y-3 text-gray-300 text-sm">
              <p>
                <span className="text-cyan-500">Total Questions:</span> {methodology.total_questions}
              </p>
              <p>
                <span className="text-cyan-500">Algorithm:</span> {methodology.algorithm}
              </p>
              <p>
                <span className="text-cyan-500">Question Format:</span> {methodology.question_format}
              </p>
              <p>
                <span className="text-cyan-500">Scoring Method:</span> {methodology.scoring_method}
              </p>
              <p>
                <span className="text-cyan-500">Start Rank:</span> {methodology.start_rank}
              </p>
              {methodology.final_bounds && (
                <p>
                  <span className="text-cyan-500">Final Bounds:</span> Low: {methodology.final_bounds.low_bound}, High: {methodology.final_bounds.high_bound}, Range: {methodology.final_bounds.range}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Detailed History Section */}
        {detailedHistory && detailedHistory.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 mb-8">
            <h2 className="text-lg font-bold mb-4 text-cyan-400">DETAILED_HISTORY</h2>
            <div className="space-y-4 text-gray-300 text-sm">
              {detailedHistory.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg border border-gray-700">
                  <div className="flex-1 mr-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-cyan-500 font-bold">{index + 1}. {item.word || 'Unknown'}</span>
                      <span className="text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-400">Rank {item.rank}</span>
                      <span className="text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-400">Phase {item.phase}</span>
                    </div>
                    <div className="text-xs text-gray-400">
                      <span className="mr-3">Time: {item.time_taken.toFixed(1)}s</span>
                      <span>Options Selected: {item.selected_option_ids?.length || 0}</span>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {item.correct ? (
                      <span className="text-green-500 font-bold text-lg">✓ CORRECT</span>
                    ) : (
                      <span className="text-red-500 font-bold text-lg">✗ WRONG</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Full Detailed Report Section - Clickable/Expandable */}
        {detailedHistory && detailedHistory.length > 0 && (
          <div className="bg-gray-900 border-2 border-cyan-500/50 rounded-lg p-8 mb-8">
            <button
              onClick={() => setShowFullReport(!showFullReport)}
              className="w-full flex items-center justify-between text-left mb-4 hover:text-cyan-400 transition-colors group"
            >
              <h2 className="text-xl font-bold text-cyan-400 group-hover:text-cyan-300">
                📊 FULL_DETAILED_REPORT
              </h2>
              <span className="text-cyan-500 text-sm font-semibold bg-cyan-500/10 px-4 py-2 rounded border border-cyan-500/30 group-hover:bg-cyan-500/20">
                {showFullReport ? '▼ Hide' : '▶ Show'} Full Report
              </span>
            </button>

            {showFullReport && (
              <div className="space-y-6 mt-4">
                {detailedHistory.map((item, index) => {
                  // Get actual option texts from all_options
                  const selectedOptions = item.all_options?.filter(opt => 
                    item.selected_option_ids?.includes(opt.id)
                  ) || []
                  const correctOptions = item.all_options?.filter(opt => 
                    item.correct_option_ids?.includes(opt.id)
                  ) || []
                  
                  return (
                    <div key={index} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                      {/* Question Header */}
                      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                        <div>
                          <h3 className="text-cyan-400 font-bold text-lg">
                            Question {item.question_number || index + 1}: {item.word || 'Unknown'}
                          </h3>
                          <div className="flex gap-3 mt-1 text-xs text-gray-400">
                            <span>Rank: {item.rank}</span>
                            <span>Phase: {item.phase}</span>
                            <span>Time: {item.time_taken.toFixed(1)}s</span>
                          </div>
                        </div>
                        <div>
                          {item.correct ? (
                            <span className="text-green-500 font-bold">✓ CORRECT</span>
                          ) : (
                            <span className="text-red-500 font-bold">✗ INCORRECT</span>
                          )}
                        </div>
                      </div>
                      
                      {/* User's Selected Answers */}
                      <div className="mb-4">
                        <h4 className="text-cyan-500 text-sm font-semibold mb-2">
                          YOUR SELECTIONS:
                        </h4>
                        {selectedOptions.length > 0 ? (
                          <div className="space-y-2">
                            {selectedOptions.map((opt, optIdx) => (
                              <div 
                                key={optIdx}
                                className={`p-2 rounded text-sm ${
                                  opt.is_correct 
                                    ? 'bg-green-900/30 border border-green-700 text-green-300' 
                                    : 'bg-red-900/30 border border-red-700 text-red-300'
                                }`}
                              >
                                <span className="font-semibold">[{opt.type.toUpperCase()}]</span> {opt.text}
                                {opt.is_correct && <span className="ml-2 text-green-400">✓</span>}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm">No options selected</p>
                        )}
                      </div>
                      
                      {/* Correct Answers */}
                      <div>
                        <h4 className="text-cyan-500 text-sm font-semibold mb-2">
                          CORRECT ANSWERS:
                        </h4>
                        {correctOptions.length > 0 ? (
                          <div className="space-y-2">
                            {correctOptions.map((opt, optIdx) => {
                              const wasSelected = item.selected_option_ids?.includes(opt.id)
                              return (
                                <div 
                                  key={optIdx}
                                  className={`p-2 rounded text-sm ${
                                    wasSelected
                                      ? 'bg-green-900/30 border border-green-700 text-green-300'
                                      : 'bg-gray-700 border border-gray-600 text-gray-300'
                                  }`}
                                >
                                  <span className="font-semibold">[{opt.type.toUpperCase()}]</span> {opt.text}
                                  {wasSelected ? (
                                    <span className="ml-2 text-green-400">✓ Selected</span>
                                  ) : (
                                    <span className="ml-2 text-yellow-400">⚠ Not selected</span>
                                  )}
                                  {/* Show sense context for target options */}
                                  {opt.type === 'target' && (opt.sense_id || opt.example_zh || opt.example_en) && (
                                    <div className="mt-1 ml-4 text-xs text-gray-400">
                                      {opt.sense_id && (
                                        <div>Sense: <code className="text-cyan-400">{opt.sense_id}</code></div>
                                      )}
                                      {opt.is_primary_sense === false && (
                                        <div className="text-yellow-400">⚠ Secondary/Shared Sense</div>
                                      )}
                                      {opt.example_zh && (
                                        <div className="mt-1 italic">例: {opt.example_zh}</div>
                                      )}
                                      {opt.example_en && !opt.example_zh && (
                                        <div className="mt-1 italic">Example: {opt.example_en}</div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm">No correct options available</p>
                        )}
                      </div>
                      
                      {/* All Options (for reference) */}
                      {item.all_options && item.all_options.length > 0 && (
                        <details className="mt-4">
                          <summary className="text-gray-400 text-xs cursor-pointer hover:text-cyan-400">
                            View all options ({item.all_options.length})
                          </summary>
                          <div className="mt-2 space-y-1">
                            {item.all_options.map((opt, optIdx) => {
                              const wasSelected = item.selected_option_ids?.includes(opt.id)
                              const isCorrect = item.correct_option_ids?.includes(opt.id)
                              return (
                                <div 
                                  key={optIdx}
                                  className={`text-xs p-1 rounded ${
                                    wasSelected && isCorrect
                                      ? 'bg-green-900/20 text-green-400'
                                      : wasSelected && !isCorrect
                                      ? 'bg-red-900/20 text-red-400'
                                      : isCorrect && !wasSelected
                                      ? 'bg-yellow-900/20 text-yellow-400'
                                      : 'bg-gray-700/30 text-gray-500'
                                  }`}
                                >
                                  [{opt.type}] {opt.text}
                                  {wasSelected && <span className="ml-1">(Selected)</span>}
                                  {isCorrect && <span className="ml-1">(Correct)</span>}
                                  {/* Show sense context for all option types */}
                                  {(opt.sense_id || opt.definition_en || opt.example_zh || opt.example_en || opt.word_name) && (
                                    <div className="mt-1 ml-2 text-xs opacity-75 space-y-1">
                                      {opt.sense_id && (
                                        <div>
                                          <span className="text-cyan-400">Sense ID:</span>{' '}
                                          <code className="text-cyan-300 text-xs">{opt.sense_id}</code>
                                        </div>
                                      )}
                                      {opt.word_name && opt.type !== 'target' && (
                                        <div>
                                          <span className="text-cyan-400">From word:</span>{' '}
                                          <span className="text-cyan-300">{opt.word_name}</span>
                                        </div>
                                      )}
                                      {opt.definition_en && (
                                        <div className="italic text-gray-300">
                                          {opt.definition_en}
                                        </div>
                                      )}
                                      {opt.example_zh && (
                                        <div className="italic text-gray-300">
                                          <span className="text-cyan-400">例：</span>{opt.example_zh}
                                        </div>
                                      )}
                                      {opt.example_en && !opt.example_zh && (
                                        <div className="italic text-gray-300">
                                          <span className="text-cyan-400">Example:</span> {opt.example_en}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </details>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={onExit}
            className="px-6 py-3 border border-cyan-500 text-cyan-500 hover:bg-cyan-500/10 rounded transition-colors"
          >
            EXIT
          </button>
          <button
            onClick={() => window.print()}
            className="px-6 py-3 border border-gray-600 text-gray-400 hover:bg-gray-800 rounded transition-colors"
          >
            PRINT_REPORT
          </button>
        </div>
      </div>
    </div>
  )
}
