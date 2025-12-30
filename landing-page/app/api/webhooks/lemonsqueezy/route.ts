import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'
import { createClient } from '@/lib/supabase/server'

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

  // Extract event type
  const eventName = data.meta?.event_name

  // Log webhook event (dev mode only)
  if (process.env.NODE_ENV === 'development') {
    console.log('📦 [Webhook] Received event:', {
      meta: data.meta,
      data: data.data,
      type: eventName
    })
  }

  // Extract subscription data (may not exist for all event types)
  const subscription = data.data?.attributes
      
  // Extract user_id from custom data (PRIMARY - immutable identifier)
  // Lemon Squeezy stores checkout custom data in subscription attributes
  const customData = data.data?.attributes?.custom_data || 
                     data.data?.attributes?.custom || 
                     data.meta?.custom_data || 
                     {}
  const userIdFromCustom = customData?.user_id || customData?.['checkout[custom][user_id]']

  // Extract email from customer data (FALLBACK - for backward compatibility)
  const customerEmail = data.data?.attributes?.user_email || 
                        data.included?.find((item: any) => item.type === 'customers')?.attributes?.email

  // Extract customer_id from payload (required for portal API)
  // Can be in subscription attributes or included customer object
  const customerId = data.data?.attributes?.customer_id ||
                     data.included?.find((item: any) => item.type === 'customers')?.id ||
                     data.data?.relationships?.customer?.data?.id

  // Log extraction attempt (for debugging)
  if (process.env.NODE_ENV === 'development') {
    console.log('🔍 [Webhook] Extracting user identity:', {
      user_id_from_custom: userIdFromCustom,
      user_email: customerEmail,
      custom_data_keys: Object.keys(customData),
      subscription_attributes: Object.keys(data.data?.attributes || {})
    })
  }

  // CRITICAL: Require either user_id OR email (at least one must be present)
  if (!userIdFromCustom && !customerEmail) {
    console.warn('⚠️ [Webhook] No user_id or email found in webhook payload')
    return NextResponse.json({
      received: true,
      pending_assignment: true,
      message: 'User not found - no user_id or email in payload'
    })
  }

  // Initialize Supabase client for database operations
  const supabase = await createClient()

  // Update billing_customer_id if present and user_id is available
  // This ensures we capture customer_id on first webhook (self-healing)
  if (customerId && userIdFromCustom) {
    try {
      const { error: updateError } = await supabase
        .from('users')
        .update({ billing_customer_id: customerId })
        .eq('id', userIdFromCustom)
        .is('billing_customer_id', null)  // Only update if currently null

      if (updateError) {
        console.warn('⚠️ [Webhook] Failed to update billing_customer_id:', updateError.message)
        // Don't fail webhook - this is non-critical
      } else {
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ [Webhook] Updated billing_customer_id:', customerId)
        }
      }
    } catch (error: any) {
      console.warn('⚠️ [Webhook] Error updating billing_customer_id:', error.message)
      // Don't fail webhook - this is non-critical
    }
  }

  // Handle subscription_payment_success event (record payment transaction)
  if (eventName === 'subscription_payment_success' || eventName === 'order_created') {
    try {
      // Extract payment details from payload
      const order = data.included?.find((item: any) => item.type === 'orders')?.attributes ||
                    data.data?.attributes
      
      const transactionId = data.data?.id || order?.id || `tx_${Date.now()}`
      const amount = order?.total || data.data?.attributes?.total || 0
      const currency = order?.currency || data.data?.attributes?.currency || 'USD'
      const invoiceUrl = order?.urls?.receipt || data.data?.attributes?.urls?.receipt || null
      const status = order?.status === 'paid' || data.data?.attributes?.status === 'paid' ? 'succeeded' : 'pending'

      // Get final user_id (from backend API response if we called it, or from custom data)
      let finalUserId = userIdFromCustom

      // If we have user_id, insert payment transaction
      if (finalUserId && amount > 0) {
        const { error: insertError } = await supabase
          .from('payment_transactions')
          .insert({
            user_id: finalUserId,
            provider: 'lemonsqueezy',
            provider_transaction_id: transactionId,
            amount: Math.round(amount),  // Ensure integer (amount should already be in cents)
            currency: currency.toLowerCase(),
            status: status,
            invoice_url: invoiceUrl
          })

        if (insertError) {
          console.error('❌ [Webhook] Failed to insert payment transaction:', insertError.message)
          // Don't fail webhook - payment was successful, just logging failed
        } else {
          if (process.env.NODE_ENV === 'development') {
            console.log('✅ [Webhook] Recorded payment transaction:', {
              transaction_id: transactionId,
              amount: amount,
              currency: currency,
              status: status
            })
          }
        }
      }

      // Return success (payment transaction recorded)
      return NextResponse.json({
        received: true,
        message: 'Payment transaction recorded',
        event: eventName
      })
    } catch (error: any) {
      console.error('❌ [Webhook] Error processing payment event:', error)
      // Return success to prevent webhook retry (payment was successful, just logging failed)
      return NextResponse.json({
        received: true,
        message: 'Payment event processed with errors',
        error: error.message
      })
    }
  }

  // Handle subscription_created and other subscription events (existing logic)
  if (!subscription) {
    // For non-subscription events, just acknowledge receipt
    return NextResponse.json({
      received: true,
      message: 'Event received (not a subscription event)',
      event: eventName
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
  // CRITICAL: Lifetime plans should have NULL end_date
  const isLifetime = planType.includes('lifetime')
  const subscriptionEndDate = isLifetime ? null : (subscription.ends_at || subscription.renews_at || null)

    // Call backend API to update subscription
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 10000) // 10 second timeout

    try {
    const response = await fetch(`${backendUrl}/api/subscriptions/activate`, {
        method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
        body: JSON.stringify({
        user_id: userIdFromCustom || undefined,  // Primary: Use ID if available
        email: customerEmail || undefined,        // Fallback: Use email if ID not available
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
          console.warn(`⚠️ [Webhook] User not found in database`)
          if (userIdFromCustom) {
            console.warn(`⚠️ [Webhook] Attempted to find user by ID: ${userIdFromCustom}`)
          }
          if (customerEmail) {
            console.warn(`⚠️ [Webhook] Attempted to find user by email: ${customerEmail}`)
          }
          console.warn(`⚠️ [Webhook] Check:`)
          console.warn(`⚠️ [Webhook] 1. Does the user_id or email match a user in the database?`)
          console.warn(`⚠️ [Webhook] 2. Does the user exist in public.users table?`)
          return NextResponse.json({ 
            received: true, 
            pending_assignment: true,
            message: `User not found with ${userIdFromCustom ? `user_id: ${userIdFromCustom}` : `email: ${customerEmail}`} - logged for manual review`
          })
        }

      return NextResponse.json(
        { error: 'Backend API error', details: errorText },
        { status: 500 }
      )
      }

      const result = await response.json()

      // Log success in development
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ [Webhook] Subscription activated successfully:', {
          user_id_from_custom: userIdFromCustom,
          email: customerEmail,
          status: subscriptionStatus,
          plan: planType,
          matched_user_id: result.user_id
        })
      }

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
