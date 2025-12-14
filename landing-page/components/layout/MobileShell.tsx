'use client'

import { ReactNode } from 'react'
import { BottomNav } from './BottomNav'
import { useIsMobile } from '@/hooks/useMediaQuery'

interface MobileShellProps {
  children: ReactNode
}

/**
 * MobileShell - Wrapper for authenticated app pages
 * 
 * - Shows BottomNav on mobile (< lg breakpoint)
 * - Adds bottom padding to account for nav height
 * - Handles safe-area insets for notched phones
 */
export function MobileShell({ children }: MobileShellProps) {
  const isMobile = useIsMobile()

  return (
    <>
      {/* Main content with top navbar padding and bottom nav padding on mobile */}
      <div className={`pt-top-nav ${isMobile ? 'pb-bottom-nav' : ''}`}>
        {children}
      </div>
      
      {/* Bottom navigation (only renders on mobile) */}
      <BottomNav />
    </>
  )
}

export default MobileShell

