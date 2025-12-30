import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

/**
 * Billing Portal API Endpoint
 * 
 * Generates Lemon Squeezy customer portal URL dynamically (Billing Gateway Pattern).
 * This endpoint abstracts the payment provider, allowing us to swap providers without frontend changes.
 * 
 * GET /api/billing/portal
 */
export async function GET(request: NextRequest) {
  try {
    // Verify user authentication
    const supabase = await createClient()
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()

    if (sessionError || !session) {
      return NextResponse.json(
        { error: 'Unauthorized - please log in' },
        { status: 401 }
      )
    }

    const userId = session.user.id

    // Fetch user from database to get billing_customer_id and email
    const { data: user, error: userError } = await supabase
      .from('users')
      .select('id, email, billing_customer_id')
      .eq('id', userId)
      .single()

    if (userError || !user) {
      console.error('Failed to fetch user:', userError)
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      )
    }

    // Check if user has billing_customer_id
    let customerId = user.billing_customer_id

    // Self-healing: If customer_id is missing, look it up by email
    if (!customerId) {
      const apiKey = process.env.LEMON_SQUEEZY_API_KEY
      if (!apiKey) {
        return NextResponse.json(
          { error: 'Lemon Squeezy API key not configured' },
          { status: 500 }
        )
      }

      try {
        // Look up customer by email
        const lookupResponse = await fetch(
          `https://api.lemonsqueezy.com/v1/customers?filter[email]=${encodeURIComponent(user.email)}`,
          {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${apiKey}`,
              'Accept': 'application/vnd.api+json',
              'Content-Type': 'application/vnd.api+json'
            }
          }
        )

        if (!lookupResponse.ok) {
          const errorText = await lookupResponse.text()
          console.error('Lemon Squeezy customer lookup failed:', errorText)
          return NextResponse.json(
            { error: 'Failed to find customer in Lemon Squeezy. Please contact support.' },
            { status: 500 }
          )
        }

        const lookupData = await lookupResponse.json()
        const customers = lookupData.data || []

        if (customers.length === 0) {
          return NextResponse.json(
            { error: 'No customer found in Lemon Squeezy. You may not have made a payment yet.' },
            { status: 404 }
          )
        }

        // Use the first customer found
        customerId = customers[0].id

        // Update database with customer_id (self-healing)
        const { error: updateError } = await supabase
          .from('users')
          .update({ billing_customer_id: customerId })
          .eq('id', userId)

        if (updateError) {
          console.warn('Failed to update billing_customer_id:', updateError.message)
          // Continue anyway - we have the customer_id now
        } else {
          console.log('✅ Updated billing_customer_id for user:', userId)
        }
      } catch (error: any) {
        console.error('Error looking up customer:', error)
        return NextResponse.json(
          { error: 'Failed to connect to Lemon Squeezy. Please try again later.' },
          { status: 500 }
        )
      }
    }

    // Generate portal URL using customer_id
    // According to Lemon Squeezy docs:
    // 1. Store billing URL: https://[STORE].lemonsqueezy.com/billing
    // 2. Signed URLs: Available from customer_portal attribute in Subscription/Customer API response
    const apiKey = process.env.LEMON_SQUEEZY_API_KEY
    if (!apiKey) {
      return NextResponse.json(
        { error: 'Lemon Squeezy API key not configured' },
        { status: 500 }
      )
    }

    // Try to get signed URL from customer's subscriptions (if available)
    // For lifetime purchases (one-time), there are no subscriptions, so we'll use the store billing URL
    try {
      // Fetch customer details to get signed portal URL
      const customerResponse = await fetch(
        `https://api.lemonsqueezy.com/v1/customers/${customerId}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json'
          }
        }
      )

      if (customerResponse.ok) {
        const customerData = await customerResponse.json()
        // Check if customer has a signed portal URL
        const signedPortalUrl = customerData.data?.attributes?.urls?.customer_portal
        if (signedPortalUrl) {
          console.log('✅ Found signed portal URL for customer:', customerId)
          return NextResponse.json({
            portal_url: signedPortalUrl
          })
        } else {
          console.warn('⚠️ Customer API response OK but no signed portal URL found')
        }
      } else {
        const errorText = await customerResponse.text()
        console.error('❌ Customer API failed:', customerResponse.status, errorText)
      }
    } catch (error: any) {
      console.error('❌ Error fetching signed portal URL:', error.message)
      // Continue to fallback
    }

    // Fallback: Use store billing URL
    // Store subdomain: lexicraft-xyz (from campaign-config.ts)
    // NOTE: If store is not activated, this will show an error
    // Users should contact support or activate the store in Lemon Squeezy dashboard
    const portalUrl = 'https://lexicraft-xyz.lemonsqueezy.com/billing'

    return NextResponse.json({
      portal_url: portalUrl,
      message: 'If you see a "store not activated" error, please contact support. The store needs to be activated in the Lemon Squeezy dashboard.'
    })
  } catch (error: any) {
    console.error('Unexpected error in portal endpoint:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

