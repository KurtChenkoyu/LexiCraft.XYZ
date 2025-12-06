/**
 * MCQ API Service
 * 
 * Handles communication with the MCQ adaptive selection backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface MCQOption {
  text: string
  source: string
}

export interface MCQData {
  mcq_id: string
  sense_id: string
  word: string
  mcq_type: string
  question: string
  context: string | null
  options: MCQOption[]
  user_ability: number
  mcq_difficulty: number | null
  selection_reason: string
}

export interface MCQResult {
  is_correct: boolean
  correct_index: number
  explanation: string
  feedback: string
  ability_before: number
  ability_after: number
  mcq_difficulty: number | null
}

export interface QualityReport {
  total_mcqs: number
  active_mcqs: number
  needs_review: number
  quality_distribution: Record<string, number>
  avg_quality_score: number | null
  total_attempts: number
}

export interface UserMCQStats {
  total_attempts: number
  correct_attempts: number
  accuracy: number
  senses_tested: number
  sense_abilities: Record<string, {
    ability: number
    confidence: number
    source: string
  }>
}

class MCQApiService {
  private baseUrl: string
  private authToken: string | null = null

  constructor() {
    this.baseUrl = API_URL
  }

  /**
   * Set the auth token for authenticated requests
   */
  setAuthToken(token: string | null) {
    this.authToken = token
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`
    }
    return headers
  }

  /**
   * Get a single MCQ for verification
   */
  async getMCQ(senseId: string, mcqType?: string): Promise<MCQData> {
    const params = new URLSearchParams({ sense_id: senseId })
    if (mcqType) params.append('mcq_type', mcqType)

    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/get?${params}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Get multiple MCQs for a verification session
   */
  async getMCQSession(senseId: string, count: number = 3): Promise<MCQData[]> {
    const params = new URLSearchParams({
      sense_id: senseId,
      count: count.toString(),
    })

    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/session?${params}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Submit an MCQ answer
   */
  async submitAnswer(
    mcqId: string,
    selectedIndex: number,
    responseTimeMs: number,
    verificationScheduleId?: number
  ): Promise<MCQResult> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/submit`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          mcq_id: mcqId,
          selected_index: selectedIndex,
          response_time_ms: responseTimeMs,
          verification_schedule_id: verificationScheduleId,
        }),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Get quality report (admin/analytics)
   */
  async getQualityReport(): Promise<QualityReport> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/quality`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Get user's MCQ statistics
   */
  async getUserStats(): Promise<UserMCQStats> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/stats/user`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Trigger quality recalculation (admin)
   */
  async recalculateQuality(): Promise<{ success: boolean; recalculated: number }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/recalculate`,
      {
        method: 'POST',
        headers: this.getHeaders(),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }
}

// Export singleton instance
export const mcqApi = new MCQApiService()

