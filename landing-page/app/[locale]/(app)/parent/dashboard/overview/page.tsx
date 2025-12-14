'use client'

import { useUserData } from '@/contexts/UserDataContext'
import { Link } from '@/i18n/routing'
import { EmailConfirmationBanner } from '@/components/features/auth/EmailConfirmationBanner'
import { KidModeButton } from '@/components/features/kidmode/KidModeButton'

/**
 * Dashboard Overview Tab
 * 
 * High-level summary combining key info from Analytics and Finance.
 * This is the default landing tab for parents.
 * 
 * URL: /parent/dashboard/overview
 */
export default function OverviewPage() {
  const { 
    children, 
    selectedChildId, 
    selectChild, 
    balance, 
    isLoading,
    isSyncing,
  } = useUserData()

  const selectedChild = children.find(c => c.id === selectedChildId)

  return (
    <>
      <EmailConfirmationBanner />
      
      {/* Kid Mode - Quick Launch */}
      {children.length > 0 && (
        <div className="mb-6">
          <KidModeButton />
        </div>
      )}

      {/* Sync Status */}
      {isSyncing && (
        <div className="mb-4 inline-flex items-center gap-2 px-4 py-2 bg-cyan-50 text-cyan-700 rounded-full text-sm">
          <div className="w-3 h-3 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span>同步中...</span>
        </div>
      )}

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Children Count */}
        <div className="bg-white rounded-xl shadow-lg p-5">
          <div className="flex items-start justify-between">
            <span className="text-3xl">👨‍👩‍👧</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{children.length}</div>
            <div className="text-gray-600 text-sm">孩子帳戶</div>
          </div>
        </div>

        {/* Balance */}
        <div className="bg-white rounded-xl shadow-lg p-5">
          <div className="flex items-start justify-between">
            <span className="text-3xl">💰</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{balance.available_points.toLocaleString()}</div>
            <div className="text-gray-600 text-sm">可用點數</div>
          </div>
        </div>

        {/* Locked Points */}
        <div className="bg-white rounded-xl shadow-lg p-5">
          <div className="flex items-start justify-between">
            <span className="text-3xl">🔒</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{balance.locked_points.toLocaleString()}</div>
            <div className="text-gray-600 text-sm">鎖定點數</div>
          </div>
        </div>

        {/* Selected Child */}
        <div className="bg-white rounded-xl shadow-lg p-5">
          <div className="flex items-start justify-between">
            <span className="text-3xl">🎯</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900 truncate">
              {selectedChild?.name || '未選擇'}
            </div>
            <div className="text-gray-600 text-sm">當前關注</div>
          </div>
        </div>
      </div>

      {/* Children Selection */}
      {children.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">選擇孩子</h2>
          <div className="flex flex-wrap gap-3">
            {children.map((child) => (
              <button
                key={child.id}
                onClick={() => selectChild(child.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedChildId === child.id
                    ? 'bg-cyan-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {child.name || '未命名'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/parent/dashboard/analytics"
          className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow group"
        >
          <div className="text-3xl mb-3">📊</div>
          <h3 className="font-bold text-gray-900 group-hover:text-cyan-600 transition-colors">
            學習分析
          </h3>
          <p className="text-gray-600 text-sm mt-1">查看詳細學習數據和進度</p>
        </Link>

        <Link
          href="/parent/dashboard/finance"
          className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow group"
        >
          <div className="text-3xl mb-3">💳</div>
          <h3 className="font-bold text-gray-900 group-hover:text-cyan-600 transition-colors">
            財務管理
          </h3>
          <p className="text-gray-600 text-sm mt-1">儲值和管理點數餘額</p>
        </Link>

        <Link
          href="/parent/children"
          className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow group"
        >
          <div className="text-3xl mb-3">👨‍👩‍👧‍👦</div>
          <h3 className="font-bold text-gray-900 group-hover:text-cyan-600 transition-colors">
            孩子管理
          </h3>
          <p className="text-gray-600 text-sm mt-1">新增或管理孩子帳戶</p>
        </Link>
      </div>

      {/* Empty State */}
      {children.length === 0 && !isLoading && (
        <div className="bg-white rounded-2xl shadow-xl p-12 text-center mt-8">
          <div className="text-6xl mb-4">👨‍👩‍👧</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">開始您的旅程</h2>
          <p className="text-gray-600 mb-6">新增您的第一個孩子帳戶開始學習</p>
          <Link
            href="/parent/children"
            className="inline-block px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-semibold transition-colors"
          >
            新增孩子 →
          </Link>
        </div>
      )}
    </>
  )
}

