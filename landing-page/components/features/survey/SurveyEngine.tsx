'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { surveyApi, SurveyResult, QuestionPayload, TriMetricReport, QuestionHistoryItem, Methodology } from '@/services/surveyApi'
import MultiSelectMatrix from './MultiSelectMatrix'
import SurveyResultDashboard from './SurveyResultDashboard'
import SurveyProgress from './SurveyProgress'
import PreSurveyCalibration from './PreSurveyCalibration'

interface SurveyEngineProps {
  initialCefr?: string
  onExit: () => void
  userId?: string  // User ID from auth
}

const SurveyEngine: React.FC<SurveyEngineProps> = ({ initialCefr, onExit, userId }) => {
  // --- State Machine ---
  const [status, setStatus] = useState<'calibration' | 'init' | 'loading' | 'active' | 'complete' | 'error'>('calibration')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<QuestionPayload | null>(null)
  const [finalMetrics, setFinalMetrics] = useState<TriMetricReport | null>(null)
  
  // New reporting state
  const [detailedHistory, setDetailedHistory] = useState<QuestionHistoryItem[] | undefined>(undefined)
  const [methodology, setMethodology] = useState<Methodology | undefined>(undefined)
  
  // Calibration state
  const [selectedCefr, setSelectedCefr] = useState<string | undefined>(undefined)
  const [userAge, setUserAge] = useState<number | undefined>(undefined)
  const [calibrationComplete, setCalibrationComplete] = useState<boolean>(false)
  
  // Progress Tracking
  const [phase, setPhase] = useState<number>(1)
  const [questionCount, setQuestionCount] = useState<number>(0)
  const totalTarget = 15 // Maximum questions in survey

  // Timer State for Metadata
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now())
  
  // Error state for detailed error display
  const [lastError, setLastError] = useState<any>(null)

  // --- Actions ---

  // 2. Handle API Response Router
  const handleApiResult = useCallback((result: SurveyResult) => {
    if (result.session_id) setSessionId(result.session_id)

    // Extract phase and question count from debug_info
    if (result.debug_info) {
      if (result.debug_info.phase !== undefined) {
        setPhase(result.debug_info.phase)
      }
      if (result.debug_info.question_count !== undefined) {
        setQuestionCount(result.debug_info.question_count)
      }
    }

    if (result.status === 'complete' && result.metrics) {
      setFinalMetrics(result.metrics)
      // Extract detailed history and methodology
      if (result.detailed_history) {
        setDetailedHistory(result.detailed_history)
      }
      if (result.methodology) {
        setMethodology(result.methodology)
      }
      setStatus('complete')
    } else if (result.payload) {
      setCurrentQuestion(result.payload)
      setQuestionStartTime(Date.now())
      setStatus('active')
      // If debug_info doesn't have question_count, increment manually
      if (!result.debug_info?.question_count) {
        setQuestionCount(prev => prev + 1)
      }
    }
  }, [])

  // Handle calibration completion
  const handleCalibrationComplete = useCallback((cefrLevel: string | undefined, age?: number) => {
    console.log('Calibration complete:', { cefrLevel, age })
    setSelectedCefr(cefrLevel) // Can be undefined for SKIP option
    setUserAge(age)
    setCalibrationComplete(true)
    setStatus('init')
  }, [])

  // 1. Start Survey
  useEffect(() => {
    const initSurvey = async () => {
      if (!calibrationComplete) {
        return
      }

      try {
        console.log('Starting survey with CEFR:', selectedCefr || 'undefined (default)', 'User ID:', userId)
        setStatus('loading')
        const result = await surveyApi.start(selectedCefr, userId)
        console.log('Survey start result:', result)
        handleApiResult(result)
      } catch (err: any) {
        console.error('Survey Start Failed', err)
        // Store error details for display
        setLastError(err)
        // Log more details for debugging
        if (err.response) {
          console.error('API Error Response:', err.response.status, err.response.data)
        } else if (err.request) {
          console.error('API Request Failed - Backend not reachable. Check NEXT_PUBLIC_API_URL environment variable.')
        } else {
          console.error('Error:', err.message)
        }
        setStatus('error')
      }
    }

    if (status === 'init' && calibrationComplete) {
      initSurvey()
    }
  }, [selectedCefr, status, calibrationComplete, handleApiResult])

  // 3. Submit Answer
  const handleAnswerSubmit = useCallback(
    async (selectedIds: string[]) => {
      if (!sessionId || !currentQuestion) return

      // optimistic UI update or loading state here if desired
      // setStatus('loading'); // Optional: keeps UI responsive if backend is fast

      try {
        const timeTaken = (Date.now() - questionStartTime) / 1000

        const result = await surveyApi.next(sessionId, {
          question_id: currentQuestion.question_id,
          selected_option_ids: selectedIds,
          time_taken: timeTaken,
        })

        handleApiResult(result)
      } catch (err) {
        console.error('Submission Failed', err)
        setStatus('error')
      }
    },
    [sessionId, currentQuestion, questionStartTime, handleApiResult]
  )

  // --- Render Logic ---

  // Show calibration form first
  if (status === 'calibration') {
    return <PreSurveyCalibration onComplete={handleCalibrationComplete} />
  }

  if (status === 'loading' || status === 'init') {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950 text-cyan-500 font-mono animate-pulse">
        CALIBRATING_ASSET_SURVEY...
      </div>
    )
  }

  if (status === 'error') {
    // Get API URL from the service (it's computed there)
    const apiUrl = typeof window !== 'undefined' 
      ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
      : 'http://localhost:8000'
    
    // Extract error details
    let errorMessage = 'Unknown error'
    let errorStatus = null
    let errorData = null
    
    if (lastError) {
      if (lastError.response) {
        errorStatus = lastError.response.status
        errorData = lastError.response.data
        errorMessage = `HTTP ${errorStatus}: ${JSON.stringify(errorData)}`
      } else if (lastError.request) {
        errorMessage = 'Network Error: Backend not reachable. Check NEXT_PUBLIC_API_URL.'
      } else {
        errorMessage = lastError.message || String(lastError)
      }
    }
    
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-950 text-red-500 px-4 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold mb-4">SURVEY INITIALIZATION FAILED</h2>
        <p className="text-red-400 mb-4 text-center">
          There was an error starting the survey.
        </p>
        
        {/* Error Details Box */}
        <div className="bg-gray-900 border border-red-500/50 rounded p-4 mb-6 w-full text-left">
          <p className="text-red-300 font-mono text-xs mb-2">Error Details:</p>
          <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words overflow-auto max-h-40">
            {errorMessage}
          </pre>
          {errorStatus && (
            <p className="text-xs text-yellow-400 mt-2">Status Code: {errorStatus}</p>
          )}
        </div>
        
        <div className="text-sm text-gray-400 mb-6 text-center w-full space-y-1">
          <p>Selected CEFR Level: {selectedCefr || 'Not set'}</p>
          <p>Calibration Complete: {calibrationComplete ? 'Yes' : 'No'}</p>
          <p>User ID: {userId || 'Not set'}</p>
          <p className="text-yellow-400 mt-2">API URL: {apiUrl}</p>
          {apiUrl.includes('localhost') && (
            <p className="text-yellow-500 text-xs mt-1">
              ⚠️ Using localhost - This won't work in production. Set NEXT_PUBLIC_API_URL in Vercel.
            </p>
          )}
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={onExit}
            className="mt-4 px-4 py-2 border border-red-500 hover:bg-red-900/20 rounded"
          >
            ABORT
          </button>
          <button
            onClick={() => {
              setStatus('init')
              setCalibrationComplete(true)
              setLastError(null)
            }}
            className="mt-4 px-4 py-2 border border-cyan-500 hover:bg-cyan-900/20 rounded text-cyan-400"
          >
            RETRY
          </button>
        </div>
      </div>
    )
  }

  if (status === 'complete' && finalMetrics) {
    return (
      <SurveyResultDashboard 
        metrics={finalMetrics} 
        detailedHistory={detailedHistory}
        methodology={methodology}
        onExit={onExit} 
      />
    )
  }

  if (status === 'active' && currentQuestion) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center pt-20">
        <div className="w-full max-w-4xl px-6">
          {/* Survey Progress Bar */}
          <SurveyProgress 
            phase={phase}
            questionCount={questionCount}
            totalTarget={totalTarget}
          />

          {/* The Matrix Interaction */}
          <MultiSelectMatrix
            key={currentQuestion.question_id} // Force re-render on new question
            question={currentQuestion}
            onSubmit={handleAnswerSubmit}
          />
        </div>
      </div>
    )
  }

  return null
}

export default SurveyEngine
