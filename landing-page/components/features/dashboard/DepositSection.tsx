'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { DepositForm } from '@/components/features/deposit/DepositForm'

interface Child {
  id: string
  name: string | null
  age: number | null
}

interface DepositSectionProps {
  children: Child[]
  selectedChildId: string | null
  onSelectChild: (childId: string) => void
  userId: string
  isLoading: boolean
}

export function DepositSection({
  children,
  selectedChildId,
  onSelectChild,
  userId,
  isLoading,
}: DepositSectionProps) {
  const t = useTranslations('dashboard')

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{t('deposit.title')}</h2>
      <p className="text-gray-600 mb-6">{t('deposit.description')}</p>
      
      {isLoading ? (
        <LoadingState message={t('loading')} />
      ) : children.length === 0 ? (
        <NoChildrenState />
      ) : (
        <>
          <ChildSelector
            children={children}
            selectedChildId={selectedChildId}
            onSelectChild={onSelectChild}
          />
          
          <DepositForm 
            learnerId={selectedChildId || ''}
            userId={userId}
            onSuccess={() => console.log('Deposit initiated')}
          />
        </>
      )}
    </div>
  )
}

function LoadingState({ message }: { message: string }) {
  return (
    <div className="text-center py-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600 mx-auto mb-4"></div>
      <p className="text-gray-600">{message}</p>
    </div>
  )
}

function NoChildrenState() {
  const t = useTranslations('dashboard')

  return (
    <div className="text-center py-8">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      </div>
      <p className="text-gray-600 mb-2">{t('noChildren.message')}</p>
      <p className="text-sm text-gray-500 mb-6">{t('noChildren.hint')}</p>
      <Link
        href="/settings"
        className="inline-block px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg font-semibold transition-colors"
      >
        前往設定新增孩子
      </Link>
    </div>
  )
}

function ChildSelector({
  children,
  selectedChildId,
  onSelectChild,
}: {
  children: Child[]
  selectedChildId: string | null
  onSelectChild: (childId: string) => void
}) {
  const t = useTranslations('dashboard')

  if (children.length > 1) {
    return (
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">{t('selectChild')}</label>
        <select
          value={selectedChildId || ''}
          onChange={(e) => onSelectChild(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white text-gray-900"
        >
          {children.map((child) => (
            <option key={child.id} value={child.id}>
              {child.name || '未命名'} {child.age ? `(${child.age}歲)` : ''}
            </option>
          ))}
        </select>
      </div>
    )
  }

  // Single child info display
  if (children.length === 1) {
    const child = children[0]
    return (
      <div className="mb-6 p-4 bg-cyan-50 rounded-lg border border-cyan-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full flex items-center justify-center text-white font-bold">
            {(child.name || '?')[0].toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-gray-900">{child.name || '未命名'}</p>
            <p className="text-sm text-gray-600">{child.age ? `${child.age} 歲` : ''}</p>
          </div>
        </div>
      </div>
    )
  }

  return null
}

