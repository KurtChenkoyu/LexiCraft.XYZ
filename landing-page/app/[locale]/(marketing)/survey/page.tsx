'use client'

/**
 * Public Survey Page - Accessible to first-time visitors
 * 
 * This route is in the (marketing) group, so it's accessible without authentication.
 * It handles both authenticated and unauthenticated users:
 * - Unauthenticated: Uses anonymous mode (cold-start)
 * - Authenticated: Can use warm-start mode with prior knowledge
 */

import React, { useCallback } from 'react'
import { usePathname } from '@/i18n/routing'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import SurveyEngine from '@/components/features/survey/SurveyEngine'

export default function PublicSurveyPage() {
  const router = useRouter()
  const pathname = usePathname()
  const { user, loading: authLoading } = useAuth()

  const locale = pathname.split('/')[1] || 'zh-TW'

  // Handle exit - redirect based on auth status
  const handleExit = useCallback(() => {
    if (user) {
      // Authenticated user → go to dashboard
      router.push(`/${locale}/dashboard`)
    } else {
      // Unauthenticated user → go to signup (with survey results)
      router.push(`/${locale}/signup?from=survey`)
    }
  }, [user, router, locale])

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-600 mx-auto mb-4"></div>
          <p className="text-gray-400">載入中...</p>
        </div>
      </main>
    )
  }

  // SurveyEngine handles both authenticated and unauthenticated users
  // userId is optional - if not provided, backend uses ANONYMOUS_USER_ID
  return (
    <main className="min-h-screen bg-gray-950">
      <SurveyEngine 
        onExit={handleExit}
        userId={user?.id} // Optional - undefined for anonymous users
      />
    </main>
  )
}

