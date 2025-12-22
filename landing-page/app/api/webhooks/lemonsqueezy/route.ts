import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

/**
 * Lemon Squeezy Webhook Handler
 * 
 * Handles subscription events from Lemon Squeezy
 * POST /api/webhooks/lemonsqueezy
 * 
 * Events handled:
 * - order_created: Initial purchase
 * - subscription_created: Subscription activated
 * - subscription_updated: Subscription status changed
 * - subscription_cancelled: Subscription cancelled
 */

// Disable body parsing for webhooks (Lemon Squeezy needs raw body for signature verification)
export const runtime = 'nodejs'

/**
 * Verify Lemon Squeezy webhook signature using HMAC-SHA256
 * 
 * Lemon Squeezy sends signature in format: "sha256=<hash>"
 * We need to extract the hash and compare with our computed HMAC
 */
function verifySignature(body: string, signature: string, secret: string): boolean {
  try {
    // Extract hash from signature (format: "sha256=<hash>" or just "<hash>")
    const signatureHash = signature.replace(/^sha256=/, '')
    
    // Compute HMAC-SHA256
    const hmac = crypto.createHmac('sha256', secret)
    const digest = hmac.update(body).digest('hex')
    
    // Use timing-safe comparison to prevent timing attacks
    return crypto.timingSafeEqual(
      Buffer.from(signatureHash, 'hex'),
      Buffer.from(digest, 'hex')
    )
  } catch (error) {
    console.error('Signature verification error:', error)
    return false
  }
}

/**
 * Map Lemon Squeezy status to our subscription_status values
 */
function mapLemonSqueezyStatus(lsStatus: string): string {
  const statusLower = lsStatus.toLowerCase()
  
  if (statusLower === 'on_trial') {
    return 'trial'
  } else if (statusLower === 'active') {
    return 'active'
  } else if (statusLower === 'past_due') {
    return 'past_due'
  } else if (['unpaid', 'cancelled', 'expired'].includes(statusLower)) {
    return 'inactive'
  } else {
    // Default to inactive for unknown statuses
    return 'inactive'
  }
}

/**
 * Extract plan type from Lemon Squeezy product/variant name
 */
function extractPlanType(variantName?: string, productName?: string): string | null {
  const name = variantName || productName || ''
  const nameLower = name.toLowerCase()
  
  if (nameLower.includes('6-month') || nameLower.includes('6 month')) {
    return '6-month-pass'
  } else if (nameLower.includes('12-month') || nameLower.includes('12 month')) {
    return '12-month-pass'
  }
  
  return null
}

export async function POST(request: NextRequest) {
  const webhookSecret = process.env.LEMON_SQUEEZY_WEBHOOK_SECRET
  const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  if (!webhookSecret) {
    console.error('LEMON_SQUEEZY_WEBHOOK_SECRET is not configured')
    return NextResponse.json(
      { error: 'Webhook secret not configured' },
      { status: 500 }
    )
  }

  // Get raw body for signature verification
  const body = await request.text()
  // Lemon Squeezy sends signature in x-signature header (format: "sha256=<hash>")
  const signature = request.headers.get('x-signature') || request.headers.get('signature') || ''

  if (!signature) {
    console.error('Missing webhook signature header')
    return NextResponse.json(
      { error: 'Missing signature header' },
      { status: 400 }
    )
  }

  // Verify signature
  if (!verifySignature(body, signature, webhookSecret)) {
    console.error('Webhook signature verification failed')
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    )
  }

  let event: any
  try {
    event = JSON.parse(body)
  } catch (error) {
    console.error('Failed to parse webhook body:', error)
    return NextResponse.json(
      { error: 'Invalid JSON body' },
      { status: 400 }
    )
  }

  const eventType = event.meta?.event_name || event.type
  console.log(`📦 Lemon Squeezy webhook received: ${eventType}`)

  // Handle different event types
  try {
    let email: string | null = null
    let subscriptionStatus: string | null = null
    let planType: string | null = null
    let endDate: string | null = null

    // Extract data based on event type
    if (eventType === 'order_created' || eventType === 'subscription_created' || 
        eventType === 'subscription_updated' || eventType === 'subscription_cancelled') {
      
      const attributes = event.data?.attributes || {}
      
      // Extract email (try multiple possible fields)
      email = attributes.customer_email || 
              attributes.user_email || 
              attributes.email ||
              event.data?.relationships?.customer?.data?.attributes?.email ||
              null

      // Extract subscription status
      subscriptionStatus = attributes.status || null

      // Extract plan type from variant or product
      const variantName = attributes.variant_name || 
                         event.data?.relationships?.variant?.data?.attributes?.name
      const productName = attributes.product_name ||
                         event.data?.relationships?.product?.data?.attributes?.name
      planType = extractPlanType(variantName, productName)

      // Extract end date
      endDate = attributes.ends_at || 
                attributes.renews_at || 
                attributes.expires_at ||
                null
    }

    // Only process if we have email and status
    if (!email || !subscriptionStatus) {
      console.warn(`⚠️ Webhook missing required data: email=${!!email}, status=${!!subscriptionStatus}`)
      return NextResponse.json({ received: true, skipped: 'Missing required data' })
    }

    // Map Lemon Squeezy status to our values
    const mappedStatus = mapLemonSqueezyStatus(subscriptionStatus)

    console.log(`🔄 Processing subscription update:`, {
      email,
      lemonSqueezyStatus: subscriptionStatus,
      mappedStatus,
      planType,
      endDate,
      eventType
    })

    // Call backend API to update subscription
    try {
      const response = await fetch(`${backendUrl}/api/subscriptions/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          subscription_status: mappedStatus,
          plan_type: planType,
          subscription_end_date: endDate,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        
        // Handle email mismatch (404) - log as Pending Assignment but return 200 OK
        if (response.status === 404) {
          console.warn(`⚠️ PENDING ASSIGNMENT: User not found for email: ${email}`, {
            email,
            subscription_status: mappedStatus,
            plan_type: planType,
            end_date: endDate,
            event_type: eventType,
            webhook_payload: event.data,
          })
          
          // TODO: Store this in a "pending_assignments" table or log file for manual review
          // For now, we log it and return success to Lemon Squeezy
          return NextResponse.json({ 
            received: true, 
            pending_assignment: true,
            message: 'User not found - logged for manual review'
          })
        }

        // Other errors - log but don't fail the webhook
        console.error(`❌ Backend API error (${response.status}):`, errorData)
        return NextResponse.json({ 
          received: true, 
          error: 'Backend update failed (non-critical)',
          status: response.status
        })
      }

      const result = await response.json()
      console.log(`✅ Subscription updated successfully:`, result)

      return NextResponse.json({ received: true, result })
    } catch (error: any) {
      console.error('❌ Failed to call backend API:', error)
      // Don't fail the webhook - we can retry later
      return NextResponse.json({ 
        received: true, 
        error: 'Backend API call failed (non-critical)',
        message: error.message
      })
    }
  } catch (error: any) {
    console.error('❌ Error processing webhook:', error)
    return NextResponse.json(
      { error: 'Webhook processing failed', message: error.message },
      { status: 500 }
    )
  }
}

