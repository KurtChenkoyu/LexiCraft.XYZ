'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { useUserData } from '@/contexts/UserDataContext'

/**
 * Children Management Page
 * 
 * Manage child accounts for parents.
 * 
 * URL: /parent/children
 */
export default function ChildrenPage() {
  const t = useTranslations('settings')
  const { 
    children, 
    isLoading: dataLoading,
    addChild,
    refreshChildren
  } = useUserData()

  // Ensure children are loaded when page mounts
  useEffect(() => {
    if (!dataLoading && children.length === 0) {
      refreshChildren()
    }
  }, [dataLoading, children.length, refreshChildren])
  
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

  // Always render UI - never loading state
  return (
    <>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">孩子管理</h1>
        <p className="text-gray-600">管理您孩子的學習帳戶</p>
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

      {/* Add Child Button */}
      {!showCreateChild && (
        <div className="mb-6">
          <button
            onClick={() => setShowCreateChild(true)}
            className="px-6 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors font-medium flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            {t('children.addChild')}
          </button>
        </div>
      )}

      {/* Create Child Form */}
      {showCreateChild && (
        <div className="mb-6 bg-cyan-50 rounded-lg border border-cyan-200 p-6">
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
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <p className="text-gray-600 mb-2">{t('children.noChildren')}</p>
          <p className="text-sm text-gray-500">{t('children.noChildrenHint')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {children.map((child) => (
            <div
              key={child.id}
              className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 hover:border-cyan-300 transition-colors"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                  {(child.name || '?')[0].toUpperCase()}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 text-lg">
                    {child.name || '未命名'}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {child.age ? `${child.age} 歲` : '年齡未設定'}
                  </p>
                </div>
              </div>
              
              <div className="space-y-2">
                <Link
                  href="/parent/dashboard/analytics"
                  className="block w-full px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors text-center font-medium"
                >
                  查看學習分析
                </Link>
                <Link
                  href="/survey"
                  className="block w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-center font-medium"
                >
                  開始測驗
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

