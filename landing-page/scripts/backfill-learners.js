/**
 * Backfill Learner Profiles Script
 * 
 * Creates Learner profiles for existing children that don't have them.
 * Run this from the landing-page directory.
 */

const { createClient } = require('@supabase/supabase-js')
require('dotenv').config({ path: '.env.local' })

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('❌ Missing Supabase environment variables')
  console.error('   Make sure .env.local has NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
  process.exit(1)
}

async function backfillLearnerProfiles() {
  try {
    // Create Supabase client
    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    // Get current session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()
    
    if (sessionError || !session) {
      console.error('❌ Not authenticated. Please log in first.')
      console.error('   Error:', sessionError?.message || 'No session found')
      process.exit(1)
    }
    
    const token = session.access_token
    console.log('✅ Authenticated as:', session.user.email)
    console.log('📦 Calling backfill endpoint...\n')
    
    // Call the backfill endpoint
    const response = await fetch(`${API_BASE}/api/users/me/learners/backfill`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    
    const result = await response.json()
    
    console.log('✅ Backfill completed!')
    console.log(`   Created ${result.created_count} learner profile(s)`)
    console.log(`   Message: ${result.message}`)
    
  } catch (error) {
    console.error('❌ Error:', error.message)
    process.exit(1)
  }
}

backfillLearnerProfiles()

