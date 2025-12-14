/**
 * Vocabulary Loader Manager
 * 
 * Manages vocabulary hydration. Worker handles download/parse.
 * Main thread handles ALL IndexedDB operations (single Dexie instance).
 */

export type LoaderStatus = 
  | { state: 'idle' }
  | { state: 'checking' }
  | { state: 'cached'; count: number }
  | { state: 'needs_hydration' }
  | { state: 'downloading'; progress: number }
  | { state: 'parsing'; progress: number }
  | { state: 'inserting'; progress: number; current: number; total: number }
  | { state: 'complete'; count: number }
  | { state: 'error'; error: string }

export type StatusCallback = (status: LoaderStatus) => void

export interface VocabularyReadyResult {
  success: true
  source: 'cache' | 'hydration'
  count: number
  version: string
}

class VocabularyLoader {
  private worker: Worker | null = null
  private callbacks: Set<StatusCallback> = new Set()
  private currentStatus: LoaderStatus = { state: 'idle' }
  private loadingStarted = false
  private readyPromise: Promise<VocabularyReadyResult> | null = null
  private readyResolve: ((result: VocabularyReadyResult) => void) | null = null
  private readyReject: ((error: Error) => void) | null = null

  startLoading() {
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 vocabularyLoader.startLoading() called')
    }
    
    if (this.loadingStarted) {
      if (process.env.NODE_ENV === 'development') {
        console.log('⚠️ Loading already started, skipping')
      }
      return
    }
    this.loadingStarted = true

    if (typeof Worker === 'undefined') {
      console.error('❌ Web Workers not supported')
      this.updateStatus({ state: 'error', error: 'Web Workers not supported' })
      this.readyReject?.(new Error('Web Workers not supported'))
      return
    }

    try {
      // Cache-busting via query param (increment when worker logic changes)
      const WORKER_VERSION = '20'  // v20: Comprehensive sense extraction (29K senses, 3K newly enriched)
      const workerUrl = `/workers/vocab-loader.js?v=${WORKER_VERSION}`
      if (process.env.NODE_ENV === 'development') {
        console.log('🔧 Creating worker:', workerUrl)
      }
      this.worker = new Worker(workerUrl)
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Worker created successfully')
      }
      
      this.worker.onmessage = async (event) => {
        const { status, progress, count, current, total, error, senses, version } = event.data
        if (process.env.NODE_ENV === 'development') {
          console.log('📬 Worker message received:', status, event.data)
        }

        switch (status) {
          case 'worker_ready':
            if (process.env.NODE_ENV === 'development') {
              console.log('✅ Worker ready')
            }
            break

          case 'check_main_thread':
            // Check IndexedDB using MAIN THREAD'S Dexie instance
            if (process.env.NODE_ENV === 'development') {
              console.log('🔍 Checking vocabulary cache (main thread)...')
            }
            try {
              const { isVocabularyReady, vocabularyDB } = await import('./vocabularyDB')
              const ready = await isVocabularyReady()
              
              if (ready) {
                const cachedCount = await vocabularyDB.senses.count()
                if (process.env.NODE_ENV === 'development') {
                  console.log(`✅ Vocabulary cached: ${cachedCount} senses`)
                }
                this.updateStatus({ state: 'cached', count: cachedCount })
                this.readyResolve?.({
                  success: true,
                  source: 'cache',
                  count: cachedCount,
                  version: '6.0-gemini-enriched'
                })
                this.terminate()
              } else {
                if (process.env.NODE_ENV === 'development') {
                  console.log('⚙️ Vocabulary not cached, starting hydration...')
                }
                this.updateStatus({ state: 'needs_hydration' })
                this.worker?.postMessage({ action: 'hydrate' })
              }
            } catch (checkError) {
              console.error('❌ Cache check failed:', checkError)
              this.worker?.postMessage({ action: 'hydrate' })
            }
            break

          case 'downloading':
            this.updateStatus({ state: 'downloading', progress })
            break

          case 'parsing':
            this.updateStatus({ state: 'parsing', progress })
            break

          case 'parsed':
            // MAIN THREAD writes to IndexedDB
            if (process.env.NODE_ENV === 'development') {
              console.log(`📥 Received ${count} senses from worker, writing to IndexedDB...`)
            }
            this.updateStatus({ state: 'inserting', progress: 0, current: 0, total: count })
            
            try {
              const { vocabularyDB, VOCABULARY_VERSION } = await import('./vocabularyDB')
              
              // Clear old data from IndexedDB
              await vocabularyDB.senses.clear()
              await vocabularyDB.metadata.clear()
              
              // IMPORTANT: Clear in-memory cache to prevent stale data
              const { vocabulary } = await import('./vocabulary')
              vocabulary.clearCache()
              
              // Bulk insert in chunks
              const CHUNK_SIZE = 1000
              for (let i = 0; i < senses.length; i += CHUNK_SIZE) {
                const chunk = senses.slice(i, i + CHUNK_SIZE)
                await vocabularyDB.senses.bulkPut(chunk)
                
                const insertProgress = Math.floor((i / senses.length) * 100)
                this.updateStatus({ 
                  state: 'inserting', 
                  progress: insertProgress,
                  current: Math.min(i + CHUNK_SIZE, senses.length),
                  total: senses.length
                })
              }
              
              // Set version metadata
              await vocabularyDB.metadata.put({ key: 'version', value: VOCABULARY_VERSION })
              
              if (process.env.NODE_ENV === 'development') {
                console.log(`✅ Vocabulary stored: ${senses.length} senses`)
              }
              this.updateStatus({ state: 'complete', count: senses.length })
              this.readyResolve?.({
                success: true,
                source: 'hydration',
                count: senses.length,
                version: VOCABULARY_VERSION
              })
              
            } catch (writeError) {
              console.error('❌ IndexedDB write failed:', writeError)
              this.updateStatus({ state: 'error', error: `Write failed: ${writeError}` })
              this.readyReject?.(new Error(`IndexedDB write failed: ${writeError}`))
            }
            this.terminate()
            break

          case 'error':
            console.error('❌ Worker error:', error)
            this.updateStatus({ state: 'error', error })
            this.readyReject?.(new Error(error))
            this.terminate()
            break
        }
      }

