import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'

/**
 * Create Stripe Checkout Session for deposit
 * 
 * POST /api/deposits/create-checkout
 * Body: { amount: number, learnerId: string, userId: string }
 */
export async function POST(request: NextRequest) {
  try {
    // Initialize Stripe inside the handler (not at module level)
    // This prevents build-time errors when env vars aren't available
    const stripeSecretKey = process.env.STRIPE_SECRET_KEY
    if (!stripeSecretKey) {
      return NextResponse.json(
        { error: 'STRIPE_SECRET_KEY is not configured' },
        { status: 500 }
      )
    }
    
    const stripe = new Stripe(stripeSecretKey)
    const { amount, learnerId, userId } = await request.json()  // Changed from childId
    
    // Validate input
    if (!amount || amount < 500 || amount > 10000) {
      return NextResponse.json(
        { error: 'Amount must be between NT$500 and NT$10,000' },
        { status: 400 }
      )
    }
    
    if (!learnerId || !userId) {
      return NextResponse.json(
        { error: 'learnerId and userId are required' },
        { status: 400 }
      )
    }
    
    // Get origin and locale for redirect URLs
    const origin = request.headers.get('origin') || 'http://localhost:3000'
    const referer = request.headers.get('referer') || ''
    // Extract locale from referer URL (e.g., /zh-TW/dashboard)
    const localeMatch = referer.match(/\/([a-z]{2}(?:-[A-Z]{2})?)\//i)
    const locale = localeMatch ? localeMatch[1] : 'zh-TW'
    
    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'twd',
            product_data: {
              name: 'lexicraft.xyz Block Trust Package',
              description: 'Deposit for vocabulary learning rewards',
            },
            unit_amount: amount * 100, // Convert NT$ to cents
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${origin}/${locale}/dashboard?success=true&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/${locale}/dashboard?canceled=true`,
      metadata: {
        learner_id: learnerId,  // Changed from child_id
        user_id: userId,
        amount: amount.toString(),
      },
      // Taiwan-specific settings
      locale: 'zh-TW',
      payment_intent_data: {
        description: `lexicraft.xyz deposit for learner ${learnerId}`,
      },
    })

    return NextResponse.json({ 
      url: session.url,
      sessionId: session.id 
    })
  } catch (error: any) {
    console.error('Error creating checkout session:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to create checkout session' },
      { status: 500 }
    )
  }
}

