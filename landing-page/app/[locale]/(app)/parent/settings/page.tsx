'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/contexts/UserDataContext'

/**
 * Parent Settings Page
 * 
 * Account settings for parents.
 * 
 * URL: /parent/settings
 */
interface PaymentTransaction {
  id: string
  provider: string
  provider_transaction_id: string
  amount: number
  currency: string
  status: string
  invoice_url: string | null
  created_at: string
}

export default function SettingsPage() {
  const t = useTranslations('settings')
  const { user } = useAuth()
  const { profile, refreshProfile } = useUserData()
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [loadingPortal, setLoadingPortal] = useState(false)
  const [portalError, setPortalError] = useState<string | null>(null)

  // Refresh profile on mount to get latest subscription status
  useEffect(() => {
    refreshProfile()
  }, [refreshProfile])

  // Fetch payment history
  useEffect(() => {
    const fetchHistory = async () => {
      setLoadingHistory(true)
      try {
        const response = await fetch('/api/billing/history')
        if (response.ok) {
          const data = await response.json()
          setTransactions(data.transactions || [])
        }
      } catch (error) {
        console.error('Failed to fetch payment history:', error)
      } finally {
        setLoadingHistory(false)
      }
    }

    fetchHistory()
  }, [])

  // Handle "Manage Subscription" button click
  const handleManageSubscription = async () => {
    setLoadingPortal(true)
    setPortalError(null)
    try {
      const response = await fetch('/api/billing/portal')
      if (!response.ok) {
        const error = await response.json()
        setPortalError(error.error || 'Failed to open subscription portal')
        return
      }
      const data = await response.json()
      if (data.portal_url) {
        window.open(data.portal_url, '_blank', 'noopener,noreferrer')
      } else {
        setPortalError('Portal URL not found')
      }
    } catch (error: any) {
      console.error('Failed to get portal URL:', error)
      setPortalError('Failed to connect to billing portal. Please try again later.')
    } finally {
      setLoadingPortal(false)
    }
  }

  // Format subscription status display
  const getSubscriptionStatusDisplay = () => {
    if (!profile?.subscription_status) {
      return { text: '未訂閱', color: 'bg-gray-100 text-gray-700' }
    }
    switch (profile.subscription_status) {
      case 'active':
        return { text: '已啟用', color: 'bg-green-100 text-green-700' }
      case 'trial':
        return { text: '試用中', color: 'bg-blue-100 text-blue-700' }
      case 'past_due':
        return { text: '逾期', color: 'bg-amber-100 text-amber-700' }
      case 'inactive':
      case 'cancelled':
      case 'expired':
        return { text: '已取消', color: 'bg-gray-100 text-gray-700' }
      default:
        return { text: profile.subscription_status, color: 'bg-gray-100 text-gray-700' }
    }
  }

  // Format plan type display
  const getPlanTypeDisplay = () => {
    if (!profile?.plan_type) return '未設定'
    const planMap: Record<string, string> = {
      'lifetime': 'Emoji 永久方案',
      'lifetime-pass': 'Emoji 永久方案', // Add this mapping
      '6-month-pass': '6個月方案',
      '12-month-pass': '12個月方案',
      'monthly': '月付方案',
      'yearly': '年付方案'
    }
    return planMap[profile.plan_type] || profile.plan_type
  }

  // Format date display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  // Format amount display
  const formatAmount = (amount: number, currency: string) => {
    const dollars = (amount / 100).toFixed(2)
    return `${currency === 'USD' ? '$' : currency} ${dollars}`
  }

  const statusDisplay = getSubscriptionStatusDisplay()

  // ALWAYS render UI - never loading state
  return (
    <>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('title')}</h1>
        <p className="text-gray-600">{t('subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Account Info */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {t('account.title')}
            </h2>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-600">{t('account.email')}</span>
                <span className="font-medium text-gray-900">{profile?.email || user?.email}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-600">{t('account.name')}</span>
                <span className="font-medium text-gray-900">{profile?.name || '未設定'}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-600">{t('account.age')}</span>
                <span className="font-medium text-gray-900">{profile?.age ? `${profile.age} 歲` : '未設定'}</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-gray-600">{t('account.roles')}</span>
                <div className="flex gap-2">
                  {profile?.roles?.map((role) => (
                    <span
                      key={role}
                      className="px-3 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm font-medium"
                    >
                      {role === 'parent' ? '家長' : role === 'learner' ? '學習者' : role}
                    </span>
                  )) || <span className="text-gray-500">-</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Subscription & Billing */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              訂閱與付款
            </h2>

            {/* Subscription Status */}
            <div className="space-y-4 mb-6">
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-600">訂閱狀態</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusDisplay.color}`}>
                  {statusDisplay.text}
                </span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-600">方案類型</span>
                <span className="font-medium text-gray-900">{getPlanTypeDisplay()}</span>
              </div>
              {profile?.subscription_end_date && (
                <div className="flex justify-between items-center py-3 border-b border-gray-100">
                  <span className="text-gray-600">到期日期</span>
                  <span className="font-medium text-gray-900">
                    {new Date(profile.subscription_end_date).toLocaleDateString('zh-TW', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
              )}
              <div className="pt-4">
                <button
                  onClick={handleManageSubscription}
                  disabled={loadingPortal}
                  className="w-full px-4 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                >
                  {loadingPortal ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      載入中...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      管理訂閱
                    </>
                  )}
                </button>
                {portalError && (
                  <div className="mt-2 text-sm text-red-600">{portalError}</div>
                )}
              </div>
            </div>

            {/* Payment History */}
            <div className="mt-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">付款記錄</h3>
              {loadingHistory ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-cyan-600 border-t-transparent rounded-full animate-spin" />
                  <span className="ml-2 text-gray-600">載入中...</span>
                </div>
              ) : transactions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>尚無付款記錄</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">日期</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">金額</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">狀態</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">發票</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((tx) => (
                        <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-gray-900">{formatDate(tx.created_at)}</td>
                          <td className="py-3 px-4 text-sm text-gray-900">{formatAmount(tx.amount, tx.currency)}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              tx.status === 'succeeded' 
                                ? 'bg-green-100 text-green-700'
                                : tx.status === 'pending'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}>
                              {tx.status === 'succeeded' ? '成功' : tx.status === 'pending' ? '處理中' : tx.status}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            {tx.invoice_url ? (
                              <a
                                href={tx.invoice_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-cyan-600 hover:text-cyan-700 text-sm font-medium"
                              >
                                下載
                              </a>
                            ) : (
                              <span className="text-gray-400 text-sm">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Children Management Link */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 mb-2">
                  <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  {t('children.title')}
                </h2>
                <p className="text-gray-600 text-sm">管理您孩子的學習帳戶</p>
              </div>
              <Link
                href="/parent/children"
                className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors font-medium flex items-center gap-2"
              >
                前往管理
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Account Status */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">帳戶狀態</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">電子郵件驗證</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  profile?.email_confirmed 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-amber-100 text-amber-700'
                }`}>
                  {profile?.email_confirmed ? '已驗證' : '未驗證'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">{t('quickActions.title')}</h3>
            <div className="space-y-3">
              <Link
                href="/parent/dashboard"
                className="block w-full px-4 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors text-center font-semibold"
              >
                {t('quickActions.dashboard')}
              </Link>
              <Link
                href="/survey"
                className="block w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-center font-semibold"
              >
                {t('quickActions.survey')}
              </Link>
              <Link
                href="/"
                className="block w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-center font-semibold"
              >
                {t('quickActions.home')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

