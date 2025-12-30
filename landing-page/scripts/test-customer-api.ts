#!/usr/bin/env node
/**
 * Test Lemon Squeezy Customer API
 * 
 * Tests fetching customer details to see if we can get a signed portal URL.
 */

import { config } from 'dotenv'
import { resolve } from 'path'

config({ path: resolve(process.cwd(), '.env.local') })
config({ path: resolve(process.cwd(), '.env') })

async function testCustomerApi(customerId: string) {
  const apiKey = process.env.LEMON_SQUEEZY_API_KEY

  if (!apiKey) {
    console.error('❌ ERROR: LEMON_SQUEEZY_API_KEY is not configured')
    process.exit(1)
  }

  console.log('='.repeat(60))
  console.log('Test Lemon Squeezy Customer API')
  console.log('='.repeat(60))
  console.log()
  console.log('🆔 Customer ID:', customerId)
  console.log()

  try {
    const url = `https://api.lemonsqueezy.com/v1/customers/${customerId}`
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
      
      if (json.data) {
        console.log()
        console.log('✅ Customer found')
        console.log('  ID:', json.data.id)
        console.log('  Email:', json.data.attributes?.email)
        console.log('  URLs:', JSON.stringify(json.data.attributes?.urls, null, 2))
        
        if (json.data.attributes?.urls?.customer_portal) {
          console.log()
          console.log('🎉 Signed Portal URL found:', json.data.attributes.urls.customer_portal)
        } else {
          console.log()
          console.log('⚠️  No signed portal URL in response')
        }
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

testCustomerApi(customerId)

