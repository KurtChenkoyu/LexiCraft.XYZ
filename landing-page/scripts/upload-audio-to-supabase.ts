/**
 * Upload Audio Files to Supabase Storage
 * 
 * This script uploads emoji audio files from local filesystem to Supabase Storage.
 * 
 * Usage:
 *   npm run upload-audio
 *   OR
 *   npx tsx scripts/upload-audio-to-supabase.ts
 * 
 * Prerequisites:
 *   - NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local
 *   - Audio files exist in landing-page/public/audio/emoji/
 */

import { createClient } from '@supabase/supabase-js'
import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load environment variables
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('❌ Missing Supabase environment variables')
  console.error('   Make sure .env.local has NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
const BUCKET_NAME = 'audio'
const AUDIO_DIR = path.join(__dirname, '../public/audio/emoji')

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

async function uploadFile(filePath: string, relativePath: string): Promise<boolean> {
  const fileContent = fs.readFileSync(filePath)
  const fileName = path.basename(relativePath)
  const storagePath = `emoji/${fileName}`
  
  console.log(`  📤 Uploading ${fileName}...`)
  
  const { data, error } = await supabase.storage
    .from(BUCKET_NAME)
    .upload(storagePath, fileContent, {
      contentType: 'audio/mpeg',
      upsert: true, // Overwrite if exists
    })
  
  if (error) {
    console.error(`  ❌ Error uploading ${fileName}:`, error.message)
    return false
  }
  
  console.log(`  ✅ Uploaded ${fileName}`)
  return true
}

async function getAllAudioFiles(dir: string): Promise<string[]> {
  const files: string[] = []
  
  if (!fs.existsSync(dir)) {
    console.warn(`⚠️  Directory does not exist: ${dir}`)
    return files
  }
  
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    
    if (entry.isDirectory()) {
      // Recursively search subdirectories
      files.push(...await getAllAudioFiles(fullPath))
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
    
    // Step 2: Find all audio files
    console.log(`\n📁 Scanning for audio files in ${AUDIO_DIR}...`)
    const audioFiles = await getAllAudioFiles(AUDIO_DIR)
    
    if (audioFiles.length === 0) {
      console.warn('⚠️  No audio files found!')
      console.warn(`   Expected location: ${AUDIO_DIR}`)
      console.warn('   Make sure audio files exist before running this script.')
      process.exit(0)
    }
    
    console.log(`✅ Found ${audioFiles.length} audio file(s)\n`)
    
    // Step 3: Upload files
    console.log('📤 Uploading files...\n')
    let successCount = 0
    let failCount = 0
    
    for (const filePath of audioFiles) {
      const relativePath = path.relative(AUDIO_DIR, filePath)
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
    console.log(`   ${SUPABASE_URL}/storage/v1/object/public/${BUCKET_NAME}/emoji/`)
    
  } catch (error: any) {
    console.error('\n❌ Upload failed:', error.message)
    process.exit(1)
  }
}

main()

