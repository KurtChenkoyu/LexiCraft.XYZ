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
}

const DB_NAME = 'lexicraft'
const DB_VERSION = 1

/**
 * Get or create database instance
 */
let dbPromise: Promise<IDBPDatabase<LexiCraftDB>> | null = null

function getDB(): Promise<IDBPDatabase<LexiCraftDB>> {
  if (!dbPromise) {
    dbPromise = openDB<LexiCraftDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Progress store
        if (!db.objectStoreNames.contains('progress')) {
          const progressStore = db.createObjectStore('progress', { keyPath: 'senseId' })
          progressStore.createIndex('by-status', 'status')
        }

        // Sync queue store
        if (!db.objectStoreNames.contains('syncQueue')) {
          const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id' })
          syncStore.createIndex('by-synced', 'synced')
        }

        // Cache store
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' })
        }
      },
    })
  }
  return dbPromise
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
    const db = await getDB()
    await db.clear('progress')
    await db.clear('syncQueue')
    await db.clear('cache')
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
}

