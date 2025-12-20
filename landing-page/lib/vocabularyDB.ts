/**
 * Vocabulary Database - IndexedDB wrapper using Dexie.js
 * 
 * Provides indexed storage for 80MB vocabulary data with instant queries.
 * No main-thread blocking, async access only.
 */

import Dexie, { Table } from 'dexie'

// Import types from existing vocabulary.ts
import type { VocabularySense } from './vocabulary'

/**
 * Vocabulary sense with guaranteed ID field for indexing
 */
export interface VocabularySenseIndexed extends VocabularySense {
  id: string // Primary key (sense_id like "formal.a.01")
}

/**
 * Metadata record for version tracking
 */
export interface MetadataRecord {
  key: string
  value: string
}

/**
 * Vocabulary Database Schema
 * 
 * Indexes:
 * - id: Primary key for O(1) lookup by sense_id
 * - word: For word search and lemma lookups
 * - frequency_rank: For band-based queries and sorting
 * - cefr: For level-based filtering
 */
export class VocabularyDatabase extends Dexie {
  senses!: Table<VocabularySenseIndexed, string>
  metadata!: Table<MetadataRecord, string>

  constructor() {
    super('LexiCraftVocab_V4_Gemini')  // V4: Gemini-enriched schema with collocations
    
    // Version 1: Fresh start with metadata table for version tracking
    this.version(1).stores({
      senses: 'id, word, frequency_rank, cefr, rank, [word+pos]',  // Changed from tier to rank
      metadata: 'key'
    })
  }
}

// Singleton instance - lazy initialization to prevent SSR errors
let _vocabularyDB: VocabularyDatabase | null = null

function getVocabularyDB(): VocabularyDatabase {
  // Only create on client side
  if (typeof window === 'undefined') {
    // Return a dummy object for SSR (Next.js will hydrate on client)
    // This prevents SSR from trying to access IndexedDB
    return {
      senses: {
        count: async () => 0,
        get: async () => undefined,
        bulkGet: async () => [],
        toArray: async () => [],
        where: () => ({
          between: async () => [],
          startsWith: async () => [],
        }),
        toCollection: () => ({
          primaryKeys: async () => [],
        }),
        limit: () => ({
          toArray: async () => [],
        }),
        clear: async () => {},
      } as any,
      metadata: {
        get: async () => undefined,
        clear: async () => {},
      } as any,
    } as any as VocabularyDatabase
  }
  
  if (!_vocabularyDB) {
    _vocabularyDB = new VocabularyDatabase()
  }
  
  return _vocabularyDB
}

// Create a dummy object for SSR that matches the VocabularyDatabase interface
const createDummyDB = (): VocabularyDatabase => ({
  senses: {
    count: async () => 0,
    get: async () => undefined,
    bulkGet: async () => [],
    toArray: async () => [],
    where: () => ({
      between: async () => [],
      startsWith: async () => [],
    }),
    toCollection: () => ({
      primaryKeys: async () => [],
    }),
    limit: () => ({
      toArray: async () => [],
    }),
    clear: async () => {},
  } as any,
  metadata: {
    get: async () => undefined,
    clear: async () => {},
  } as any,
} as any as VocabularyDatabase)

// Export a proxy that lazily initializes only on client side
// Use Object.defineProperty to make it non-enumerable and prevent SSR serialization issues
let _vocabularyDBProxy: VocabularyDatabase | null = null

export const vocabularyDB = (typeof window !== 'undefined' 
  ? new Proxy({} as VocabularyDatabase, {
      get(target, prop) {
        return getVocabularyDB()[prop as keyof VocabularyDatabase]
      }
    })
  : createDummyDB()) as VocabularyDatabase

export const VOCABULARY_VERSION = '6.19-comprehensive-senses'
export const VERSION_KEY = 'vocabulary_version'

/**
 * Check if vocabulary is loaded and up-to-date
 * 
 * CRITICAL: Also validates data SCHEMA, not just version string!
 * If version matches but data structure is wrong, we purge and re-download.
 */
export async function isVocabularyReady(): Promise<boolean> {
  // Guard against SSR
  if (typeof window === 'undefined') {
    return false
  }
  
  try {
    const db = getVocabularyDB()
    const versionRecord = await db.metadata.get('version')
    const storedVersion = versionRecord?.value
    const count = await db.senses.count()
    
    // Step 1: Check version and count
    if (storedVersion !== VOCABULARY_VERSION || count < 10000) {
      if (process.env.NODE_ENV === 'development') {
        console.log(`⏳ Vocabulary not ready: count=${count}, version=${storedVersion || 'none'}`)
      }
      return false
    }
    
    // Step 2: SCHEMA VALIDATION - Sample a sense and verify structure
    // This catches cases where version was updated but old data persists
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 Validating vocabulary schema...')
    }
    
    // Get a sample sense (pick a common word that should have collocations)
    const sampleSense = await db.senses.get('theater.n.01')
    
    if (!sampleSense) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Sample sense not found - data may be corrupted')
      }
      await purgeVocabularyData()
      return false
    }
    
    // Check if data has Gemini-enriched schema (collocations)
    const hasCollocations = sampleSense.connections?.collocations && 
                           Array.isArray(sampleSense.connections.collocations)
    
    if (!hasCollocations) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Schema validation FAILED - old data structure detected')
        console.warn('   Expected: connections.collocations (array)')
        console.warn('   Found:', sampleSense.connections ? Object.keys(sampleSense.connections) : 'no connections')
        console.log('🗑️ Purging old vocabulary data...')
      }
      await purgeVocabularyData()
      return false
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ Vocabulary ready: ${count} senses, version ${storedVersion} (schema validated)`)
    }
    return true
    
  } catch (err) {
    console.error('❌ Error checking vocabulary:', err)
    return false
  }
}

/**
 * Purge all vocabulary data (senses + metadata)
 * Used when schema validation fails
 */
async function purgeVocabularyData(): Promise<void> {
  // Guard against SSR
  if (typeof window === 'undefined') {
    return
  }
  
  try {
    const db = getVocabularyDB()
    await db.senses.clear()
    await db.metadata.clear()
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ Vocabulary data purged')
    }
  } catch (err) {
    console.error('❌ Failed to purge vocabulary:', err)
  }
}

/**
 * Clear vocabulary cache
 */
export async function clearVocabularyCache(): Promise<void> {
  // Guard against SSR
  if (typeof window === 'undefined') {
    return
  }
  
  const db = getVocabularyDB()
  await db.senses.clear()
  await db.metadata.clear()
}

