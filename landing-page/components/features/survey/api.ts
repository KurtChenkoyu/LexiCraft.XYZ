/**
 * Survey API Client
 * 
 * Axios-based API client for LexiSurvey backend.
 * Provides type-safe methods for starting surveys and submitting answers.
 */

import axios from 'axios'
import {
  SurveyResult,
  AnswerSubmission,
  QuestionPayload,
  TriMetricReport,
} from './types'

// API Configuration
const API_BASE = process.env.NEXT_PUBLIC_API_URL 
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1/survey`
  : 'http://localhost:8000/api/v1/survey'

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
    cefrLevel: string = 'B1',
    userId?: string
  ): Promise<SurveyResult> => {
    const response = await axios.post<SurveyResult>(`${API_BASE}/start`, {
      cefr_level: cefrLevel,
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

