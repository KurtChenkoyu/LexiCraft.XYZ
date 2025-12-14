/**
 * CACHING STRATEGY (IMMUTABLE - DO NOT CHANGE):
 * 
 * This file follows the "Last War" caching approach:
 * - IndexedDB is the ONLY cache for user data
 * - localStorage is FORBIDDEN for user data
 * - Load from IndexedDB first, sync from API in background
 * 
 * See: docs/ARCHITECTURE_PRINCIPLES.md
 * 
 * DO NOT add localStorage usage for user data here.
 */

/**
 * Local Store - IndexedDB-based persistent storage
 * 
 * Provides offline-capable storage for user progress and action queue.
 * Uses idb library for a promise-based IndexedDB API.
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb'

/**
 * User action types for sync queue
 */
export type UserActionType = 
  | 'START_FORGING'
  | 'COMPLETE_VERIFICATION'
  | 'UPDATE_PROGRESS'

/**
 * User action to be synced with server
 */
export interface UserAction {
  id: string
  type: UserActionType
  senseId: string
  payload?: Record<string, unknown>
  timestamp: number
  synced: boolean
}

/**
 * Block progress stored locally
 */
export interface LocalBlockProgress {
  senseId: string
  status: 'raw' | 'hollow' | 'solid'
  tier?: number
  startedAt?: string
  masteryLevel?: string
  updatedAt: number
}

/**
 * MCQ data for verification bundle (includes correct_index for instant feedback)
 */
export interface VerificationBundleMCQ {
  mcq_id: string
  question: string
  context: string | null
  options: Array<{ text: string; source: string }>
  correct_index: number
  mcq_type: string
}

/**
 * Pre-cached verification data for a sense
 * Enables instant MCQ loading without API calls
 */
export interface VerificationBundleData {
  senseId: string
  word: string
  mcqs: VerificationBundleMCQ[]
  cachedAt: number
  version?: number  // Add version field (defaults to 1 for old bundles)
}

/**
 * Database schema
 */
interface LexiCraftDB extends DBSchema {
  progress: {
    key: string
    value: LocalBlockProgress
    indexes: { 'by-status': string }
  }
  syncQueue: {
    key: string
    value: UserAction
    indexes: { 'by-synced': number }
  }
  cache: {
    key: string
    value: {
      key: string
      data: unknown
      expiresAt: number
    }
  }
  verificationBundles: {
    key: string  // sense_id
    value: VerificationBundleData
  }
}

const DB_NAME = 'lexicraft'
const DB_VERSION = 2  // Bumped for verificationBundles store

/**
 * Get or create database instance
 */
let dbPromise: Promise<IDBPDatabase<LexiCraftDB>> | null = null

function getDB(): Promise<IDBPDatabase<LexiCraftDB>> {
  if (!dbPromise) {
    dbPromise = openDB<LexiCraftDB>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion) {
        console.log(`Upgrading IndexedDB from v${oldVersion} to v${DB_VERSION}`)
        
        // Progress store (v1)
        if (!db.objectStoreNames.contains('progress')) {
          const progressStore = db.createObjectStore('progress', { keyPath: 'senseId' })
          progressStore.createIndex('by-status', 'status')
        }

        // Sync queue store (v1)
        if (!db.objectStoreNames.contains('syncQueue')) {
          const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id' })
          syncStore.createIndex('by-synced', 'synced')
        }

        // Cache store (v1)
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' })
        }

        // Verification bundles store (v2) - pre-cached MCQs for instant loading
        if (!db.objectStoreNames.contains('verificationBundles')) {
          db.createObjectStore('verificationBundles', { keyPath: 'senseId' })
          console.log('Created verificationBundles store')
        }
      },
      blocked() {
        // Called if there are older versions of the database open
        console.warn('IndexedDB upgrade blocked - please close other tabs')
      },
      blocking() {
        // Called if this connection is blocking a future version upgrade
        console.warn('This tab is blocking a database upgrade')
      },
    })
  }
  return dbPromise
}

/**
 * Check if verificationBundles store exists
 */
async function hasVerificationBundlesStore(): Promise<boolean> {
  try {
    const db = await getDB()
    return db.objectStoreNames.contains('verificationBundles')
  } catch {
    return false
  }
}

/**
 * Local Store API
 */
