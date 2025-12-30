#!/usr/bin/env node
/**
 * Test Lemon Squeezy Portal API
 * 
 * Tests the portal API endpoint directly to see what error we get.
 * 
 * Usage:
 *   npm run test-portal-api -- --customerId 7430846
 */

import { config } from 'dotenv'
import { resolve } from 'path'

// Load environment variables
config({ path: resolve(process.cwd(), '.env.local') })
config({ path: resolve(process.cwd(), '.env') })

async function testPortalApi(customerId: string) {
  const apiKey = process.env.LEMON_SQUEEZY_API_KEY

  if (!apiKey) {
    console.error('❌ ERROR: LEMON_SQUEEZY_API_KEY is not configured')
    process.exit(1)
  }

  if (!customerId) {
    console.error('❌ ERROR: --customerId is required')
    console.error('   Usage: npm run test-portal-api -- --customerId 7430846')
    process.exit(1)
  }

  console.log('='.repeat(60))
  console.log('Test Lemon Squeezy Portal API')
  console.log('='.repeat(60))
  console.log()
  console.log('🆔 Customer ID:', customerId)
  console.log('🔑 API Key:', apiKey.substring(0, 10) + '...' + apiKey.substring(apiKey.length - 4))
  console.log()

  try {
    const url = `https://api.lemonsqueezy.com/v1/customers/${customerId}/portal`
    console.log('📤 Calling:', url)
    console.log()

    const response = await fetch(url, {
      method: 'POST',
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
    } catch {
      console.log(responseText)
    }
    console.log()

    if (response.ok) {
      const data = JSON.parse(responseText)
      const portalUrl = data.data?.attributes?.url
      if (portalUrl) {
        console.log('✅ Success! Portal URL:', portalUrl)
      } else {
        console.log('⚠️  Response OK but no portal URL in response')
      }
    } else {
      console.error('❌ API call failed')
      console.error('   Status:', response.status)
      console.error('   Status Text:', response.statusText)
    }
  } catch (error: any) {
    console.error('❌ Error:', error.message)
    if (error.stack) {
      console.error('   Stack:', error.stack)
    }
  }
}

// Parse command line arguments
const args = process.argv.slice(2)
let customerId: string | undefined

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--customerId' && args[i + 1]) {
    customerId = args[i + 1]
    break
  }
}

testPortalApi(customerId || '')

