#!/usr/bin/env node
/**
 * Find Customer ID Script
 * 
 * Looks up the Lemon Squeezy customer ID for a given email address.
 * This helps fix the billing_customer_id in the database when it's missing.
 * 
 * Usage:
 *   npm run find-customer-id -- --email user@example.com
 * 
 * Requirements:
 *   - LEMON_SQUEEZY_API_KEY in .env.local
 */

import { config } from 'dotenv'
import { resolve } from 'path'

// Load environment variables
config({ path: resolve(process.cwd(), '.env.local') })
config({ path: resolve(process.cwd(), '.env') })

async function findCustomerId(email: string) {
  const apiKey = process.env.LEMON_SQUEEZY_API_KEY
  
  if (!apiKey) {
    console.error('❌ ERROR: LEMON_SQUEEZY_API_KEY is not configured')
    console.error('   Set it in .env.local or .env file')
    process.exit(1)
  }

  if (!email) {
    console.error('❌ ERROR: --email is required')
    console.error('   Usage: npm run find-customer-id -- --email user@example.com')
    process.exit(1)
  }

  console.log('='.repeat(60))
  console.log('Lemon Squeezy Customer ID Lookup')
  console.log('='.repeat(60))
  console.log()
  console.log('📧 Looking up customer ID for:', email)
  console.log()

  try {
    const response = await fetch(
      `https://api.lemonsqueezy.com/v1/customers?filter[email]=${encodeURIComponent(email)}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Accept': 'application/vnd.api+json',
          'Content-Type': 'application/vnd.api+json'
        }
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ API Error:', response.status, response.statusText)
      console.error('   Response:', errorText)
      process.exit(1)
    }

    const data = await response.json()
    const customers = data.data || []

    if (customers.length === 0) {
      console.log('⚠️  No customer found with email:', email)
      console.log()
      console.log('   This could mean:')
      console.log('   1. The email doesn\'t match any Lemon Squeezy customer')
      console.log('   2. You\'re using Test Mode API key but customer is in Live Mode (or vice versa)')
      console.log('   3. The customer hasn\'t made any purchases yet')
      process.exit(1)
    }

    console.log('✅ Found', customers.length, 'customer(s):')
    console.log()

    customers.forEach((customer: any, index: number) => {
      console.log(`Customer ${index + 1}:`)
      console.log('   ID:', customer.id)
      console.log('   Email:', customer.attributes?.email || 'N/A')
      console.log('   Name:', customer.attributes?.name || 'N/A')
      console.log('   Created:', customer.attributes?.createdAt || 'N/A')
      console.log()
    })

    // If only one customer, show the SQL command
    if (customers.length === 1) {
      const customerId = customers[0].id
      console.log('📋 SQL Command to update database:')
      console.log()
      console.log(`UPDATE public.users`)
      console.log(`SET billing_customer_id = '${customerId}',`)
      console.log(`    updated_at = NOW()`)
      console.log(`WHERE email = '${email}';`)
      console.log()
    }

    process.exit(0)
  } catch (error: any) {
    console.error('❌ Error:', error.message)
    if (error.message.includes('ECONNREFUSED') || error.message.includes('fetch')) {
      console.error('   Check your internet connection')
    }
    process.exit(1)
  }
}

// Parse command line arguments
const args = process.argv.slice(2)
let email: string | undefined

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--email' && args[i + 1]) {
    email = args[i + 1]
    break
  }
}

findCustomerId(email || '')

