/**
 * MCQ API Service
 * 
 * Handles communication with the MCQ adaptive selection backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface MCQOption {
  text: string
  source: string
  pool_index?: number
}

export interface MCQData {
  mcq_id: string
  sense_id: string
  word: string
  mcq_type: string
  question: string
  context: string | null
  options: MCQOption[]
  correct_index?: number  // Present when loaded from cache (for instant feedback)
  user_ability: number
  mcq_difficulty: number | null
  selection_reason: string
}

// Gamification types for One-Shot Payload
export interface LevelUnlock {
  code: string
  type: string
  name_en: string
  name_zh?: string
  description_en?: string
  description_zh?: string
  icon?: string
  unlocked_at_level?: number
}

export interface LevelUpInfo {
  old_level: number
  new_level: number
  rewards?: string[]
  new_unlocks?: LevelUnlock[]
}

export interface AchievementUnlockedInfo {
  id: string
  code: string
  name_en: string
  name_zh?: string
  description_en?: string
  description_zh?: string
  icon?: string
  xp_reward: number
  crystal_reward?: number
  points_bonus: number
}

export interface GamificationResult {
  // Legacy XP fields
  xp_gained: number
  total_xp: number
  current_level: number
  xp_to_next_level: number
  xp_in_current_level: number
  progress_percentage: number
  
  // Three-Currency System
  sparks_gained: number
  sparks_total: number
  essence_gained: number
  essence_total: number
  energy_gained: number
  energy_total: number
  blocks_gained: number
  blocks_total: number
  
  // Other gamification
  points_earned: number
  streak_extended: boolean
  streak_days: number
  streak_multiplier?: number  // e.g., 2.0 for Day 7 payout
  level_up: LevelUpInfo | null
  achievements_unlocked: AchievementUnlockedInfo[]
  speed_warning?: string
  sync_status?: string  // 'processing' indicates background work
}

export interface VerificationResult {
  next_review_date: string
  next_interval_days: number
  was_correct: boolean
  retention_predicted: number | null
  mastery_level: string
  mastery_changed: boolean
  became_leech: boolean
  algorithm_type: string
}

export interface MCQResult {
  is_correct: boolean
  correct_index: number
  explanation: string
  feedback: string
  ability_before: number
  ability_after: number
  mcq_difficulty: number | null
  // Spaced repetition data (optional)
  verification_result?: VerificationResult
  // Gamification data for instant feedback (One-Shot Payload)
  gamification?: GamificationResult
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
    verificationScheduleId?: number,
    selectedPoolIndex?: number | null,
    servedOptionPoolIndices?: number[]
  ): Promise<MCQResult> {
    // Build request body, omitting undefined/null fields
    const requestBody: any = {
      mcq_id: mcqId,
      selected_index: selectedIndex,
      response_time_ms: responseTimeMs,
    }
    
    if (selectedPoolIndex !== undefined && selectedPoolIndex !== null) {
      requestBody.selected_option_pool_index = selectedPoolIndex
    }
    
    if (servedOptionPoolIndices !== undefined && servedOptionPoolIndices !== null) {
      requestBody.served_option_pool_indices = servedOptionPoolIndices
    }
    
    if (verificationScheduleId !== undefined && verificationScheduleId !== null) {
      requestBody.verification_schedule_id = verificationScheduleId
    }
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/submit`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(requestBody),
      }
    )

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      
      // For validation errors (422), log the full error details
      if (response.status === 422 && process.env.NODE_ENV === 'development') {
        console.error('❌ MCQ Submit Validation Error:', error)
        console.error('Request body was:', {
          mcq_id: mcqId,
          selected_index: selectedIndex,
          selected_option_pool_index: selectedPoolIndex ?? undefined,
          served_option_pool_indices: servedOptionPoolIndices,
          response_time_ms: responseTimeMs,
          verification_schedule_id: verificationScheduleId,
        })
      }
      
      // Format validation errors nicely
      if (error.detail && Array.isArray(error.detail)) {
        const messages = error.detail.map((err: any) => 
          `${err.loc?.join('.')} - ${err.msg}`
        ).join(', ')
        throw new Error(`Validation error: ${messages}`)
      }
      
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * Submit multiple MCQ answers in a single batch
   */
  async submitBatchAnswers(
    answers: Array<{
      mcqId: string
      selectedIndex: number
      responseTimeMs: number
      verificationScheduleId?: number
      selectedPoolIndex?: number | null
      servedOptionPoolIndices?: number[]
      // FAST PATH: Frontend provides these to skip DB fetch
      isCorrect?: boolean
      senseId?: string
      correctIndex?: number
    }>
  ): Promise<MCQResult[]> {
    // Build request body - wrap in 'answers' key to match SubmitBatchRequest model
    const answersArray = answers.map(answer => {
      const body: any = {
        mcq_id: answer.mcqId,
        selected_index: answer.selectedIndex,
        response_time_ms: answer.responseTimeMs,
      }
      
      if (answer.selectedPoolIndex !== undefined && answer.selectedPoolIndex !== null) {
        body.selected_option_pool_index = answer.selectedPoolIndex
      }
      
      if (answer.servedOptionPoolIndices !== undefined && answer.servedOptionPoolIndices !== null) {
        body.served_option_pool_indices = answer.servedOptionPoolIndices
      }
      
      if (answer.verificationScheduleId !== undefined && answer.verificationScheduleId !== null) {
        body.verification_schedule_id = answer.verificationScheduleId
      }
      
      // FAST PATH fields - skip DB fetch on backend
      if (answer.isCorrect !== undefined) {
        body.is_correct = answer.isCorrect
      }
      if (answer.senseId) {
        body.sense_id = answer.senseId
      }
      if (answer.correctIndex !== undefined) {
        body.correct_index = answer.correctIndex
      }
      
      return body
    })
    
    const requestBody = { answers: answersArray }
    
    console.log('📤 Batch submit request:', {
      url: `${this.baseUrl}/api/v1/mcq/submit-batch`,
      answerCount: answersArray.length,
      answers: answersArray.map(a => ({ mcqId: a.mcq_id, selectedIndex: a.selected_index })),
      headers: this.getHeaders(),
      bodyPreview: JSON.stringify(requestBody).substring(0, 200) + '...'
    })
    
    const startTime = Date.now()
    let response: Response
    try {
      response = await fetch(
        `${this.baseUrl}/api/v1/mcq/submit-batch`,
        {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(requestBody),
        }
      )
      
      const elapsed = Date.now() - startTime
      console.log(`⏱️ Batch submit response received after ${elapsed}ms, status: ${response.status}`)
      
      // Log response headers
      console.log('Response headers:', {
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length'),
      })
    } catch (error) {
      const elapsed = Date.now() - startTime
      console.error(`❌ Batch submit failed after ${elapsed}ms:`, error)
      throw error
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      
      if (response.status === 422 && process.env.NODE_ENV === 'development') {
        console.error('❌ MCQ Batch Submit Validation Error:', error)
      }
      
      if (error.detail && Array.isArray(error.detail)) {
        const messages = error.detail.map((err: any) => 
          `${err.loc?.join('.')} - ${err.msg}`
        ).join(', ')
        throw new Error(`Validation error: ${messages}`)
      }
      
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    console.log('⏳ Parsing response JSON...')
    const data = await response.json()
    console.log(`✅ Batch submit complete: ${data.length} results returned`)
    return data
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

  /**
   * Get achievements unlocked in the last N seconds.
   * Used to poll for achievements after MCQ submission.
   */
  async getRecentAchievements(seconds: number = 60): Promise<AchievementUnlockedInfo[]> {
    const params = new URLSearchParams({ seconds: seconds.toString() })
    const response = await fetch(
      `${this.baseUrl}/api/v1/mcq/achievements/recent?${params}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    )
    
    if (!response.ok) {
      return []
    }

    return response.json()
  }
}

// Export singleton instance
export const mcqApi = new MCQApiService()

