/**
 * Verification Script for Caching Implementation
 * 
 * This script verifies that the caching implementation follows the "Last War" approach:
 * - IndexedDB is the ONLY cache for user data
 * - localStorage is FORBIDDEN for user data (except tiny UI preferences)
 * - All user data loads from IndexedDB on mount
 * - All user data saves to IndexedDB when changed
 * 
 * Run this script to verify the implementation is correct.
 */

import * as fs from 'fs'
import * as path from 'path'

const ROOT_DIR = path.join(__dirname, '..')
const USER_DATA_CONTEXT = path.join(ROOT_DIR, 'contexts/UserDataContext.tsx')
const DOWNLOAD_SERVICE = path.join(ROOT_DIR, 'services/downloadService.ts')
const LOCAL_STORE = path.join(ROOT_DIR, 'lib/local-store.ts')
const MINE_PAGE = path.join(ROOT_DIR, 'app/[locale]/(app)/mine/page.tsx')

interface VerificationResult {
  file: string
  passed: boolean
  issues: string[]
}

const results: VerificationResult[] = []

function verifyFile(filePath: string, checks: {
  mustContain?: string[]
  mustNotContain?: string[]
  description: string
}) {
  const content = fs.readFileSync(filePath, 'utf-8')
  const result: VerificationResult = {
    file: path.relative(ROOT_DIR, filePath),
    passed: true,
    issues: []
  }

  // Check must contain
  if (checks.mustContain) {
    for (const pattern of checks.mustContain) {
      if (!content.includes(pattern)) {
        result.passed = false
        result.issues.push(`Missing required pattern: ${pattern}`)
      }
    }
  }

  // Check must not contain
  if (checks.mustNotContain) {
    for (const pattern of checks.mustNotContain) {
      if (content.includes(pattern)) {
        result.passed = false
        result.issues.push(`Contains forbidden pattern: ${pattern}`)
      }
    }
  }

  results.push(result)
}

console.log('🔍 Verifying Caching Implementation...\n')

// Verify UserDataContext.tsx
verifyFile(USER_DATA_CONTEXT, {
  description: 'UserDataContext uses IndexedDB only',
  mustContain: [
    'CACHING STRATEGY (IMMUTABLE',
    'downloadService.getProfile()',
    'downloadService.getChildren()',
    'localStore.setCache',
    'CACHE_KEYS.PROFILE',
    'CACHE_KEYS.CHILDREN'
  ],
  mustNotContain: [
    'localStorage.getItem(STORAGE_KEYS.PROFILE',
    'localStorage.getItem(STORAGE_KEYS.CHILDREN',
    'localStorage.setItem(STORAGE_KEYS.PROFILE',
    'localStorage.setItem(STORAGE_KEYS.CHILDREN'
  ]
})

// Verify downloadService.ts
verifyFile(DOWNLOAD_SERVICE, {
  description: 'downloadService has caching strategy comments',
  mustContain: [
    'CACHING STRATEGY (IMMUTABLE',
    'IndexedDB is the ONLY cache'
  ]
})

// Verify local-store.ts
verifyFile(LOCAL_STORE, {
  description: 'local-store has caching strategy comments',
  mustContain: [
    'CACHING STRATEGY (IMMUTABLE',
    'IndexedDB is the ONLY cache'
  ]
})

// Verify mine/page.tsx (starter pack)
verifyFile(MINE_PAGE, {
  description: 'Starter pack uses IndexedDB',
  mustContain: [
    'localStore.getCache',
    'localStore.setCache',
    'STARTER_PACK_CACHE_KEY'
  ],
  mustNotContain: [
    'localStorage.getItem(STARTER_PACK',
    'localStorage.setItem(STARTER_PACK'
  ]
})

// Print results
console.log('Results:\n')
let allPassed = true
for (const result of results) {
  const status = result.passed ? '✅' : '❌'
  console.log(`${status} ${result.file}`)
  if (result.issues.length > 0) {
    allPassed = false
    for (const issue of result.issues) {
      console.log(`   - ${issue}`)
    }
  }
}

console.log('\n' + '='.repeat(50))
if (allPassed) {
  console.log('✅ All verification checks passed!')
  console.log('\nNext step: Run manual browser testing (see testing checklist)')
} else {
  console.log('❌ Some verification checks failed!')
  console.log('Please fix the issues above before proceeding.')
}
console.log('='.repeat(50))

process.exit(allPassed ? 0 : 1)

