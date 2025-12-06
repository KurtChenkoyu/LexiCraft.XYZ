'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/contexts/UserDataContext'

export default function SettingsPage() {
  const t = useTranslations('settings')
  const { user } = useAuth()
  const { 
    profile, 
    children, 
    isLoading: dataLoading,
    addChild,
    refreshChildren
  } = useUserData()
  
  // Create child form
  const [showCreateChild, setShowCreateChild] = useState(false)
  const [childName, setChildName] = useState('')
  const [childAge, setChildAge] = useState('')
  const [creatingChild, setCreatingChild] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const handleCreateChild = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!childName || !childAge) return
    
    setCreatingChild(true)
    setErrorMessage('')
    
    try {
      await addChild(childName, parseInt(childAge))
      
      setShowCreateChild(false)
      setChildName('')
      setChildAge('')
      setSuccessMessage('孩子帳戶建立成功！')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (error: any) {
      console.error('Failed to create child:', error)
      setErrorMessage(error.response?.data?.detail || '建立失敗，請重試')
    } finally {
      setCreatingChild(false)
    }
  }

  // Loading state
  if (dataLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-600 mx-auto mb-4"></div>
          <p className="text-gray-600">載入中...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
            <p className="text-gray-600 mt-1">{t('subtitle')}</p>
          </div>
          <Link
            href="/dashboard"
            className="px-4 py-2 text-cyan-600 hover:text-cyan-700 font-medium flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            {t('backToDashboard')}
          </Link>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-lg flex items-center">
            <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold">{successMessage}</span>
          </div>
        )}

        {/* Error Message */}
        {errorMessage && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-6 py-4 rounded-lg flex items-center">
            <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold">{errorMessage}</span>
          </div>
        )}

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

            {/* Children Management */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  {t('children.title')}
                </h2>
                {!showCreateChild && (
                  <button
                    onClick={() => setShowCreateChild(true)}
                    className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors font-medium flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    {t('children.addChild')}
                  </button>
                )}
              </div>

              {/* Create Child Form */}
              {showCreateChild && (
                <div className="mb-6 p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('children.createTitle')}</h3>
                  <form onSubmit={handleCreateChild} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('children.childName')}
                      </label>
                      <input
                        type="text"
                        value={childName}
                        onChange={(e) => setChildName(e.target.value)}
                        required
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900"
                        placeholder="孩子的名字"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('children.childAge')}
                      </label>
                      <input
                        type="number"
                        value={childAge}
                        onChange={(e) => setChildAge(e.target.value)}
                        required
                        min={1}
                        max={19}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900"
                        placeholder="5"
                      />
                      <p className="mt-2 text-sm text-gray-600">{t('children.ageHint')}</p>
                    </div>
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => {
                          setShowCreateChild(false)
                          setChildName('')
                          setChildAge('')
                          setErrorMessage('')
                        }}
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700 font-medium"
                      >
                        {t('children.cancel')}
                      </button>
                      <button
                        type="submit"
                        disabled={creatingChild || !childName || !childAge}
                        className="flex-1 px-4 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
                      >
                        {creatingChild ? t('children.creating') : t('children.create')}
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Children List */}
              {children.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <p className="text-gray-600 mb-2">{t('children.noChildren')}</p>
                  <p className="text-sm text-gray-500">{t('children.noChildrenHint')}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {children.map((child) => (
                    <div
                      key={child.id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-cyan-300 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                          {(child.name || '?')[0].toUpperCase()}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 text-lg">
                            {child.name || '未命名'}
                          </h3>
                          <p className="text-gray-600 text-sm">
                            {child.age ? `${child.age} 歲` : '年齡未設定'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                          學習者
                        </span>
                        <Link
                          href="/survey"
                          className="px-3 py-1.5 text-cyan-600 hover:bg-cyan-50 rounded-lg text-sm font-medium transition-colors"
                        >
                          開始測驗 →
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">{t('stats.title')}</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">{t('stats.totalChildren')}</span>
                  <span className="text-2xl font-bold text-cyan-600">{children.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">{t('stats.accountStatus')}</span>
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
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
                  href="/dashboard"
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
      </div>
    </main>
  )
}
