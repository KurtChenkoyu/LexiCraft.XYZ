'use client'

import { useState } from 'react'
import { getStripe } from '@/lib/stripe'

interface DepositButtonProps {
  amount: number // in NT$
  learnerId: string  // Changed from childId
  userId: string
  className?: string
}

/**
 * Deposit Button Component
 * 
 * Creates a Stripe checkout session and redirects to payment
 */
export function DepositButton({ 
  amount, 
  learnerId,  // Changed from childId
  userId,
  className = '' 
}: DepositButtonProps) {
  const [loading, setLoading] = useState(false)

  const handleDeposit = async () => {
    try {
      setLoading(true)
      
      const response = await fetch('/api/deposits/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          amount, 
          learnerId,  // Changed from childId
          userId 
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to create checkout')
      }

      const { url } = await response.json()
      
      if (url) {
        // Redirect to Stripe Checkout
        window.location.href = url
      } else {
        throw new Error('No checkout URL returned')
      }
    } catch (error: any) {
      console.error('Error creating checkout:', error)
      alert(`付款失敗: ${error.message || '請稍後再試'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleDeposit}
      disabled={loading || !amount || !learnerId || !userId}
      className={`
        px-6 py-3 
        bg-gradient-to-r from-cyan-600 to-blue-600 
        text-white font-semibold 
        rounded-lg 
        hover:from-cyan-700 hover:to-blue-700 
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          處理中...
        </span>
      ) : (
        `存入 NT$${amount.toLocaleString()}`
      )}
    </button>
  )
}

