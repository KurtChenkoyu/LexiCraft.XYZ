'use client'

/**
 * App Layout for authenticated pages
 * 
 * ⚡ ARCHITECTURE PRINCIPLE: "As Snappy as Last War"
 * See: /docs/ARCHITECTURE_PRINCIPLES.md
 * 
 * - Pages should render UI INSTANTLY (no loading spinners for content)
 * - Use default/empty states, fetch in background
 * - Offline is valid, not an error
 */

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { checkOnboardingStatus } from '@/lib/onboarding'
import { MobileShell } from '@/components/layout/MobileShell'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, loading } = useAuth()
  const [onboardingChecked, setOnboardingChecked] = useState(false)

  // Get locale from pathname
  const locale = pathname.split('/')[1] || 'zh-TW'

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push(`/${locale}/login`)
    }
  }, [user, loading, router, locale])

  // Check onboarding status (skip if already on onboarding page)
  useEffect(() => {
    const checkOnboarding = async () => {
      if (!loading && user && !onboardingChecked) {
        // Skip check if already on onboarding page
        if (pathname.includes('/onboarding')) {
          setOnboardingChecked(true)
          return
        }

        try {
          const status = await checkOnboardingStatus(user.id)
          if (status && !status.completed) {
            router.push(`/${locale}/onboarding`)
          }
        } catch (error) {
          console.error('Onboarding check failed:', error)
        }
        setOnboardingChecked(true)
      }
    }

    if (user && !loading) {
      checkOnboarding()
    }
  }, [user, loading, router, locale, pathname, onboardingChecked])

  // Show loading state
  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-600 mx-auto mb-4"></div>
          <p className="text-gray-600">載入中...</p>
        </div>
      </main>
    )
  }

  // Don't render if not authenticated (will redirect)
  if (!user) {
    return null
  }

  return <MobileShell>{children}</MobileShell>
}

