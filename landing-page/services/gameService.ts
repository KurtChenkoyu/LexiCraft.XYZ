/**
 * Game Service
 * 
 * Handles game actions like mining, building, etc.
 * Fire-and-forget API calls to persist optimistic updates.
 */

import { authenticatedPost } from '@/lib/api-client'

interface MineBatchRequest {
  sense_ids: string[]
  tier?: number
}

interface MineBatchResponse {
  success: boolean
  mined_count: number
  skipped_count: number
  new_wallet_balance: {
    total_earned: number
    available_points: number
    locked_points: number
    withdrawn_points: number
  }
  xp_gained: number
}

/**
 * Mine a batch of words (Phase 5b - Backend Persistence)
 * 
 * This is called AFTER the optimistic UI update.
 * If it fails, we show a toast but don't revert the UI (eventual consistency).
 * 
 * @param senseIds - Array of sense IDs to mine
 * @param tier - Rank level (default 1) - parameter name kept as tier for API compatibility
 * @returns Promise with mining result
 */
export async function mineBatch(
  senseIds: string[],
  tier: number = 1  // Parameter name kept as tier for API compatibility, but represents word rank
): Promise<MineBatchResponse> {
  try {
    const response = await authenticatedPost<MineBatchResponse>(
      '/api/v1/mine/batch',
      { sense_ids: senseIds, tier }
    )
    
    return response
  } catch (error) {
    console.error('Failed to persist mining batch:', error)
    throw error
  }
}

export const gameService = {
  mineBatch,
}

