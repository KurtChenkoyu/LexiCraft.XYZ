'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'

interface Child {
  id: string
  name: string | null
  age: number | null
}

interface ChildrenOverviewProps {
  children: Child[]
  selectedChildId: string | null
  onSelectChild: (childId: string) => void
  isLoading: boolean
}

export function ChildrenOverview({
  children,
  selectedChildId,
  onSelectChild,
  isLoading,
}: ChildrenOverviewProps) {
  const t = useTranslations('dashboard')

  if (isLoading || children.length === 0) return null

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <svg className="w-7 h-7 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          {t('childrenOverview.title')}
        </h2>
        <Link
          href="/settings"
          className="px-4 py-2 text-cyan-600 hover:bg-cyan-50 rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          {t('childrenOverview.manageAll')}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {children.map((child) => (
          <ChildCard
            key={child.id}
            child={child}
            isSelected={selectedChildId === child.id}
            onSelect={() => onSelectChild(child.id)}
          />
        ))}
        
        {/* Add Child Card */}
        <Link
          href="/settings"
          className="p-4 rounded-lg border-2 border-dashed border-gray-300 hover:border-cyan-400 bg-gray-50 hover:bg-cyan-50 transition-all flex flex-col items-center justify-center min-h-[120px]"
        >
          <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center mb-2">
            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <span className="text-gray-600 font-medium text-sm">新增孩子</span>
        </Link>
      </div>
    </div>
  )
}

function ChildCard({
  child,
  isSelected,
  onSelect,
}: {
  child: Child
  isSelected: boolean
  onSelect: () => void
}) {
  const t = useTranslations('dashboard')

  return (
    <div
      className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
        isSelected
          ? 'border-cyan-500 bg-cyan-50'
          : 'border-gray-200 hover:border-cyan-300 bg-white'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md">
          {(child.name || '?')[0].toUpperCase()}
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 text-lg">
            {child.name || t('childrenOverview.unnamed')}
          </h3>
          <p className="text-gray-500 text-sm">
            {child.age ? `${child.age} ${t('childrenOverview.yearsOld')}` : ''}
          </p>
        </div>
      </div>
      <div className="flex justify-between items-center">
        <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">學習者</span>
        <Link
          href="/survey"
          className="text-cyan-600 hover:text-cyan-700 text-sm font-medium"
          onClick={(e) => e.stopPropagation()}
        >
          {t('childrenOverview.startSurvey')} →
        </Link>
      </div>
    </div>
  )
}

