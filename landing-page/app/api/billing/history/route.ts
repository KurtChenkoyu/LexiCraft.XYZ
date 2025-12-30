import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

/**
 * Payment History API Endpoint
 * 
 * Returns user's payment transaction history from local ledger.
 * This implements the "Local Ledger Pattern" - we maintain our own payment history
 * independent of the payment provider.
 * 
 * GET /api/billing/history
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

    // Get pagination parameters (optional)
    const searchParams = request.nextUrl.searchParams
    const limit = parseInt(searchParams.get('limit') || '50', 10)
    const offset = parseInt(searchParams.get('offset') || '0', 10)

    // Query payment_transactions table
    const { data: transactions, error: queryError } = await supabase
      .from('payment_transactions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (queryError) {
      console.error('Failed to fetch payment transactions:', queryError)
      return NextResponse.json(
        { error: 'Failed to fetch payment history' },
        { status: 500 }
      )
    }

    // Format transactions for response
    const formattedTransactions = (transactions || []).map((tx: any) => ({
      id: tx.id,
      provider: tx.provider,
      provider_transaction_id: tx.provider_transaction_id,
      amount: tx.amount,  // in cents
      currency: tx.currency,
      status: tx.status,
      invoice_url: tx.invoice_url,
      created_at: tx.created_at
    }))

    return NextResponse.json({
      transactions: formattedTransactions,
      count: formattedTransactions.length,
      limit,
      offset
    })
  } catch (error: any) {
    console.error('Unexpected error in history endpoint:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

