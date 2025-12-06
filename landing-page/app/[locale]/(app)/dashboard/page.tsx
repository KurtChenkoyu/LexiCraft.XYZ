'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/contexts/UserDataContext'
import { EmailConfirmationBanner } from '@/components/features/auth/EmailConfirmationBanner'
import { GamificationWidget } from '@/components/features/gamification/GamificationWidget'
import {
  PaymentAlerts,
  ChildrenOverview,
  VerificationCard,
  BalanceCard,
  QuickActions,
  HowItWorks,
  DepositSection,
} from '@/components/features/dashboard'
import { Link } from '@/i18n/routing'

export default function DashboardPage() {
  const t = useTranslations('dashboard')
  const searchParams = useSearchParams()
  const { user } = useAuth()
  const { 
    children, 
    selectedChildId, 
    selectChild, 
    balance, 
    isLoading: dataLoading,
    isSyncing,
    refreshAll,
    triggerSync,
    profile,
  } = useUserData()
  
  const [apiError, setApiError] = useState(false)
  
  const [showSuccess, setShowSuccess] = useState(false)
  const [showCancel, setShowCancel] = useState(false)

  // Handle Stripe redirect messages
  useEffect(() => {
    const success = searchParams.get('success')
    const canceled = searchParams.get('canceled')

    if (success === 'true') {
      setShowSuccess(true)
      refreshAll()
      setTimeout(() => setShowSuccess(false), 5000)
    }

    if (canceled === 'true') {
      setShowCancel(true)
      setTimeout(() => setShowCancel(false), 5000)
    }
  }, [searchParams, refreshAll])

  // Check if API is available (if loading finishes but no profile, API might be down)
  useEffect(() => {
    if (!dataLoading && !profile && user) {
      // API might be unavailable
      const timer = setTimeout(() => {
        setApiError(true)
      }, 2000)
      return () => clearTimeout(timer)
    } else if (profile) {
      setApiError(false)
    }
  }, [dataLoading, profile, user])

  // Get user ID for deposit form (user is guaranteed by layout)
  const userId = user?.id || ''

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <EmailConfirmationBanner />
        
        <PaymentAlerts
          showSuccess={showSuccess}
          showCancel={showCancel}
          onDismissSuccess={() => setShowSuccess(false)}
          onDismissCancel={() => setShowCancel(false)}
        />

        {/* API Error Banner */}
        {apiError && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-8">
            <div className="flex items-start gap-4">
              <div className="text-3xl">⚠️</div>
              <div className="flex-1">
                <h3 className="font-bold text-amber-800 mb-1">後端服務未連線</h3>
                <p className="text-amber-700 text-sm mb-3">
                  無法連接到 API 伺服器，部分功能可能無法使用。
                </p>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => {
                      setApiError(false)
                      triggerSync()
                    }}
                    disabled={isSyncing}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors inline-flex items-center gap-2"
                  >
                    {isSyncing ? (
                      <>
                        <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        同步中...
                      </>
                    ) : (
                      '重新連線'
                    )}
                  </button>
                  <Link
                    href="/mine"
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    前往礦區 (離線可用)
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">{t('title')}</h1>
          <p className="text-xl text-gray-600">{t('subtitle')}</p>
          
          {/* Sync Status Indicator */}
          {isSyncing && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-cyan-50 text-cyan-700 rounded-full text-sm">
              <div className="w-3 h-3 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              <span>同步中...</span>
            </div>
          )}
        </div>

        <ChildrenOverview
          children={children}
          selectedChildId={selectedChildId}
          onSelectChild={selectChild}
          isLoading={dataLoading}
        />

        {/* Dashboard Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Verification Card - Quick Access */}
          <div className="lg:col-span-1 order-2 lg:order-1">
            <VerificationCard />
          </div>

          {/* Main Content - Deposit Form */}
          <div className="lg:col-span-2 order-1 lg:order-2">
            <DepositSection
              children={children}
              selectedChildId={selectedChildId}
              onSelectChild={selectChild}
              userId={userId}
              isLoading={dataLoading}
            />

            <BalanceCard
              availablePoints={balance.available_points}
              lockedPoints={balance.locked_points}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <GamificationWidget />
            <QuickActions />
            <HowItWorks />
          </div>
        </div>
      </div>
    </main>
  )
}
