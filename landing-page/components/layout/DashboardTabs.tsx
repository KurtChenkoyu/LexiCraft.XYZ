'use client'

import { usePathname } from 'next/navigation'
import { Link } from '@/i18n/routing'

/**
 * Dashboard Tabs Component
 * 
 * Renders tab navigation for the Parent Dashboard.
 * Uses nested routes (not state-based tabs) per Architecture Bible.
 * 
 * Tabs:
 * - Overview: High-level summary
 * - Analytics: Learning metrics (deep dive)
 * - Finance: Wallet & transactions
 * 
 * @see .cursorrules - App Architecture Bible, Section 4 "Tabbed Page Pattern"
 */

interface Tab {
  name: string
  href: string
  label: string
}

const tabs: Tab[] = [
  { name: 'overview', href: '/parent/dashboard/overview', label: '總覽' },
  { name: 'analytics', href: '/parent/dashboard/analytics', label: '學習分析' },
  { name: 'finance', href: '/parent/dashboard/finance', label: '財務管理' },
]

export function DashboardTabs() {
  const pathname = usePathname()
  
  // Determine active tab from pathname
  const getActiveTab = () => {
    if (pathname.includes('/analytics')) return 'analytics'
    if (pathname.includes('/finance')) return 'finance'
    return 'overview' // default
  }
  
  const activeTab = getActiveTab()

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8" aria-label="Dashboard Tabs">
        {tabs.map((tab) => {
          const isActive = tab.name === activeTab
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${isActive
                  ? 'border-cyan-500 text-cyan-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              {tab.label}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

