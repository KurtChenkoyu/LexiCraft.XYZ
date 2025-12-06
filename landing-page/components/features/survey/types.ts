/**
 * Survey Types and Interfaces
 * 
 * Type definitions for LexiSurvey frontend components.
 * Matches backend API response models.
 */

export interface QuestionOption {
  id: string
  text: string
  type: 'target' | 'trap' | 'filler' | 'unknown'
  is_correct: boolean
  sense_id?: string
  definition_en?: string
  example_zh?: string
  example_en?: string
  is_primary_sense?: boolean
  word_name?: string  // For traps/fillers, show which word they came from
}

export interface QuestionPayload {
  question_id: string
  word: string
  rank: number
  options: QuestionOption[]
  time_limit: number
}

export interface TriMetricReport {
  volume: number
  reach: number
  density: number
}

export interface QuestionHistoryItem {
  rank: number
  correct: boolean
  time_taken: number
  word?: string
  question_id?: string
  phase?: number
  selected_option_ids?: string[]
  correct_option_ids?: string[]
  all_options?: QuestionOption[]
  question_number?: number
}

export interface Methodology {
  total_questions: number
  phases: Record<string, any>
  algorithm: string
  question_format: string
  scoring_method: string
  start_rank: number
  final_bounds: {
    low_bound: number
    high_bound: number
    range: number
  }
}

export interface SurveyResult {
  status: 'continue' | 'complete'
  session_id: string
  payload?: QuestionPayload
  metrics?: TriMetricReport
  detailed_history?: QuestionHistoryItem[]
  methodology?: Methodology
  debug_info?: {
    phase?: number
    confidence?: number
    question_count?: number
    [key: string]: any
  }
}

export interface AnswerSubmission {
  question_id: string
  selected_option_ids: string[]
  time_taken: number
}

export type SurveyState =
  | { type: 'loading' }
  | { type: 'error'; message: string }
  | { type: 'question'; data: QuestionPayload; sessionId: string; debugInfo?: { phase?: number; question_count?: number;[key: string]: any } }
  | { type: 'complete'; metrics: TriMetricReport; sessionId: string }
