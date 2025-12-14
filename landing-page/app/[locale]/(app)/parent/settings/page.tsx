'use client'

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
export default function SettingsPage() {
  const t = useTranslations('settings')
  const { user } = useAuth()
  const { profile } = useUserData()

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

