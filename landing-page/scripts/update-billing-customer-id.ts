#!/usr/bin/env node
/**
 * Update Billing Customer ID Script
 * 
 * Updates the billing_customer_id in the database for a user.
 * This fixes the issue where simulation scripts use fake customer IDs.
 * 
 * Usage:
 *   npm run update-billing-customer-id -- --email user@example.com --customerId 123456
 * 
 * Requirements:
 *   - NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local
 *   - Or SUPABASE_URL and SUPABASE_ANON_KEY in .env.local
 */

import { config } from 'dotenv'
import { resolve } from 'path'
import { createClient } from '@supabase/supabase-js'

// Load environment variables
config({ path: resolve(process.cwd(), '.env.local') })
config({ path: resolve(process.cwd(), '.env') })

async function updateBillingCustomerId(email: string, customerId: string, userId?: string) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseKey) {
    console.error('❌ ERROR: Supabase credentials not found')
    console.error('   Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local')
    process.exit(1)
  }

  if (!customerId) {
    console.error('❌ ERROR: --customerId is required')
    process.exit(1)
  }

  if (!email && !userId) {
    console.error('❌ ERROR: Either --email or --userId is required')
    console.error('   Usage: npm run update-billing-customer-id -- --email user@example.com --customerId 123456')
    console.error('   Or:    npm run update-billing-customer-id -- --userId <uuid> --customerId 123456')
    process.exit(1)
  }

  console.log('='.repeat(60))
  console.log('Update Billing Customer ID')
  console.log('='.repeat(60))
  console.log()
  console.log('📧 Email:', email)
  console.log('🆔 Customer ID:', customerId)
  console.log()

  const supabase = createClient(supabaseUrl, supabaseKey)

  // First, verify the user exists
  console.log('🔍 Checking if user exists...')
  let user: any = null
  let userError: any = null

  if (userId) {
    // Try by user ID first (more reliable)
    const { data, error } = await supabase
      .from('users')
      .select('id, email, billing_customer_id')
      .eq('id', userId)
      .maybeSingle()
    
    user = data
    userError = error
  } else {
    // Try by email
    const { data: users, error } = await supabase
      .from('users')
      .select('id, email, billing_customer_id')
      .eq('email', email)
    
    if (error) {
      userError = error
    } else if (users && users.length > 0) {
      user = users[0]
      if (users.length > 1) {
        console.warn('⚠️  Warning: Multiple users found with that email. Using the first one.')
      }
    }
  }

  if (userError) {
    console.error('❌ Error querying users:', userError.message)
    console.error('   This might be due to RLS policies. Try using --userId instead.')
    process.exit(1)
  }

  if (!user) {
    console.error('❌ User not found')
    if (!userId) {
      console.error('   Try using: --userId <uuid> instead of --email')
      console.error('   User ID from earlier: a1f68c67-2c2d-45be-9aac-038bf23dd5bd')
    }
    process.exit(1)
  }

  console.log('✅ User found:')
  console.log('   ID:', user.id)
  console.log('   Current billing_customer_id:', user.billing_customer_id || '(null)')
  console.log()

  // Update the billing_customer_id
  console.log('🔄 Updating billing_customer_id...')
  const { data: updatedUser, error: updateError } = await supabase
    .from('users')
    .update({ 
      billing_customer_id: customerId,
      updated_at: new Date().toISOString()
    })
    .eq('id', user.id)
    .select('id, email, billing_customer_id, updated_at')
    .single()

  if (updateError) {
    console.error('❌ Failed to update:', updateError.message)
    process.exit(1)
  }

  console.log('✅ Successfully updated!')
  console.log()
  console.log('Updated user:')
  console.log('   ID:', updatedUser.id)
  console.log('   Email:', updatedUser.email)
  console.log('   billing_customer_id:', updatedUser.billing_customer_id)
  console.log('   updated_at:', updatedUser.updated_at)
  console.log()
  console.log('🎉 Done! You can now test the "Manage Subscription" button.')
  console.log()
}

// Parse command line arguments
const args = process.argv.slice(2)
let email: string | undefined
let customerId: string | undefined
let userId: string | undefined

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--email' && args[i + 1]) {
    email = args[i + 1]
    i++
  } else if (args[i] === '--customerId' && args[i + 1]) {
    customerId = args[i + 1]
    i++
  } else if (args[i] === '--userId' && args[i + 1]) {
    userId = args[i + 1]
    i++
  }
}

if (!customerId) {
  console.error('❌ ERROR: --customerId is required')
  console.error('   Usage: npm run update-billing-customer-id -- --email user@example.com --customerId 123456')
  console.error('   Or:    npm run update-billing-customer-id -- --userId <uuid> --customerId 123456')
  process.exit(1)
}

updateBillingCustomerId(email || '', customerId, userId)

