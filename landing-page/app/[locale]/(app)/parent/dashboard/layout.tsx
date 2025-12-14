import { DashboardTabs } from '@/components/layout/DashboardTabs'

/**
 * Parent Dashboard Layout
 * 
 * This layout wraps all /parent/dashboard/* routes.
 * It renders the DashboardTabs component for tab navigation.
 * 
 * URL: /parent/dashboard/*
 * 
 * Sub-routes:
 * - /parent/dashboard/overview - Summary view
 * - /parent/dashboard/analytics - Learning metrics
 * - /parent/dashboard/finance - Wallet & transactions
 * 
 * @see .cursorrules - App Architecture Bible, Section 4 "Tabbed Page Pattern"
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">控制台</h1>
        <p className="text-gray-600 mt-1">管理您的孩子學習和財務</p>
      </div>
      
      {/* Tab Navigation */}
      <DashboardTabs />
      
      {/* Tab Content */}
      <div>
        {children}
      </div>
    </div>
  )
}

