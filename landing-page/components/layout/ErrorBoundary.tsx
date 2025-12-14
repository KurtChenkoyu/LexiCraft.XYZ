'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    // Log to analytics if available
    if (typeof window !== 'undefined' && (window as any).gtag) {
      ;(window as any).gtag('event', 'exception', {
        description: error.toString(),
        fatal: false,
      })
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-cosmic-950 p-4">
          <div className="max-w-md w-full bg-slate-900 border border-white/10 rounded-xl p-6 text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-bold text-white mb-2">發生錯誤</h2>
            <p className="text-slate-400 mb-6">
              很抱歉，頁面載入時發生問題。請重新整理頁面或返回首頁。
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-neon-cyan text-cosmic-950 rounded-lg font-semibold hover:bg-cyan-300 transition-colors"
              >
                重新整理
              </button>
              <a
                href="/"
                className="px-4 py-2 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition-colors"
              >
                返回首頁
              </a>
            </div>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 text-left">
                <summary className="text-sm text-slate-500 cursor-pointer">錯誤詳情</summary>
                <pre className="mt-2 text-xs text-red-400 overflow-auto">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary


