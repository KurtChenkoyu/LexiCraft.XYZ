#!/usr/bin/env node
/**
 * Lemon Squeezy Webhook Simulation Script
 * 
 * Generates valid Lemon Squeezy webhook payloads and sends them to the local API endpoint.
 * This allows rapid, repeatable testing of the webhook handler without needing real payments.
 * 
 * Usage:
 *   npm run simulate-webhook -- --email user@example.com --userId <uuid>
 *   npm run simulate-webhook -- --email user@example.com --userId <uuid> --status trial --plan 6-month-pass
 * 
 * Requirements:
 *   - LEMON_SQUEEZY_WEBHOOK_SECRET in .env.local
 *   - Backend API running on http://localhost:8000
 *   - Frontend API running on http://localhost:3000
 */

import crypto from 'crypto'
import { config } from 'dotenv'
import { resolve } from 'path'

// Load environment variables from .env.local (Next.js convention)
config({ path: resolve(process.cwd(), '.env.local') })
config({ path: resolve(process.cwd(), '.env') }) // Fallback to .env

// Parse command-line arguments
interface Args {
  email?: string
  userId?: string
  status?: 'active' | 'trial' | 'cancelled' | 'expired'
  plan?: string
  endDate?: string
}

function parseArgs(): Args {
  const args: Args = {}
  const argv = process.argv.slice(2)
  
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    const nextArg = argv[i + 1]
    
    if (arg === '--email' && nextArg) {
      args.email = nextArg
      i++
    } else if (arg === '--userId' && nextArg) {
      args.userId = nextArg
      i++
    } else if (arg === '--status' && nextArg) {
      args.status = nextArg as Args['status']
      i++
    } else if (arg === '--plan' && nextArg) {
      args.plan = nextArg
      i++
    } else if (arg === '--endDate' && nextArg) {
      args.endDate = nextArg
      i++
    }
  }
  
  return args
}

function generateWebhookPayload(args: Args): any {
  const subscriptionId = `sub_${Date.now()}`
  const variantId = `var_${Date.now()}`
  const customerId = `cus_${Date.now()}`
  
  // Map plan type to variant name
  const planToVariantName: Record<string, string> = {
    'lifetime': 'Lifetime Pass',
    '6-month-pass': '6-Month Pass',
    '12-month-pass': '12-Month Pass',
    'monthly': 'Monthly Subscription',
    'yearly': 'Yearly Subscription'
  }
  
  const variantName = args.plan ? planToVariantName[args.plan] || args.plan : 'Lifetime Pass'
  const status = args.status || 'active'
  const endDate = args.endDate || (args.plan === 'lifetime' ? null : new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString())
  
  // Build custom_data object (where user_id is stored)
  const customData: any = {}
  if (args.userId) {
    customData.user_id = args.userId
  }
  
  // Build payload matching Lemon Squeezy structure
  const payload = {
    meta: {
      event_name: 'subscription_created',
      custom_data: customData
    },
    data: {
      type: 'subscriptions',
      id: subscriptionId,
      attributes: {
        status: status,
        user_email: args.email,
        variant_name: variantName,
        ends_at: endDate,
        renews_at: endDate,
        custom_data: customData
      }
    },
    included: [
      {
        type: 'customers',
        id: customerId,
        attributes: {
          email: args.email
        }
      },
      {
        type: 'variants',
        id: variantId,
        attributes: {
          name: variantName
        }
      }
    ]
  }
  
  return payload
}

function computeSignature(body: string, secret: string): string {
  const hmac = crypto.createHmac('sha256', secret)
  const digest = hmac.update(body).digest('hex')
  return `sha256=${digest}`
}

async function sendWebhook(payload: any, signature: string): Promise<Response> {
  const url = 'http://localhost:3000/api/webhooks/lemonsqueezy'
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Signature': signature
    },
    body: JSON.stringify(payload)
  })
  
  return response
}

async function main() {
  console.log('='.repeat(60))
  console.log('Lemon Squeezy Webhook Simulation')
  console.log('='.repeat(60))
  console.log()
  
  // Parse arguments
  const args = parseArgs()
  
  // Validate required arguments
  if (!args.email) {
    console.error('❌ ERROR: --email is required')
    console.error('   Usage: npm run simulate-webhook -- --email user@example.com [--userId <uuid>] [--status active] [--plan lifetime] [--endDate <iso-date>]')
    process.exit(1)
  }
  
  // Check webhook secret
  const webhookSecret = process.env.LEMON_SQUEEZY_WEBHOOK_SECRET
  if (!webhookSecret) {
    console.error('❌ ERROR: LEMON_SQUEEZY_WEBHOOK_SECRET is not configured')
    console.error('   Set it in .env.local or .env file')
    console.error('   Example: LEMON_SQUEEZY_WEBHOOK_SECRET=your-secret-key')
    process.exit(1)
  }
  
  // Generate payload
  console.log('📦 Generating webhook payload...')
  const payload = generateWebhookPayload(args)
  
  console.log('   Email:', args.email)
  if (args.userId) {
    console.log('   User ID:', args.userId)
  }
  console.log('   Status:', payload.data.attributes.status)
  console.log('   Plan:', payload.data.attributes.variant_name)
  console.log('   End Date:', payload.data.attributes.ends_at || 'NULL (lifetime)')
  console.log()
  
  // Compute signature
  const body = JSON.stringify(payload)
  const signature = computeSignature(body, webhookSecret)
  console.log('🔐 Computed signature:', signature.substring(0, 30) + '...')
  console.log()
  
  // Send webhook
  console.log('📤 Sending webhook to http://localhost:3000/api/webhooks/lemonsqueezy...')
  try {
    const response = await sendWebhook(payload, signature)
    const responseData = await response.json()
    
    console.log()
    console.log('📥 Response:')
    console.log('   Status:', response.status, response.statusText)
    console.log('   Body:', JSON.stringify(responseData, null, 2))
    console.log()
    
    if (response.ok) {
      console.log('✅ Webhook sent successfully!')
      if (responseData.pending_assignment) {
        console.log('⚠️  Note: User not found - pending manual assignment')
      } else {
        console.log('✅ Subscription activated successfully!')
      }
      process.exit(0)
    } else {
      console.error('❌ Webhook failed:', responseData.error || responseData.message || 'Unknown error')
      process.exit(1)
    }
  } catch (error: any) {
    console.error()
    console.error('❌ Error sending webhook:', error.message)
    if (error.message.includes('ECONNREFUSED')) {
      console.error('   Make sure the frontend server is running on http://localhost:3000')
    }
    process.exit(1)
  }
}

main().catch((error) => {
  console.error('❌ Unexpected error:', error)
  process.exit(1)
})

