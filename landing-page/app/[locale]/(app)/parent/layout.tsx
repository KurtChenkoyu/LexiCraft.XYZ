'use client'

import { ParentSidebar } from '@/components/layout/ParentSidebar'
import { useSidebar } from '@/contexts/SidebarContext'
import { useIsMobile } from '@/hooks/useMediaQuery'

/**
 * Parent Layout
 * 
 * This layout wraps all /parent/* routes.
 * It renders the ParentSidebar for desktop navigation.
 * On mobile, the sidebar is an overlay that can be toggled.
 * 
 * URL: /parent/*
 * 
 * @see .cursorrules - App Architecture Bible, Section 2
 */
export default function ParentLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const isMobile = useIsMobile()
  const { isOpen: sidebarOpen, close: closeSidebar } = useSidebar()

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Mobile: Overlay backdrop */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar - Desktop: fixed, Mobile: overlay */}
      {isMobile ? (
        <div
          className={`fixed left-0 top-16 bottom-0 z-40 w-60 transition-transform duration-300 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <ParentSidebar onClose={closeSidebar} />
        </div>
      ) : (
        <ParentSidebar />
      )}

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isMobile ? 'pt-16' : 'pt-20 lg:ml-60'
        }`}
        style={{ maxHeight: 'calc(100vh - 4rem)' }}
      >
        <div className="p-6 lg:p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

