/**
 * Survey API Service
 * 
 * Centralized API client for LexiSurvey backend.
 * Exports types and API methods.
 */

import axios from 'axios'
import {
  SurveyResult,
  AnswerSubmission,
  QuestionPayload,
  TriMetricReport,
  QuestionHistoryItem,
  Methodology,
} from '@/components/features/survey/types'

// API Configuration
// Ensure we always use an absolute URL
const getApiBase = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  if (apiUrl) {
    // Ensure it's a full URL (starts with http:// or https://)
    if (apiUrl.startsWith('http://') || apiUrl.startsWith('https://')) {
      return `${apiUrl}/api/v1/survey`
    }
    // If it doesn't start with http, assume https
    return `https://${apiUrl}/api/v1/survey`
  }
  // Default fallback - but this won't work in production!
  return 'http://localhost:8000/api/v1/survey'
}

const API_BASE = getApiBase()

// Log API base for debugging (only in development)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('Survey API Base URL:', API_BASE)
  console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL)
}

/**
 * Survey API Client
 * 
 * Provides methods to interact with the LexiSurvey backend API.
 */
export const surveyApi = {
  /**
   * Initialize a new survey session
   * 
   * @param cefrLevel - CEFR level for calibration (A1, A2, B1, B2, C1, C2)
   * @param userId - Optional user identifier
   * @returns SurveyResult with first question or error
   */
  start: async (
    cefrLevel?: string,
    userId?: string
  ): Promise<SurveyResult> => {
    const url = `${API_BASE}/start`
    console.log('Survey API Request:', { url, cefrLevel, userId })
    
    const response = await axios.post<SurveyResult>(url, {
      cefr_level: cefrLevel || undefined, // Pass undefined for default behavior (market median)
      user_id: userId,
    })
    return response.data
  },

  /**
   * Submit an answer and get the next question or completion
   * 
   * @param sessionId - Session identifier from start() response
   * @param submission - Answer submission data
   * @returns SurveyResult with next question or completion metrics
   */
  next: async (
    sessionId: string,
    submission: AnswerSubmission
  ): Promise<SurveyResult> => {
    const response = await axios.post<SurveyResult>(
      `${API_BASE}/next`,
      submission,
      {
        params: { session_id: sessionId }, // Pass session_id in query string as per API definition
      }
    )
    return response.data
  },
}

// Re-export types for convenience
export type {
  SurveyResult,
  QuestionPayload,
  TriMetricReport,
  AnswerSubmission,
  QuestionHistoryItem,
  Methodology
}

