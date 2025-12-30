#!/usr/bin/env node
/**
 * Test Lemon Squeezy Subscriptions API
 * 
 * Tests fetching subscriptions for a customer to see what data structure we get.
 */

import { config } from 'dotenv'
import { resolve } from 'path'

config({ path: resolve(process.cwd(), '.env.local') })
config({ path: resolve(process.cwd(), '.env') })

async function testSubscriptionsApi(customerId: string) {
  const apiKey = process.env.LEMON_SQUEEZY_API_KEY

  if (!apiKey) {
    console.error('❌ ERROR: LEMON_SQUEEZY_API_KEY is not configured')
    process.exit(1)
  }

  console.log('='.repeat(60))
  console.log('Test Lemon Squeezy Subscriptions API')
  console.log('='.repeat(60))
  console.log()
  console.log('🆔 Customer ID:', customerId)
  console.log()

  try {
    // Try different filter formats
    const url = `https://api.lemonsqueezy.com/v1/subscriptions?filter[customerId]=${customerId}`
    console.log('📤 Calling:', url)
    console.log()

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json'
      }
    })

    console.log('📥 Response Status:', response.status, response.statusText)
    console.log()

    const responseText = await response.text()
    console.log('📄 Response Body:')
    try {
      const json = JSON.parse(responseText)
      console.log(JSON.stringify(json, null, 2))
      
      if (json.data && json.data.length > 0) {
        console.log()
        console.log('✅ Found', json.data.length, 'subscription(s)')
        console.log()
        console.log('First subscription structure:')
        console.log('  ID:', json.data[0].id)
        console.log('  Links:', JSON.stringify(json.data[0].links, null, 2))
        console.log('  Attributes:', JSON.stringify(json.data[0].attributes, null, 2))
      } else {
        console.log()
        console.log('⚠️  No subscriptions found')
        console.log('   This is normal for one-time purchases (lifetime plans)')
      }
    } catch {
      console.log(responseText)
    }
  } catch (error: any) {
    console.error('❌ Error:', error.message)
  }
}

const args = process.argv.slice(2)
const customerId = args.find(arg => arg.startsWith('--customerId'))?.split('=')[1] || args[args.indexOf('--customerId') + 1] || '7430846'

testSubscriptionsApi(customerId)