export const localStore = {
  /**
   * Save block progress locally
   */
  async saveProgress(senseId: string, status: 'raw' | 'hollow' | 'solid', extra?: Partial<LocalBlockProgress>): Promise<void> {
    const db = await getDB()
    await db.put('progress', {
      senseId,
      status,
      updatedAt: Date.now(),
      ...extra,
    })
  },

  /**
   * Get progress for a specific block
   */
  async getProgress(senseId: string): Promise<LocalBlockProgress | undefined> {
    const db = await getDB()
    return db.get('progress', senseId)
  },

  /**
   * Get all progress entries
   */
  async getAllProgress(): Promise<LocalBlockProgress[]> {
    const db = await getDB()
    return db.getAll('progress')
  },

  /**
   * Get progress by status
   */
  async getProgressByStatus(status: 'raw' | 'hollow' | 'solid'): Promise<LocalBlockProgress[]> {
    const db = await getDB()
    return db.getAllFromIndex('progress', 'by-status', status)
  },

  /**
   * Queue an action for server sync
   */
  async queueAction(action: Omit<UserAction, 'id' | 'timestamp' | 'synced'>): Promise<string> {
    const db = await getDB()
    const id = `${action.type}_${action.senseId}_${Date.now()}`
    await db.put('syncQueue', {
      ...action,
      id,
      timestamp: Date.now(),
      synced: false,
    })
    return id
  },

  /**
   * Get all pending (unsynced) actions
   */
  async getPendingActions(): Promise<UserAction[]> {
    const db = await getDB()
    const all = await db.getAll('syncQueue')
    return all.filter(a => !a.synced)
  },

  /**
   * Mark actions as synced
   */
  async markSynced(actionIds: string[]): Promise<void> {
    const db = await getDB()
    const tx = db.transaction('syncQueue', 'readwrite')
    
    for (const id of actionIds) {
      const action = await tx.store.get(id)
      if (action) {
        action.synced = true
        await tx.store.put(action)
      }
    }
    
    await tx.done
  },

  /**
   * Clear synced actions (cleanup)
   */
  async clearSyncedActions(): Promise<void> {
    const db = await getDB()
    const all = await db.getAll('syncQueue')
    const tx = db.transaction('syncQueue', 'readwrite')
    
    for (const action of all) {
      if (action.synced) {
        await tx.store.delete(action.id)
      }
    }
    
    await tx.done
  },

  /**
   * Cache data with expiration
   */
  async setCache<T>(key: string, data: T, ttlMs: number = 5 * 60 * 1000): Promise<void> {
    const db = await getDB()
    await db.put('cache', {
      key,
      data,
      expiresAt: Date.now() + ttlMs,
    })
  },

  /**
   * Get cached data (returns undefined if expired)
   */
  async getCache<T>(key: string): Promise<T | undefined> {
    const db = await getDB()
    const entry = await db.get('cache', key)
    
    if (!entry) return undefined
    if (entry.expiresAt < Date.now()) {
      // Expired, delete and return undefined
      await db.delete('cache', key)
      return undefined
    }
    
    return entry.data as T
  },

  /**
   * Set persistent data (no expiration)
   */
  async set<T>(key: string, data: T): Promise<void> {
    const db = await getDB()
    await db.put('cache', {
      key,
      data,
      expiresAt: Date.now() + 365 * 24 * 60 * 60 * 1000, // 1 year
    })
  },

  /**
   * Get persistent data
   */
  async get<T>(key: string): Promise<T | undefined> {
    const db = await getDB()
    const entry = await db.get('cache', key)
    if (!entry) return undefined
    return entry.data as T
  },

  /**
   * Clear all local data (for logout)
   */
  async clearAll(): Promise<void> {
    try {
      const db = await getDB()
      await db.clear('progress')
      await db.clear('syncQueue')
      await db.clear('cache')
      if (await hasVerificationBundlesStore()) {
        await db.clear('verificationBundles')
      }
    } catch (error) {
      console.warn('Failed to clear all data:', error)
    }
  },

  /**
   * Force database upgrade by deleting and recreating
   * Call this if you see "object store not found" errors
   */
  async resetDatabase(): Promise<void> {
    try {
      // Close existing connection
      if (dbPromise) {
        const db = await dbPromise
        db.close()
        dbPromise = null
      }
      
      // Delete the database
      await new Promise<void>((resolve, reject) => {
        const request = indexedDB.deleteDatabase(DB_NAME)
        request.onsuccess = () => resolve()
        request.onerror = () => reject(request.error)
      })
      
      console.log('Database reset complete - will recreate on next access')
      
      // Reopen to trigger fresh creation
      await getDB()
    } catch (error) {
      console.error('Failed to reset database:', error)
    }
  },

  /**
   * Import progress from server (merge with local)
   */
  async importProgress(serverProgress: Array<{ sense_id: string; status: string }>): Promise<void> {
    const db = await getDB()
    const tx = db.transaction('progress', 'readwrite')
    
    for (const item of serverProgress) {
      // Map server status to local status
      let status: 'raw' | 'hollow' | 'solid' = 'raw'
      if (item.status === 'verified' || item.status === 'mastered') {
        status = 'solid'
      } else if (item.status === 'learning' || item.status === 'pending') {
        status = 'hollow'
      }
      
      // Only update if not already locally modified
      const existing = await tx.store.get(item.sense_id)
      if (!existing || existing.updatedAt < Date.now() - 60000) {
        await tx.store.put({
          senseId: item.sense_id,
          status,
          updatedAt: Date.now(),
        })
      }
    }
    
    await tx.done
  },

  // ============================================
  // Verification Bundle Methods (Pre-Cache)
  // ============================================

  /**
   * Save a verification bundle for instant MCQ loading
   */
  async saveVerificationBundle(bundle: VerificationBundleData): Promise<void> {
    try {
      if (!await hasVerificationBundlesStore()) return
      const db = await getDB()
      await db.put('verificationBundles', bundle)
    } catch (error) {
      console.warn('Failed to save verification bundle:', error)
    }
  },

  /**
   * Save multiple verification bundles at once
   */
  async saveVerificationBundles(bundles: VerificationBundleData[]): Promise<void> {
    try {
      if (!await hasVerificationBundlesStore()) return
      const db = await getDB()
      const tx = db.transaction('verificationBundles', 'readwrite')
      for (const bundle of bundles) {
        await tx.store.put(bundle)
      }
      await tx.done
    } catch (error) {
      console.warn('Failed to save verification bundles:', error)
    }
  },

  /**
   * Get a verification bundle for a sense
   */
  async getVerificationBundle(senseId: string): Promise<VerificationBundleData | undefined> {
    try {
      if (!await hasVerificationBundlesStore()) return undefined
      const db = await getDB()
      const bundle = await db.get('verificationBundles', senseId)
      
      // Invalidate old bundles (version 1 or missing version)
      if (bundle && (!bundle.version || bundle.version < 2)) {
        console.log(`Invalidating old bundle for ${senseId} (version ${bundle.version || 1})`)
        await db.delete('verificationBundles', senseId)
        return undefined
      }
      
      return bundle
    } catch (error) {
      console.warn('Failed to get verification bundle:', error)
      return undefined
    }
  },

  /**
   * Get multiple verification bundles
   */
  async getVerificationBundles(senseIds: string[]): Promise<Map<string, VerificationBundleData>> {
    const result = new Map<string, VerificationBundleData>()
    try {
      if (!await hasVerificationBundlesStore()) return result
      const db = await getDB()
      for (const senseId of senseIds) {
        const bundle = await db.get('verificationBundles', senseId)
        if (bundle) {
          result.set(senseId, bundle)
        }
      }
    } catch (error) {
      console.warn('Failed to get verification bundles:', error)
    }
    return result
  },

  /**
   * Delete a verification bundle
   */
  async deleteVerificationBundle(senseId: string): Promise<void> {
    try {
      if (!await hasVerificationBundlesStore()) return
      const db = await getDB()
      await db.delete('verificationBundles', senseId)
    } catch (error) {
      console.warn('Failed to delete verification bundle:', error)
    }
  },

  /**
   * Get all cached verification bundles (for debugging/stats)
   */
  async getAllVerificationBundles(): Promise<VerificationBundleData[]> {
    try {
      if (!await hasVerificationBundlesStore()) return []
      const db = await getDB()
      return db.getAll('verificationBundles')
    } catch (error) {
      console.warn('Failed to get all verification bundles:', error)
      return []
    }
  },

  /**
   * Check which senses are missing bundles
   */
  async getMissingSenseIds(senseIds: string[]): Promise<string[]> {
    try {
      if (!await hasVerificationBundlesStore()) return senseIds // All missing if store doesn't exist
      const db = await getDB()
      const missing: string[] = []
      for (const senseId of senseIds) {
        const bundle = await db.get('verificationBundles', senseId)
        if (!bundle) {
          missing.push(senseId)
        }
      }
      return missing
    } catch (error) {
      console.warn('Failed to check missing sense IDs:', error)
      return senseIds // Assume all missing on error
    }
  },
}

