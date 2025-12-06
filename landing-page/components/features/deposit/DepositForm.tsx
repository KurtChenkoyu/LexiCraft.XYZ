'use client'

import { useState } from 'react'
import { DepositButton } from './DepositButton'

interface DepositFormProps {
  learnerId: string  // Changed from childId
  userId: string
  onSuccess?: () => void
}

/**
 * Deposit Form Component
 * 
 * Allows parents to select deposit amount and process payment
 */
export function DepositForm({ learnerId, userId, onSuccess }: DepositFormProps) {
  const [selectedAmount, setSelectedAmount] = useState<number>(1000)
  const [customAmount, setCustomAmount] = useState<string>('')

  const presetAmounts = [500, 1000, 2000, 5000]

  const handleCustomAmount = (value: string) => {
    const num = parseInt(value)
    if (!isNaN(num) && num >= 500 && num <= 10000) {
      setSelectedAmount(num)
      setCustomAmount(value)
    } else {
      setCustomAmount(value)
    }
  }

  const finalAmount = customAmount && !isNaN(parseInt(customAmount))
    ? parseInt(customAmount)
    : selectedAmount

  return (
    <div className="bg-white rounded-xl p-8 shadow-lg max-w-md mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        存入信託資金
      </h2>
      
      <p className="text-gray-600 mb-6">
        選擇存入金額，資金將存入信託帳戶，孩子學習後可解鎖提領。
      </p>

      {/* Preset Amounts */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {presetAmounts.map((amount) => (
          <button
            key={amount}
            onClick={() => {
              setSelectedAmount(amount)
              setCustomAmount('')
            }}
            className={`
              px-4 py-3 rounded-lg border-2 transition-colors
              ${
                selectedAmount === amount && !customAmount
                  ? 'border-cyan-600 bg-cyan-50 text-cyan-700 font-semibold'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }
            `}
          >
            NT${amount.toLocaleString()}
          </button>
        ))}
      </div>

      {/* Custom Amount */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          自訂金額 (NT$500 - NT$10,000)
        </label>
        <input
          type="number"
          min="500"
          max="10000"
          step="100"
          value={customAmount}
          onChange={(e) => handleCustomAmount(e.target.value)}
          placeholder="輸入金額"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
        />
      </div>

      {/* Deposit Button */}
      <DepositButton
        amount={finalAmount}
        learnerId={learnerId}
        userId={userId}
        className="w-full"
      />

      {/* Info */}
      <p className="text-xs text-gray-500 mt-4 text-center">
        7天內可申請全額退款（消費者保護法）
      </p>
    </div>
  )
}

