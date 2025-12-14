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
    // Minimum NT$50 (Stripe minimum ~$0.50 USD ≈ NT$15, but we set NT$50 for safety)
    // Maximum NT$10,000 for fraud protection
    if (!amount || amount < 50 || amount > 10000) {
      return NextResponse.json(
        { error: 'Amount must be between NT$50 and NT$10,000' },
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
    
    // Determine product name based on amount
    const isEmojiPack = amount === 99
    const productName = isEmojiPack 
      ? 'LexiCraft 表情學英文 - 6個月暢玩' 
      : 'LexiCraft 學習點數儲值'
    const productDescription = isEmojiPack
      ? '200個表情符號單字・6個月無限練習'
      : 'Deposit for vocabulary learning rewards'
    
    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'twd',
            product_data: {
              name: productName,
              description: productDescription,
            },
            unit_amount: amount * 100, // Convert NT$ to cents
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${origin}/${locale}/parent/dashboard?success=true&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/${locale}/emoji-fun?canceled=true`,
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

