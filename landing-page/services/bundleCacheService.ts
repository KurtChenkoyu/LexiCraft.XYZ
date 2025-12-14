/**
 * Bundle Cache Service
 * 
 * Pre-caches verification bundles (MCQs) for the user's block inventory.
 * Enables instant MCQ loading without API calls during verification.
 * 
 * Usage:
 * - Call preCacheBundles() with sense IDs when inventory loads
 * - Bundles are fetched in background and stored in IndexedDB
 * - MCQSession reads from cache first, API fallback if miss
 */

import { localStore, VerificationBundleData } from '@/lib/local-store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const BATCH_SIZE = 50  // Max senses per API call

interface BundleApiResponse {
  [senseId: string]: {
    sense_id: string
    word: string
    mcqs: Array<{
      mcq_id: string
      question: string
      context: string | null
      options: Array<{ text: string; source: string }>
      correct_index: number
      mcq_type: string
    }>
  }
}

class BundleCacheService {
  private isCaching = false
  private cachePromise: Promise<void> | null = null

  /**
   * Pre-cache verification bundles for given sense IDs.
   * Skips already-cached senses. Runs in background.
   * 
   * @param senseIds - List of sense IDs to pre-cache
   * @param authToken - Auth token for API calls (optional for public senses)
   */
  async preCacheBundles(senseIds: string[], authToken?: string): Promise<void> {
    // Prevent concurrent caching
    if (this.isCaching) {
      return this.cachePromise || Promise.resolve()
    }

    if (senseIds.length === 0) return

    this.isCaching = true
    this.cachePromise = this._doCaching(senseIds, authToken)

    try {
      await this.cachePromise
    } catch (error) {
      // Silently fail - caching is optional enhancement
      if (process.env.NODE_ENV === 'development') {
        console.warn('Pre-caching failed (non-critical):', error)
      }
    } finally {
      this.isCaching = false
      this.cachePromise = null
    }
  }

  private async _doCaching(senseIds: string[], authToken?: string): Promise<void> {
    try {
      // 1. Filter out already-cached senses
      const uncached = await localStore.getMissingSenseIds(senseIds)
      
      if (uncached.length === 0) {
        console.log('📦 All bundles already cached')
        return
      }

      console.log(`📦 Pre-caching ${uncached.length} verification bundles...`)

      // 2. Batch fetch from API (chunks of BATCH_SIZE)
      let totalCached = 0
      for (let i = 0; i < uncached.length; i += BATCH_SIZE) {
        const batch = uncached.slice(i, i + BATCH_SIZE)
        
        try {
          const response = await fetch(`${API_URL}/api/v1/mcq/bundles`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(authToken && { Authorization: `Bearer ${authToken}` }),
            },
            body: JSON.stringify({ sense_ids: batch }),
          })

          if (response.ok) {
            const bundles: BundleApiResponse = await response.json()
            
            // 3. Store each bundle in IndexedDB
            const bundlesToSave: VerificationBundleData[] = []
            for (const [senseId, bundle] of Object.entries(bundles)) {
              bundlesToSave.push({
                senseId,
                word: bundle.word,
                mcqs: bundle.mcqs,
                cachedAt: Date.now(),
                version: 2,  // Set version for new bundles
              })
            }
            
            if (bundlesToSave.length > 0) {
              await localStore.saveVerificationBundles(bundlesToSave)
              totalCached += bundlesToSave.length
            }
          } else {
            if (process.env.NODE_ENV === 'development') {
              console.warn(`Bundle fetch failed for batch: ${response.status}`)
            }
          }
        } catch (error) {
          // Don't fail the whole operation for one batch
          if (process.env.NODE_ENV === 'development') {
            console.warn('Bundle batch fetch error:', error)
          }
        }
      }

      if (process.env.NODE_ENV === 'development') {
        console.log(`📦 Cached ${totalCached}/${uncached.length} verification bundles`)
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Bundle pre-caching failed:', error)
      }
    }
  }

  /**
   * Check if bundles are currently being cached
   */
  isCachingInProgress(): boolean {
    return this.isCaching
  }

  /**
   * Get stats about cached bundles
   */
  async getCacheStats(): Promise<{ total: number; oldestCachedAt: number | null }> {
    const bundles = await localStore.getAllVerificationBundles()
    const oldestCachedAt = bundles.length > 0 
      ? Math.min(...bundles.map(b => b.cachedAt))
      : null
    return { total: bundles.length, oldestCachedAt }
  }

  /**
   * Clear all cached bundles (for debugging or refresh)
   */
  async clearCache(): Promise<void> {
    const bundles = await localStore.getAllVerificationBundles()
    for (const bundle of bundles) {
      await localStore.deleteVerificationBundle(bundle.senseId)
    }
    console.log(`📦 Cleared ${bundles.length} cached bundles`)
  }
}

// Singleton instance
export const bundleCacheService = new BundleCacheService()

