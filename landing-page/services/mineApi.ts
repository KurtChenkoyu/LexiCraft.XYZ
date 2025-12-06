/**
 * Mine API Service
 * 
 * Centralized API client for The Mine (vocabulary universe) exploration.
 */

import {
  MineExploreResponse,
  BlockDetail,
  StartForgingResponse,
} from '@/types/mine'
import { authenticatedGet, authenticatedPost } from '@/lib/api-client'

/**
 * Mine API Client
 * 
 * Provides methods to interact with The Mine backend API.
 */
export const mineApi = {
  /**
   * Explore The Mine - get blocks to discover
   * 
   * Returns starter pack for new users or personalized blocks for surveyed users.
   */
  explore: async (): Promise<MineExploreResponse> => {
    return authenticatedGet<MineExploreResponse>('/api/v1/mine/explore')
  },

  /**
   * Get full block detail with connections and user progress
   * 
   * @param senseId - Neo4j Sense.id (block identifier)
   */
  getBlock: async (senseId: string): Promise<BlockDetail> => {
    return authenticatedGet<BlockDetail>(`/api/v1/mine/blocks/${senseId}`)
  },

  /**
   * Start forging a block (begin learning process)
   * 
   * @param senseId - Neo4j Sense.id (block identifier)
   */
  startForging: async (senseId: string): Promise<StartForgingResponse> => {
    return authenticatedPost<StartForgingResponse>(
      `/api/v1/mine/blocks/${senseId}/start`
    )
  },
}

// Re-export types for convenience
export type {
  MineExploreResponse,
  BlockDetail,
  Block,
  BlockConnection,
  UserStats,
  StartForgingResponse,
} from '@/types/mine'