      this.worker.onerror = (error) => {
        console.error('❌ Worker crashed:', error)
        this.updateStatus({ state: 'error', error: error.message || 'Worker crashed' })
        this.readyReject?.(new Error(error.message || 'Worker crashed'))
        this.terminate()
      }

      if (process.env.NODE_ENV === 'development') {
        console.log('🔄 Setting status to checking...')
      }
      this.updateStatus({ state: 'checking' })
      if (process.env.NODE_ENV === 'development') {
        console.log('📤 Posting "check" message to worker...')
      }
      this.worker.postMessage({ action: 'check' })
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Message posted')
      }
      
    } catch (error) {
      console.error('❌ CRITICAL: Failed to start worker:', error)
      if (process.env.NODE_ENV === 'development') {
        console.error('Error details:', error)
      }
      this.updateStatus({ state: 'error', error: String(error) })
      this.readyReject?.(new Error(String(error)))
    }
  }

  onStatusChange(callback: StatusCallback): () => void {
    this.callbacks.add(callback)
    callback(this.currentStatus)
    return () => this.callbacks.delete(callback)
  }

  getCurrentStatus(): LoaderStatus {
    return this.currentStatus
  }

  isReady(): boolean {
    return this.currentStatus.state === 'cached' || this.currentStatus.state === 'complete'
  }

  async ensureReady(): Promise<VocabularyReadyResult> {
    // 1. FASTEST PATH: In-Memory Flag (0ms)
    // If we already checked this session, return immediately.
    if (this.currentStatus.state === 'cached' || this.currentStatus.state === 'complete') {
      const count = (this.currentStatus as any).count || 0
      return {
        success: true,
        source: 'cache',
        count,
        version: '6.0-gemini-enriched'
      }
    }

    // 2. FAST PATH: Direct DB Check (5-15ms)
    // 🛑 STOP! Don't start the worker yet. Check Dexie directly.
    try {
      const { isVocabularyReady, vocabularyDB, VOCABULARY_VERSION } = await import('./vocabularyDB')
      const ready = await isVocabularyReady()
      
      if (ready) {
        const count = await vocabularyDB.senses.count()
        
        if (process.env.NODE_ENV === 'development') {
          console.log(`⚡ Fast-boot: Vocabulary ready (${count} senses)`)
        }
        
        // Update state immediately without touching the worker
        this.updateStatus({ state: 'cached', count })
        
        return {
          success: true,
          source: 'cache',
          count,
          version: VOCABULARY_VERSION
        }
      }
    } catch (e) {
      if (process.env.NODE_ENV === 'development') {
        console.warn("Fast DB check failed, falling back to worker", e)
    }
    }

    // 3. SLOW PATH: Worker Hydration (~1000ms+)
    // We only reach here if the DB is actually empty or broken.
    
    if (this.readyPromise) return this.readyPromise
    
    this.readyPromise = new Promise((resolve, reject) => {
      this.readyResolve = resolve
      this.readyReject = reject
    })
    
    if (!this.loadingStarted) this.startLoading()
    
    return this.readyPromise
  }

  private updateStatus(status: LoaderStatus) {
    this.currentStatus = status
    this.callbacks.forEach(cb => {
      try { cb(status) } catch (e) { console.error('Callback error:', e) }
    })
  }

  private terminate() {
    if (this.worker) {
      this.worker.terminate()
      this.worker = null
    }
  }

  async forceReload() {
    this.terminate()
    this.loadingStarted = false
    this.readyPromise = null
    
    try {
      const { clearVocabularyCache } = await import('./vocabularyDB')
      await clearVocabularyCache()
      
      // Also clear in-memory cache in VocabularyStore
      const { vocabulary } = await import('./vocabulary')
      vocabulary.clearCache()
    } catch (e) {
      console.error('Failed to clear cache:', e)
    }
    
    this.startLoading()
  }
}

export const vocabularyLoader = new VocabularyLoader()
