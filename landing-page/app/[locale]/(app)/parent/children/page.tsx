'use client'

import { useState, useEffect, useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { useUserData } from '@/contexts/UserDataContext'
import { createAuthenticatedClient } from '@/lib/api-client'
import { useAppStore, selectLearners } from '@/stores/useAppStore'

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
  const learners = useAppStore(selectLearners)
  // Memoize child learners to prevent infinite loops
  const childLearners = useMemo(() => 
    learners.filter(l => !l.is_parent_profile),
    [learners]
  )

  // Ensure children are loaded when page mounts
  useEffect(() => {
    if (!dataLoading && children.length === 0) {
      refreshChildren()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataLoading, children.length])
  
  // Create child form
  const [showCreateChild, setShowCreateChild] = useState(false)
  const [childName, setChildName] = useState('')
  const [childAge, setChildAge] = useState('')
  const [creatingChild, setCreatingChild] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [backfilling, setBackfilling] = useState(false)

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

  const handleBackfillLearners = async () => {
    setBackfilling(true)
    setErrorMessage('')
    setSuccessMessage('')
    
    try {
      console.log('🔄 Starting backfill...')
      const client = await createAuthenticatedClient()
      const response = await client.post('/api/users/me/learners/backfill')
      
      console.log('✅ Backfill API response:', response.data)
      const result = response.data
      
      if (result.created_count > 0) {
        setSuccessMessage(`成功建立 ${result.created_count} 個學習者檔案！`)
        setTimeout(() => setSuccessMessage(''), 5000)
        
        // Wait a moment for database transaction to be fully committed and visible
        console.log('⏳ Waiting for transaction to commit...')
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // Force refresh learners from API (bypass cache) using downloadService
        console.log('🔄 Force refreshing learners from API...')
        const { downloadService } = await import('@/services/downloadService')
        const freshLearners = await downloadService.refreshLearners()
        
        console.log(`📥 Fresh learners received: ${freshLearners.length}`)
        
        if (freshLearners.length > 0) {
          const store = useAppStore.getState()
          store.setLearners(freshLearners)
          const childCount = freshLearners.filter(l => !l.is_parent_profile).length
          console.log(`✅ Refreshed ${freshLearners.length} learners in store (${childCount} children)`)
          
          // Re-trigger switchLearner for current learner to refresh all data
          // This triggers the mini-bootstrap that updates mining/building/smelting pages
          const currentLearnerId = store.activeLearner?.id
          if (currentLearnerId) {
            console.log(`🔄 Re-triggering switchLearner for current learner to refresh data...`)
            await store.switchLearner(currentLearnerId)
            console.log('✅ Learner data refreshed - mining/building/smelting pages will update')
          } else {
            console.log('ℹ️ No active learner to refresh')
          }
        } else {
          console.warn('⚠️ No learners received from API, but backfill reported success')
        }
        
        // Refresh children to show updated data
        console.log('🔄 Refreshing children...')
        await refreshChildren()
        console.log('✅ Children refreshed')
      } else {
        setSuccessMessage('所有孩子都已同步到學習者檔案！')
        setTimeout(() => setSuccessMessage(''), 3000)
        console.log('ℹ️ No new profiles created (all children already have learner profiles)')
      }
    } catch (error: any) {
      console.error('❌ Failed to backfill learners:', error)
      console.error('   Error details:', error.response?.data || error.message)
      setErrorMessage(error.response?.data?.detail || error.message || '同步失敗，請重試')
    } finally {
      setBackfilling(false)
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

      {/* Status Info - Show sync status */}
      {children.length > 0 && (
        <div className="mb-6 bg-blue-50 border border-blue-200 text-blue-800 px-6 py-4 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="font-semibold mb-1">同步狀態</p>
              <p className="text-sm">
                您有 <strong>{children.length} 個孩子</strong>在系統中，
                其中 <strong>{childLearners.length} 個</strong>已同步到學習者檔案。
                {childLearners.length < children.length && (
                  <span className="block mt-1">
                    點擊「同步學習者檔案」按鈕來為現有孩子建立學習者檔案。
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {!showCreateChild && (
        <div className="mb-6 flex gap-3 flex-wrap">
          <button
            onClick={() => setShowCreateChild(true)}
            className="px-6 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors font-medium flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            {t('children.addChild')}
          </button>
          <button
            onClick={handleBackfillLearners}
            disabled={backfilling}
            className="px-6 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {backfilling ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>同步中...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>同步學習者檔案</span>
              </>
            )}
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

