'use client'

import { ParentSidebar } from '@/components/layout/ParentSidebar'

/**
 * Parent Layout
 * 
 * This layout wraps all /parent/* routes.
 * It renders the ParentSidebar for desktop navigation.
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
  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Desktop Sidebar - hidden on mobile */}
      <ParentSidebar />
      
      {/* Main Content Area */}
      <main className="flex-1 lg:ml-60 pt-20">
        <div className="p-6 lg:p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

