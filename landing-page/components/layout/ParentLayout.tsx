'use client'

import { ReactNode } from 'react'
import { ErrorBoundary } from './ErrorBoundary'
import { ParentSidebar } from './ParentSidebar'
import { Breadcrumbs } from './Breadcrumbs'
import { useIsMobile } from '@/hooks/useMediaQuery'
import { useSidebar } from '@/contexts/SidebarContext'

interface ParentLayoutProps {
  children: ReactNode
}

export function ParentLayout({ children }: ParentLayoutProps) {
  const isMobile = useIsMobile()
  const { isOpen: sidebarOpen, close: closeSidebar } = useSidebar()

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        {/* Sidebar - Desktop: fixed, Mobile: overlay */}
        {isMobile ? (
          <>
            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
              <div
                className="fixed inset-0 z-30 bg-black/50"
                onClick={closeSidebar}
                aria-hidden="true"
              />
            )}
            <div
              className={`fixed left-0 top-16 bottom-0 z-40 bg-slate-900 border-r border-white/5 transition-transform duration-300 w-60 ${
                sidebarOpen ? 'translate-x-0' : '-translate-x-full'
              }`}
            >
              <ParentSidebar onClose={closeSidebar} />
            </div>
          </>
        ) : (
          <ParentSidebar onClose={undefined} />
        )}

        {/* Main content area */}
        <main
          className={`transition-all duration-300 ${
            isMobile ? 'pt-16' : 'pt-20 pl-60'
          }`}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Breadcrumbs */}
            <Breadcrumbs />

            {/* Page content */}
            {children}
          </div>
        </main>
      </div>
    </ErrorBoundary>
  )
}

export default ParentLayout

