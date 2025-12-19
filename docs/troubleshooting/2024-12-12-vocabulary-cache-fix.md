# Vocabulary Cache Fix - Dec 12, 2024

## Problem

Users were not seeing Gemini-enriched vocabulary data (collocations, detailed explanations) even though:
- ✅ Backend `vocabulary.json` had enriched data
- ✅ Frontend `public/vocabulary.json` had enriched data  
- ❌ IndexedDB was serving stale WordNet data

### Root Cause

Two critical bugs:

1. **Cache Clear Function Was Async But Not Awaited**
   - `indexedDB.deleteDatabase()` returns immediately, doesn't wait
   - Page reloaded before databases were actually deleted
   - Result: "Clear Cache" button did nothing

2. **Version Check Was Too Lenient**
   - Only checked version STRING and count
   - Didn't validate actual DATA SCHEMA
   - When version was bumped, old data got relabeled with new version
   - Result: System thought data was fresh but it had old structure

## Solution

### Fix 1: Proper Async Cache Clearing

**File:** `landing-page/app/[locale]/(app)/learner/settings/page.tsx`

**Before:**
```typescript
const dbs = await indexedDB.databases()
for (const db of dbs) {
  if (db.name && !db.name.includes('supabase')) {
    indexedDB.deleteDatabase(db.name)  // ❌ Not awaited!
  }
}
window.location.reload()  // ❌ Reloads immediately!
```

**After:**
```typescript
const dbs = await indexedDB.databases()
const deletions = dbs
  .filter(db => db.name && !db.name.includes('supabase'))
  .map(db => {
    return new Promise<void>((resolve, reject) => {
      const request = indexedDB.deleteDatabase(db.name!)
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
      request.onblocked = () => resolve() // Don't block reload
    })
  })

await Promise.all(deletions)  // ✅ Wait for ALL deletions
window.location.reload()       // ✅ Only reload after complete
```

### Fix 2: Schema Validation

**File:** `landing-page/lib/vocabularyDB.ts`

Added schema validation to `isVocabularyReady()`:

```typescript
// Step 1: Check version and count (old logic)
if (storedVersion !== VOCABULARY_VERSION || count < 10000) {
  return false
}

// Step 2: SCHEMA VALIDATION (new logic)
const sampleSense = await vocabularyDB.senses.get('theater.n.01')
const hasCollocations = sampleSense.connections?.collocations && 
                       Array.isArray(sampleSense.connections.collocations)

if (!hasCollocations) {
  console.warn('Schema validation FAILED - old data structure')
  await purgeVocabularyData()  // Clear bad data
  return false
}
```

**Why This Works:**
- Samples a known word (`theater.n.01`)
- Checks if it has the NEW schema (`connections.collocations`)
- If not, purges ALL data and triggers re-download
- Ensures version string AND actual data match

## Version Changes

To force the fix:

1. **Database name:** `LexiCraftVocab_V3` → `LexiCraftVocab_V4_Gemini`
2. **Version string:** `5.0-gemini` → `6.0-gemini-enriched`
3. **Worker cache-bust:** `?v=3` → `?v=4`

## Testing

After deploying this fix:

1. **Clear cache via Settings:**
   - Go to ⚙️ Settings → 🗂️ Data
   - Click "🗑️ Clear Vocabulary Cache"
   - Should see console logs: `Deleting...` → `✅ Deleted`
   - Page reloads

2. **Schema validation triggers:**
   - On page load, console shows: `🔍 Validating vocabulary schema...`
   - If old data: `⚠️ Schema validation FAILED` → `🗑️ Purging old data...`
   - Triggers re-download from `/vocabulary.json`

3. **Verify enrichment loaded:**
   - Click any word in mine grid
   - Should see sections:
     - 💬 COLLOCATIONS (with CEFR badges, register markers, explanations)
     - 🔗 SYNONYMS
     - ⚡ ANTONYMS
     - 👨‍👩‍👧‍👦 WORD FAMILY
     - 📝 FORMS

## Console Logs (Success Path)

```
🔍 Checking vocabulary cache (main thread)...
🔍 Validating vocabulary schema...
✅ Vocabulary ready: 10470 senses, version 6.0-gemini-enriched (schema validated)
```

## Console Logs (Purge & Re-download Path)

```
🔍 Checking vocabulary cache (main thread)...
🔍 Validating vocabulary schema...
⚠️ Schema validation FAILED - old data structure detected
   Expected: connections.collocations (array)
   Found: ["related", "opposite", "confused"]
🗑️ Purging old vocabulary data...
✅ Vocabulary data purged
⏳ Vocabulary not ready: count=0, version=none
📬 Worker message: downloading...
📬 Worker message: parsing...
✅ Vocabulary ready: 10470 senses (hydration)
```

## Files Changed

1. `landing-page/app/[locale]/(app)/learner/settings/page.tsx` - Fixed async cache clear
2. `landing-page/lib/vocabularyDB.ts` - Added schema validation + purge function
3. `landing-page/lib/vocabularyLoader.ts` - Version bump
4. `landing-page/public/workers/vocab-loader.js` - Version bump
5. `landing-page/components/features/mining/MiningDetailPanel.tsx` - Removed debug logs

## Prevention

This fix prevents future schema migration issues:

- ✅ Cache clear button actually works
- ✅ Version checks validate actual schema, not just metadata
- ✅ Automatic purge when data structure mismatch detected
- ✅ Users get enriched data without manual intervention

## Related Docs

- `/docs/architecture/caching-strategy.md` - Overall caching approach
- `/docs/troubleshooting/` - Other troubleshooting guides







