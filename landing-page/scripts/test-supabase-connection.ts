/**
 * Test Supabase Connection
 * 
 * Run this script to verify Supabase connection health
 * Usage: npx tsx scripts/test-supabase-connection.ts
 */

import { testConnection, resetClient, createClient } from '../lib/supabase/client'

async function main() {
  console.log('🔍 Testing Supabase connection...\n')
  
  // Test 1: Check if client can be created
  console.log('Test 1: Creating Supabase client...')
  try {
    const client = createClient()
    console.log('✅ Client created successfully')
  } catch (error: any) {
    console.error('❌ Failed to create client:', error.message)
    process.exit(1)
  }
  
  // Test 2: Test connection health
  console.log('\nTest 2: Testing connection health...')
  const isHealthy = await testConnection()
  
  if (isHealthy) {
    console.log('✅ Connection test passed - Supabase is connected!')
  } else {
    console.log('⚠️ Connection test failed - attempting reset...')
    
    // Test 3: Reset and retry
    console.log('\nTest 3: Resetting client and retrying...')
    resetClient()
    const retryHealthy = await testConnection()
    
    if (retryHealthy) {
      console.log('✅ Connection restored after reset!')
    } else {
      console.error('❌ Connection still failing after reset')
      console.error('   Check your Supabase credentials and network connection')
      process.exit(1)
    }
  }
  
  // Test 4: Try to get session
  console.log('\nTest 4: Testing session retrieval...')
  try {
    const client = createClient()
    const { data, error } = await client.auth.getSession()
    
    if (error) {
      console.warn('⚠️ Session error (this is OK if not logged in):', error.message)
    } else if (data.session) {
      console.log('✅ Active session found:', data.session.user.email)
    } else {
      console.log('ℹ️  No active session (user not logged in)')
    }
  } catch (error: any) {
    console.error('❌ Failed to get session:', error.message)
  }
  
  console.log('\n✅ All tests completed!')
}

main().catch(console.error)

