import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

// Prevent Next.js from caching this route
export const dynamic = 'force-dynamic'
export const revalidate = 0

/**
 * Lemon Squeezy Webhook Handler
 * 
 * Handles subscription events from Lemon Squeezy
 * POST /api/webhooks/lemonsqueezy
 */
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
  const signature = request.headers.get('x-signature')

  if (!signature) {
    console.error('Missing x-signature header')
    return NextResponse.json(
      { error: 'Missing signature' },
      { status: 400 }
    )
  }

  // Verify signature
  try {
    const signatureHash = signature.replace(/^sha256=/, '')
    const hmac = crypto.createHmac('sha256', webhookSecret)
    const digest = hmac.update(body).digest('hex')
    
    if (!crypto.timingSafeEqual(
      Buffer.from(signatureHash, 'hex'),
      Buffer.from(digest, 'hex')
    )) {
      console.error('Invalid webhook signature')
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 401 }
      )
    }
  } catch (error: any) {
    console.error('Signature verification error:', error)
    return NextResponse.json(
      { error: 'Signature verification failed' },
      { status: 401 }
    )
  }

  // Parse webhook data
  let data: any
  try {
    data = JSON.parse(body)
  } catch (error) {
    console.error('Failed to parse webhook body:', error)
    return NextResponse.json(
      { error: 'Invalid JSON' },
      { status: 400 }
    )
  }

  // Log webhook event (dev mode only)
  if (process.env.NODE_ENV === 'development') {
    console.log('📦 [Webhook] Received event:', {
      meta: data.meta,
      data: data.data,
      type: data.meta?.event_name
    })
  }

  // Extract subscription data
  const subscription = data.data?.attributes
  if (!subscription) {
    console.error('Missing subscription data in webhook')
    return NextResponse.json(
      { error: 'Missing subscription data' },
      { status: 400 }
    )
  }

  // Extract email from customer data
  const customerEmail = data.data?.attributes?.user_email || 
                        data.included?.find((item: any) => item.type === 'customers')?.attributes?.email

  if (!customerEmail) {
    console.warn('⚠️ [Webhook] No email found in webhook payload')
    return NextResponse.json({
      received: true,
      pending_assignment: true,
      message: 'User not found - logged for manual review'
    })
  }

  // Map Lemon Squeezy status to our subscription_status
  const lsStatus = subscription.status || 'inactive'
  const subscriptionStatus = lsStatus === 'active' ? 'active' : 
                            lsStatus === 'cancelled' ? 'cancelled' : 
                            lsStatus === 'expired' ? 'expired' : 'inactive'

  // Extract plan type from variant name or product name
  const variantName = data.included?.find((item: any) => item.type === 'variants')?.attributes?.name ||
                      subscription.variant_name ||
                      '6-Month Pass' // Default fallback
  const planType = variantName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')

  // Extract subscription end date
  const subscriptionEndDate = subscription.ends_at || subscription.renews_at || null

  // Call backend API to update subscription
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 10000) // 10 second timeout

  try {
    const response = await fetch(`${backendUrl}/api/v1/subscriptions/activate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: customerEmail,
        subscription_status: subscriptionStatus,
        plan_type: planType,
        subscription_end_date: subscriptionEndDate,
      }),
      signal: controller.signal,
    })

    clearTimeout(timeout)

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`Backend API error (${response.status}):`, errorText)
      
      // If user not found, return 200 but log for manual review
      if (response.status === 404) {
        return NextResponse.json({
          received: true,
          pending_assignment: true,
          message: 'User not found - logged for manual review'
        })
      }
      
      return NextResponse.json(
        { error: 'Backend API error', details: errorText },
        { status: 500 }
      )
    }

    const result = await response.json()
    
    return NextResponse.json({
      received: true,
      result
    })
  } catch (error: any) {
    clearTimeout(timeout)
    
    if (error.name === 'AbortError') {
      console.error('Backend API timeout after 10 seconds')
      return NextResponse.json(
        { error: 'Backend API timeout' },
        { status: 504 }
      )
    }
    
    console.error('Error calling backend API:', error)
    return NextResponse.json(
      { error: 'Failed to process webhook', details: error.message },
      { status: 500 }
    )
  }
}
