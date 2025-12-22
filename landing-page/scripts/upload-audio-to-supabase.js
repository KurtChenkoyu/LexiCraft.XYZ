/**
 * Upload Audio Files to Supabase Storage
 * 
 * This script uploads all audio files (emoji, feedback, prompts, fx) from local filesystem to Supabase Storage.
 * 
 * Usage:
 *   node scripts/upload-audio-to-supabase.js
 * 
 * Prerequisites:
 *   - NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY) in .env.local
 *   - Audio files exist in landing-page/public/audio/ (all categories)
 * 
 * Note: Uses SECRET_KEY (not publishable/anon key) for upload permissions.
 * The new "Secret Key" (sb_secret_...) replaces the legacy "Service Role Key".
 */

require('dotenv').config({ path: '.env.local' })
const { createClient } = require('@supabase/supabase-js')
const fs = require('fs')
const path = require('path')

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
// Support both new (sb_secret_...) and legacy (service_role) key names
const SUPABASE_SECRET_KEY = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY

if (!SUPABASE_URL || !SUPABASE_SECRET_KEY) {
  console.error('❌ Missing Supabase environment variables')
  console.error('   Make sure .env.local has:')
  console.error('   - NEXT_PUBLIC_SUPABASE_URL')
  console.error('   - SUPABASE_SECRET_KEY (new: sb_secret_...) OR SUPABASE_SERVICE_ROLE_KEY (legacy)')
  console.error('   Get it from: Project Settings → API → Secret Key')
  console.error('   Note: Use Secret Key (not Publishable Key) for uploads')
  process.exit(1)
}

// Use SECRET_KEY for upload permissions (publishable/anon key cannot upload to Storage)
// The new "Secret Key" (sb_secret_...) replaces the legacy "Service Role Key"
const supabase = createClient(SUPABASE_URL, SUPABASE_SECRET_KEY)
const BUCKET_NAME = 'audio'
const AUDIO_BASE_DIR = path.join(__dirname, '../public/audio')

async function createBucketIfNotExists() {
  console.log('📦 Checking for audio bucket...')
  
  const { data: buckets, error: listError } = await supabase.storage.listBuckets()
  
  if (listError) {
    console.error('❌ Error listing buckets:', listError.message)
    throw listError
  }
  
  const audioBucket = buckets.find(b => b.name === BUCKET_NAME)
  
  if (audioBucket) {
    console.log('✅ Audio bucket already exists')
    if (!audioBucket.public) {
      console.warn('⚠️  Bucket exists but is not public. Making it public...')
      const { error: updateError } = await supabase.storage.updateBucket(BUCKET_NAME, {
        public: true
      })
      if (updateError) {
        console.error('❌ Error making bucket public:', updateError.message)
        throw updateError
      }
      console.log('✅ Bucket is now public')
    }
    return
  }
  
  console.log('📦 Creating audio bucket...')
  const { data, error } = await supabase.storage.createBucket(BUCKET_NAME, {
    public: true, // Make bucket public so files can be accessed
    fileSizeLimit: 52428800, // 50MB max file size
  })
  
  if (error) {
    console.error('❌ Error creating bucket:', error.message)
    throw error
  }
  
  console.log('✅ Audio bucket created successfully')
}

async function uploadFile(filePath, relativePath) {
  const fileContent = fs.readFileSync(filePath)
  // Preserve directory structure (e.g., "feedback/correct/well_done_coral.mp3")
  const storagePath = relativePath.replace(/\\/g, '/') // Normalize path separators
  
  // Check if file already exists (skip if exists to save time on re-runs)
  try {
    const { data: existingFile } = await supabase.storage
      .from(BUCKET_NAME)
      .list(path.dirname(storagePath) || undefined, {
        limit: 1000,
        search: path.basename(storagePath)
      })
    
    if (existingFile && existingFile.some(f => f.name === path.basename(storagePath))) {
      console.log(`  ⏭️  Skipping ${storagePath} (already exists)`)
      return true
    }
  } catch (err) {
    // If check fails, proceed with upload (might be first run or bucket doesn't exist yet)
  }
  
  console.log(`  📤 Uploading ${storagePath}...`)
  
  const { data, error } = await supabase.storage
    .from(BUCKET_NAME)
    .upload(storagePath, fileContent, {
      contentType: 'audio/mpeg', // MIME type for MP3 files (ensures browsers play, not download)
      upsert: true, // Overwrite if exists (backup safety)
    })
  
  if (error) {
    // If file already exists, that's okay (upsert should handle it, but check error code)
    if (error.message && error.message.includes('already exists')) {
      console.log(`  ⏭️  Skipping ${storagePath} (already exists)`)
      return true
    }
    console.error(`  ❌ Error uploading ${storagePath}:`, error.message)
    return false
  }
  
  console.log(`  ✅ Uploaded ${storagePath}`)
  return true
}

function getAllAudioFiles(dir) {
  const files = []
  
  if (!fs.existsSync(dir)) {
    console.warn(`⚠️  Directory does not exist: ${dir}`)
    return files
  }
  
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    
    if (entry.isDirectory()) {
      // Recursively search subdirectories
      files.push(...getAllAudioFiles(fullPath))
    } else if (entry.isFile() && entry.name.endsWith('.mp3')) {
      files.push(fullPath)
    }
  }
  
  return files
}

async function main() {
  console.log('🚀 Starting audio upload to Supabase Storage...\n')
  
  try {
    // Step 1: Create bucket if it doesn't exist
    await createBucketIfNotExists()
    
    // Step 2: Find all audio files (scan all categories: emoji, feedback, prompts, fx)
    console.log(`\n📁 Scanning for audio files in ${AUDIO_BASE_DIR}...`)
    const audioFiles = getAllAudioFiles(AUDIO_BASE_DIR)
    
    if (audioFiles.length === 0) {
      console.warn('⚠️  No audio files found!')
      console.warn(`   Expected location: ${AUDIO_BASE_DIR}`)
      console.warn('   Make sure audio files exist before running this script.')
      process.exit(0)
    }
    
    console.log(`✅ Found ${audioFiles.length} audio file(s)\n`)
    
    // Step 3: Upload files
    console.log('📤 Uploading files...\n')
    let successCount = 0
    let failCount = 0
    
    for (const filePath of audioFiles) {
      // Preserve directory structure relative to audio base directory
      const relativePath = path.relative(AUDIO_BASE_DIR, filePath)
      const success = await uploadFile(filePath, relativePath)
      
      if (success) {
        successCount++
      } else {
        failCount++
      }
    }
    
    // Step 4: Summary
    console.log('\n' + '='.repeat(50))
    console.log('📊 Upload Summary:')
    console.log(`   ✅ Success: ${successCount}`)
    console.log(`   ❌ Failed: ${failCount}`)
    console.log(`   📁 Total: ${audioFiles.length}`)
    console.log('='.repeat(50))
    
    if (failCount > 0) {
      console.error('\n⚠️  Some files failed to upload. Check errors above.')
      process.exit(1)
    }
    
    console.log('\n✅ All audio files uploaded successfully!')
    console.log(`\n🔗 Files are now available at:`)
    console.log(`   ${SUPABASE_URL}/storage/v1/object/public/${BUCKET_NAME}/`)
    console.log(`\n📝 Audio service already configured to use Supabase Storage URLs automatically!`)
    console.log(`   (When NEXT_PUBLIC_SUPABASE_URL is set, audio-service.ts uses Supabase URLs)`)
    
  } catch (error) {
    console.error('\n❌ Upload failed:', error.message)
    process.exit(1)
  }
}

main()

