'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const router = useRouter()

  useEffect(() => {
    // Log the error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('App Error:', error)
    }
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-xl p-6 text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold text-white mb-2">發生錯誤</h2>
        <p className="text-slate-400 mb-6">
          很抱歉，頁面載入時發生問題。請重新整理頁面或返回首頁。
        </p>
        {process.env.NODE_ENV === 'development' && (
          <details className="mb-6 text-left">
            <summary className="text-sm text-slate-500 cursor-pointer mb-2">錯誤詳情</summary>
            <pre className="mt-2 text-xs text-red-400 overflow-auto bg-slate-900 p-3 rounded">
              {error.message}
              {error.stack && `\n\n${error.stack}`}
            </pre>
          </details>
        )}
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-cyan-600 text-white rounded-lg font-semibold hover:bg-cyan-500 transition-colors"
          >
            重試
          </button>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-slate-700 text-white rounded-lg font-semibold hover:bg-slate-600 transition-colors"
          >
            返回首頁
          </button>
        </div>
      </div>
    </div>
  )
}


