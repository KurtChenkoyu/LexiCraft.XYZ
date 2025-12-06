/**
 * Sync Service - Background synchronization with server
 * 
 * Handles queuing user actions locally and syncing them to the server
 * in the background. Provides offline-first behavior.
 */

import { localStore, UserAction, UserActionType } from '@/lib/local-store'
import { authenticatedPost } from '@/lib/api-client'

/**
 * Batch sync request payload
 */
interface BatchSyncRequest {
  actions: Array<{
    type: UserActionType
    sense_id: string
    payload?: Record<string, unknown>
    timestamp: number
  }>
}

/**
 * Batch sync response
 */
interface BatchSyncResponse {
  synced: number
  failed: number
  errors?: string[]
}

/**
 * Sync status
 */
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline'

/**
 * Sync event listener
 */
type SyncListener = (status: SyncStatus, pendingCount: number) => void

/**
 * Sync Service Class
 */
class SyncService {
  private status: SyncStatus = 'idle'
  private syncTimer: ReturnType<typeof setTimeout> | null = null
  private listeners: Set<SyncListener> = new Set()
  private syncInterval = 5000 // 5 seconds
  private retryInterval = 30000 // 30 seconds on error
  private isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true

  constructor() {
    // Listen for online/offline events
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.isOnline = true
        this.scheduleSync(1000) // Sync soon after coming online
      })
      window.addEventListener('offline', () => {
        this.isOnline = false
        this.setStatus('offline')
      })
    }
  }

  /**
   * Subscribe to sync status changes
   */
  subscribe(listener: SyncListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  /**
   * Get current sync status
   */
  getStatus(): SyncStatus {
    return this.status
  }

  /**
   * Set status and notify listeners
   */
  private async setStatus(status: SyncStatus): Promise<void> {
    this.status = status
    const pendingCount = (await localStore.getPendingActions()).length
    this.listeners.forEach(listener => listener(status, pendingCount))
  }

  /**
   * Queue an action for sync
   */
  async queueAction(
    type: UserActionType,
    senseId: string,
    payload?: Record<string, unknown>
  ): Promise<string> {
    const actionId = await localStore.queueAction({ type, senseId, payload })
    
    // Schedule sync
    this.scheduleSync()
    
    return actionId
  }

  /**
   * Schedule a sync operation
   */
  scheduleSync(delay: number = this.syncInterval): void {
    // Clear existing timer
    if (this.syncTimer) {
      clearTimeout(this.syncTimer)
    }

    // Don't schedule if offline
    if (!this.isOnline) {
      return
    }

    this.syncTimer = setTimeout(() => {
      this.sync()
    }, delay)
  }

  /**
   * Perform sync with server
   */
  async sync(): Promise<boolean> {
    // Skip if offline
    if (!this.isOnline) {
      await this.setStatus('offline')
      return false
    }

    // Skip if already syncing
    if (this.status === 'syncing') {
      return false
    }

    // Get pending actions
    const pending = await localStore.getPendingActions()
    
    if (pending.length === 0) {
      await this.setStatus('idle')
      return true
    }

    await this.setStatus('syncing')

    try {
      // Batch sync request
      const request: BatchSyncRequest = {
        actions: pending.map(action => ({
          type: action.type,
          sense_id: action.senseId,
          payload: action.payload,
          timestamp: action.timestamp,
        })),
      }

      const response = await authenticatedPost<BatchSyncResponse>(
        '/api/v1/sync',
        request
      )

      if (response.synced > 0) {
        // Mark successfully synced actions
        const syncedIds = pending.slice(0, response.synced).map(a => a.id)
        await localStore.markSynced(syncedIds)
        
        // Clean up synced actions
        await localStore.clearSyncedActions()
      }

      if (response.failed > 0) {
        console.warn('Some actions failed to sync:', response.errors)
      }

      await this.setStatus('idle')
      
      // Schedule next sync if there are more pending
      const remaining = await localStore.getPendingActions()
      if (remaining.length > 0) {
        this.scheduleSync()
      }

      return true
    } catch (error) {
      console.error('Sync failed:', error)
      await this.setStatus('error')
      
      // Retry after longer interval
      this.scheduleSync(this.retryInterval)
      
      return false
    }
  }

  /**
   * Force immediate sync
   */
  async forceSync(): Promise<boolean> {
    // Clear pending timer
    if (this.syncTimer) {
      clearTimeout(this.syncTimer)
      this.syncTimer = null
    }

    return this.sync()
  }

  /**
   * Get pending action count
   */
  async getPendingCount(): Promise<number> {
    const pending = await localStore.getPendingActions()
    return pending.length
  }
}

// Export singleton instance
export const syncService = new SyncService()

// Export types
export type { SyncListener, BatchSyncRequest, BatchSyncResponse }

