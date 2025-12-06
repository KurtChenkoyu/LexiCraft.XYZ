'use client'

interface PaymentAlertsProps {
  showSuccess: boolean
  showCancel: boolean
  onDismissSuccess: () => void
  onDismissCancel: () => void
}

export function PaymentAlerts({
  showSuccess,
  showCancel,
  onDismissSuccess,
  onDismissCancel,
}: PaymentAlertsProps) {
  if (!showSuccess && !showCancel) return null

  return (
    <>
      {showSuccess && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold">付款成功！您的存款已確認。</span>
          </div>
          <button onClick={onDismissSuccess} className="text-green-600 hover:text-green-800">✕</button>
        </div>
      )}

      {showCancel && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 text-yellow-800 px-6 py-4 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>付款已取消。您可以隨時重新嘗試。</span>
          </div>
          <button onClick={onDismissCancel} className="text-yellow-600 hover:text-yellow-800">✕</button>
        </div>
      )}
    </>
  )
}

