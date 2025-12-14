/**
 * Vocabulary Loader Web Worker
 * 
 * Runs in a separate thread to download and parse 80MB vocabulary.json
 * without blocking the main UI thread. Hydrates IndexedDB for instant queries.
 */

// Import Dexie from CDN (workers can't use npm packages directly)
importScripts('https://unpkg.com/dexie@3.2.7/dist/dexie.min.js')

const VOCABULARY_VERSION = '3.0-stage3'
const VERSION_KEY = 'vocabulary_version'
const CHUNK_SIZE = 1000 // Bulk insert in chunks to avoid memory issues

/**
 * Define Dexie database schema (must match main thread definition)
 */
class VocabularyDB extends Dexie {
  constructor() {
    super('LexiCraftVocab_V2')  // Renamed database to force fresh start
    // Version 1: Fresh start with metadata table for version tracking
    this.version(1).stores({
      senses: 'id, word, frequency_rank, cefr, tier, [word+pos]',
      metadata: 'key'
    })
  }
}

const db = new VocabularyDB()

/**
 * Message handler
 */
self.onmessage = async (event) => {
  const { action } = event.data

  if (action === 'check') {
    // Check if vocabulary is already loaded and up-to-date
    try {
      // Check version in metadata table
      const versionRecord = await db.metadata.get('version')
      const storedVersion = versionRecord ? versionRecord.value : null
      const count = await db.senses.count()
      
      if (storedVersion === VOCABULARY_VERSION && count > 10000) {
        self.postMessage({ status: 'cached', count })
        return
      }
      
      // Need to hydrate (either first time, empty, or version mismatch)
      self.postMessage({ status: 'needs_hydration' })
    } catch (error) {
      self.postMessage({ status: 'error', error: error.message })
    }
  }

  if (action === 'hydrate') {
    try {
      self.postMessage({ status: 'downloading', progress: 0 })

      // Fetch compressed vocabulary from public folder
      const response = await fetch('/vocabulary.json')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      self.postMessage({ status: 'parsing', progress: 25 })

      // Extract senses object
      const senses = data.senses
      if (!senses || typeof senses !== 'object') {
        throw new Error('Invalid vocabulary format: missing senses object')
      }

      // Convert { sense_id: { ...data } } to [{ id: sense_id, ...data }]
      const sensesArray = Object.entries(senses).map(([id, sense]) => ({
        id,
        ...sense
      }))

      self.postMessage({ 
        status: 'inserting', 
        progress: 50, 
        total: sensesArray.length 
      })

      // Clear old data (version upgrade)
      await db.senses.clear()
      await db.metadata.clear()

      // Bulk insert in chunks to prevent memory overflow
      for (let i = 0; i < sensesArray.length; i += CHUNK_SIZE) {
        const chunk = sensesArray.slice(i, i + CHUNK_SIZE)
        await db.senses.bulkPut(chunk)
        
        const progress = 50 + Math.floor((i / sensesArray.length) * 50)
        self.postMessage({ 
          status: 'inserting', 
          progress, 
          current: i + chunk.length, 
          total: sensesArray.length 
        })
      }

      // Store version in metadata table
      await db.metadata.put({ key: 'version', value: VOCABULARY_VERSION })
      
      self.postMessage({ status: 'complete', count: sensesArray.length })
    } catch (error) {
      self.postMessage({ 
        status: 'error', 
        error: error.message || 'Unknown error during hydration' 
      })
    }
  }
}

// Signal ready
self.postMessage({ status: 'worker_ready' })

