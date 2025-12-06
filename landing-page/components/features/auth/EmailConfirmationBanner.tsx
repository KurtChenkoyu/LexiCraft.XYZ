'use client'

import { useAuth } from '@/contexts/AuthContext'
import { createClient } from '@/lib/supabase/client'
import { useState } from 'react'

export function EmailConfirmationBanner() {
  const { user, refreshUser } = useAuth()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const supabase = createClient()

  // Check if user needs to confirm email
  // Supabase uses email_confirmed_at (timestamp) - null means not confirmed
  // In production, you'd also check the users table email_confirmed field
  const needsConfirmation = user && !user.email_confirmed_at

  if (!needsConfirmation) {
    return null
  }

  const handleResendConfirmation = async () => {
    setLoading(true)
    setMessage(null)

    try {
      const { error } = await supabase.auth.resend({
        type: 'signup',
        email: user?.email || '',
      })

      if (error) throw error

      setMessage('確認郵件已重新發送，請檢查您的收件匣。')
    } catch (error: any) {
      setMessage(error.message || '發送失敗，請重試')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            請確認您的電子郵件地址
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>
              為了啟用提款功能，請確認您的電子郵件地址。我們已發送確認郵件至 <strong>{user?.email}</strong>
            </p>
          </div>
          <div className="mt-4">
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={handleResendConfirmation}
                disabled={loading}
                className="text-sm font-medium text-yellow-800 hover:text-yellow-900 underline disabled:opacity-50"
              >
                {loading ? '發送中...' : '重新發送確認郵件'}
              </button>
            </div>
            {message && (
              <p className="mt-2 text-sm text-yellow-600">{message}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

